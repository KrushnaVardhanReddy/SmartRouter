import logging

import httpx

from smartrouter.api.models import ChatCompletionRequest, ChatCompletionResponse
from smartrouter.classifier.engine import ClassifierEngine
from smartrouter.core.config import get_settings
from smartrouter.router.clients import RouterClient
from smartrouter.router.context_guard import check_context_limit, compress_context

logger = logging.getLogger(__name__)


class RouterDispatcher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.classifier = ClassifierEngine()

    async def dispatch(
        self, request: ChatCompletionRequest, shadow_mode: bool = False
    ) -> tuple[ChatCompletionResponse, str, float]:
        # 1. Score the prompt (using the last user message)
        prompt_text = ""
        for message in reversed(request.messages):
            if message.role == "user":
                prompt_text = message.content
                break

        score = self.classifier.score_prompt(prompt_text)

        # 2. Pick a Tier
        router_config = self.settings.router
        if score < router_config.low_threshold:
            tier_name = "cheap"
            tier_config = self.settings.tiers.cheap
        elif score < router_config.high_threshold:
            tier_name = "mid"
            tier_config = self.settings.tiers.mid
        else:
            tier_name = "smart"
            tier_config = self.settings.tiers.smart

        logger.info(f"Initial routing score: {score:.3f} -> {tier_name} tier")

        # 3. Context Guard Check and Upgrade
        if tier_name == "cheap" and tier_config.max_context_tokens is not None and not check_context_limit(
            request.messages, tier_config.max_context_tokens
        ):
            logger.info("Context limit exceeded for 'cheap' tier. Attempting to compress context.")
            compressed = compress_context(request.messages, tier_config.max_context_tokens)
            if check_context_limit(compressed, tier_config.max_context_tokens):
                request.messages = compressed
            else:
                logger.info("Even after compression, context limit exceeded for 'cheap' tier. Upgrading to 'mid'.")
                tier_name = "mid"
                tier_config = self.settings.tiers.mid

        if tier_name == "mid" and tier_config.max_context_tokens is not None and not check_context_limit(
            request.messages, tier_config.max_context_tokens
        ):
            logger.info("Context limit exceeded for 'mid' tier. Attempting to compress context.")
            compressed = compress_context(request.messages, tier_config.max_context_tokens)
            if check_context_limit(compressed, tier_config.max_context_tokens):
                request.messages = compressed
            else:
                logger.info("Even after compression, context limit exceeded for 'mid' tier. Upgrading to 'smart'.")
                tier_name = "smart"
                tier_config = self.settings.tiers.smart

        # 4. JSON Mode Enforcement
        if (
            request.response_format
            and request.response_format.type == "json_object"
            and tier_name == "cheap"
        ):
            logger.info("JSON mode requested. Upgrading from 'cheap' to 'mid' tier.")
            tier_name = "mid"
            tier_config = self.settings.tiers.mid

        logger.info(f"Final selected tier: {tier_name} using model {tier_config.model}")

        # Shadow mode
        is_shadow = shadow_mode or router_config.shadow_mode
        if is_shadow:
            logger.info(
                f"Shadow mode is enabled. Score {score:.3f} would have routed to {tier_name} tier. Forcing route to smart tier."
            )
            tier_name = "smart"
            tier_config = self.settings.tiers.smart

        # 4. Dispatch using RouterClient with Fallback Chain
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
                response = await client.generate(request)
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
