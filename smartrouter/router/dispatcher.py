import logging
from collections.abc import AsyncGenerator

import httpx

from smartrouter.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    RoutingPreference,
)
from smartrouter.classifier.engine import ClassifierEngine
from smartrouter.core.config import get_settings
from smartrouter.core.usage import usage_tracker
from smartrouter.router.clients import RouterClient
from smartrouter.router.context_guard import (
    compress_context,
    get_token_count,
)

logger = logging.getLogger(__name__)


class RouterDispatcher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.classifier = ClassifierEngine()

    async def dispatch(
        self, request: ChatCompletionRequest, shadow_mode: bool = False
    ) -> tuple[ChatCompletionResponse | AsyncGenerator[str], str, float]:
        router_config = self.settings.router
        score = 0.0

        if request.routing_preference == RoutingPreference.frontier_only:
            tier_name = "smart"
            tier_config = self.settings.tiers.smart
            logger.info(
                "routing_preference=frontier_only: bypassing classifier, routing directly to smart tier."
            )
        elif request.routing_preference == RoutingPreference.economy:
            tier_name = "cheap"
            tier_config = self.settings.tiers.cheap
            logger.info(
                "routing_preference=economy: bypassing classifier, routing directly to cheap tier."
            )
        else:
            # 1. Score the prompt (using the last user message)
            prompt_text = ""
            for message in reversed(request.messages):
                if message.role == "user":
                    prompt_text = message.content
                    break

            score = self.classifier.score_prompt(prompt_text)

            # 2. Check Budget Circuit Breaker
            budget_limit = router_config.budget_limit_usd
            is_budget_exceeded = (
                budget_limit > 0 and usage_tracker.total_spent_usd >= budget_limit
            )

            # 3. Pick a Tier
            if is_budget_exceeded:
                logger.warning(
                    f"Budget limit of ${budget_limit:.2f} exceeded (spent: ${usage_tracker.total_spent_usd:.2f}). "
                    "Forcing cheap tier."
                )
                tier_name = "cheap"
                tier_config = self.settings.tiers.cheap
            elif score < router_config.low_threshold:
                tier_name = "cheap"
                tier_config = self.settings.tiers.cheap
            elif score < router_config.high_threshold:
                tier_name = "mid"
                tier_config = self.settings.tiers.mid
            else:
                tier_name = "smart"
                tier_config = self.settings.tiers.smart

            if not is_budget_exceeded:
                logger.info(f"Initial routing score: {score:.3f} -> {tier_name} tier")
            else:
                logger.info(
                    f"Initial routing score: {score:.3f} but budget exceeded. Forced to {tier_name} tier."
                )

            # 4. Context Guard Check and Upgrade
            # Resolve summarizer API key (handles both plain str and SecretStr)
            summarizer_config = self.settings.tiers.cheap
            api_key_raw = summarizer_config.api_key
            summarizer_api_key_str: str = ""
            if api_key_raw is not None:
                if hasattr(api_key_raw, "get_secret_value"):
                    summarizer_api_key_str = api_key_raw.get_secret_value()
                else:
                    summarizer_api_key_str = str(api_key_raw)

            # 4. Context-Aware Capacity Routing: cascade tiers, compress first before upgrading
            tiers_order = ["cheap", "mid", "smart"]
            tier_index = tiers_order.index(tier_name)

            while tier_index < len(tiers_order):
                current_tier_name = tiers_order[tier_index]
                current_tier_config = getattr(self.settings.tiers, current_tier_name)

                if current_tier_config.max_context_tokens is None:
                    break

                token_count = get_token_count(request.messages)
                if token_count <= current_tier_config.max_context_tokens:
                    break

                logger.info(
                    f"Context limit exceeded for '{current_tier_name}' tier. Attempting to compress context."
                )
                compressed = await compress_context(
                    request.messages,
                    current_tier_config.max_context_tokens,
                    summarizer_config.base_url,
                    summarizer_config.model,
                    summarizer_api_key_str,
                )

                if (
                    get_token_count(compressed)
                    <= current_tier_config.max_context_tokens
                ):
                    request.messages = compressed
                    break

                if is_budget_exceeded:
                    logger.warning(
                        f"Context limit exceeded for '{current_tier_name}' tier and budget exceeded. "
                        f"Remaining on '{current_tier_name}' tier."
                    )
                    break

                if current_tier_name == "smart":
                    logger.warning(
                        "Context limit exceeded for 'smart' tier. Cannot upgrade further."
                    )
                    break

                next_tier_name = tiers_order[tier_index + 1]
                logger.info(
                    f"Even after compression, context limit exceeded for '{current_tier_name}' tier. "
                    f"Upgrading to '{next_tier_name}'."
                )
                tier_index += 1

            tier_name = tiers_order[tier_index]
            tier_config = getattr(self.settings.tiers, tier_name)

            # 5. JSON Mode Enforcement
            if (
                request.response_format
                and request.response_format.type == "json_object"
                and tier_name == "cheap"
                and not is_budget_exceeded
            ):
                logger.info(
                    "JSON mode requested. Upgrading from 'cheap' to 'mid' tier."
                )
                tier_name = "mid"
                tier_config = self.settings.tiers.mid
            elif (
                request.response_format
                and request.response_format.type == "json_object"
                and tier_name == "cheap"
                and is_budget_exceeded
            ):
                logger.warning(
                    "JSON mode requested, but budget is exceeded. Remaining on 'cheap' tier and hoping for the best."
                )

            logger.info(
                f"Final selected tier: {tier_name} using model {tier_config.model}"
            )

            # Shadow mode
            is_shadow = shadow_mode or router_config.shadow_mode
            if is_shadow:
                logger.info(
                    f"Shadow mode is enabled. Score {score:.3f} would have routed to {tier_name} tier. Forcing route to smart tier."
                )
                tier_name = "smart"
                tier_config = self.settings.tiers.smart

        # 6. Dispatch using RouterClient with Fallback Chain
        fallback_chains = {
            "smart": ["smart", "mid", "cheap"],
            "mid": ["mid", "cheap"],
            "cheap": ["cheap"],
        }

        tiers_to_try = fallback_chains.get(tier_name, [tier_name])
        last_exception: Exception | None = None

        for current_tier in tiers_to_try:
            current_config = getattr(self.settings.tiers, current_tier)
            client = RouterClient(config=current_config)

            try:
                logger.info(f"Attempting dispatch with tier: {current_tier}")
                if request.stream:
                    response_gen = client.stream_generate(request)
                    return response_gen, current_config.model, score
                else:
                    response = await client.generate(request)

                    # Estimate cost based on tier
                    cost_map = {"cheap": 0.001, "mid": 0.005, "smart": 0.02}
                    actual_cost = cost_map.get(current_tier, 0.0)
                    hypothetical_cost = cost_map["smart"]
                    usage_tracker.record_usage(actual_cost, hypothetical_cost)

                    return response, current_config.model, score
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if 500 <= status_code < 600:
                    logger.warning(
                        f"Tier '{current_tier}' failed with 5xx error ({status_code}). "
                        f"Falling back to next tier if available."
                    )
                    last_exception = e
                    continue
                else:
                    # Don't fallback on 4xx errors
                    raise
            except httpx.RequestError as e:
                logger.warning(
                    f"Tier '{current_tier}' failed with network error: {e}. "
                    f"Falling back to next tier if available."
                )
                last_exception = e
                continue

        if last_exception:
            logger.error("All tiers in fallback chain failed.")
            raise last_exception

        raise RuntimeError("Unreachable")
