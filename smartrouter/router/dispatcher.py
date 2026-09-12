import logging

from smartrouter.api.models import ChatCompletionRequest, ChatCompletionResponse
from smartrouter.classifier.engine import ClassifierEngine
from smartrouter.core.config import get_settings
from smartrouter.router.clients import RouterClient
from smartrouter.router.context_guard import check_context_limit

logger = logging.getLogger(__name__)


class RouterDispatcher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.classifier = ClassifierEngine()

    async def dispatch(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
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
        if tier_name == "cheap" and not check_context_limit(
            request.messages, tier_config.max_context_tokens
        ):
            logger.info("Context limit exceeded for 'cheap' tier. Upgrading to 'mid'.")
            tier_name = "mid"
            tier_config = self.settings.tiers.mid

        if tier_name == "mid" and not check_context_limit(
            request.messages, tier_config.max_context_tokens
        ):
            logger.info("Context limit exceeded for 'mid' tier. Upgrading to 'smart'.")
            tier_name = "smart"
            tier_config = self.settings.tiers.smart

        # 4. JSON Mode Enforcement
        if request.response_format and request.response_format.type == "json_object" and tier_name == "cheap":
            logger.info("JSON mode requested. Upgrading from 'cheap' to 'mid' tier.")
            tier_name = "mid"
            tier_config = self.settings.tiers.mid

        logger.info(f"Final selected tier: {tier_name} using model {tier_config.model}")

        # Shadow mode
        if router_config.shadow_mode:
            logger.info(
                "Shadow mode is enabled. Proceeding with standard routing for now."
            )

        # 4. Dispatch using RouterClient
        client = RouterClient(config=tier_config)
        return await client.generate(request)
