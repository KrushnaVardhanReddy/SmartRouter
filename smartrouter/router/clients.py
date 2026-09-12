import os

import httpx

from smartrouter.api.models import ChatCompletionRequest, ChatCompletionResponse
from smartrouter.router.base_provider import BaseProvider


class OpenRouterClient(BaseProvider):
    """
    Client for OpenRouter API.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    async def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Forward the request to OpenRouter.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Dump the Pydantic model to a dict, excluding unset/none to avoid
        # sending unnecessary fields or overriding OpenRouter defaults wrongly.
        payload = request.model_dump(exclude_none=True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url, json=payload, headers=headers, timeout=30.0
            )
            response.raise_for_status()

            # Note: We expect OpenRouter to return a response that can be parsed
            # into our ChatCompletionResponse model.
            data = response.json()
            return ChatCompletionResponse(**data)
