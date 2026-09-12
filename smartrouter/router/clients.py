import asyncio
import itertools
import os
from collections.abc import AsyncGenerator

import httpx

from smartrouter.api.models import ChatCompletionRequest, ChatCompletionResponse
from smartrouter.core.config import TierConfig
from smartrouter.router.base_provider import BaseProvider


class OpenRouterClient(BaseProvider):
    """
    Client for OpenRouter API.
    """

    def __init__(self) -> None:
        api_key_env = os.getenv("OPENROUTER_API_KEY")
        if not api_key_env:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

        self.api_keys = [key.strip() for key in api_key_env.split(",") if key.strip()]
        if not self.api_keys:
            raise ValueError("OPENROUTER_API_KEY contains no valid keys")

        self._key_iterator = itertools.cycle(self.api_keys)
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def _get_next_api_key(self) -> str:
        """Get the next API key in round-robin fashion."""
        return next(self._key_iterator)

    async def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Forward the request to OpenRouter with retries and round-robin load balancing.
        """
        payload = request.model_dump(exclude_none=True)
        max_retries = 3
        base_delay = 1.0

        async with httpx.AsyncClient() as client:
            for attempt in range(max_retries + 1):
                api_key = self._get_next_api_key()
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                try:
                    response = await client.post(
                        self.base_url, json=payload, headers=headers, timeout=30.0
                    )

                    if response.status_code == 429 or 500 <= response.status_code < 600:
                        if attempt < max_retries:
                            await asyncio.sleep(base_delay * (2**attempt))
                            continue
                        response.raise_for_status()

                    response.raise_for_status()
                    data = response.json()
                    return ChatCompletionResponse(**data)

                except httpx.RequestError:
                    if attempt < max_retries:
                        await asyncio.sleep(base_delay * (2**attempt))
                        continue
                    raise
            raise RuntimeError("Unreachable")


class RouterClient(BaseProvider):
    """
    Dynamic client for routing to different providers based on TierConfig.
    """

    def __init__(self, config: TierConfig) -> None:
        self.config = config

    async def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Forward the request to the configured provider.
        """
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        if "anthropic" in self.config.base_url.lower():
            headers["anthropic-version"] = "2023-06-01"

        # The router dictates the actual model being used for the backend provider
        request.model = self.config.model

        payload = request.model_dump(exclude_none=True)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config.base_url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()
            return ChatCompletionResponse(**data)

    async def stream_generate(
        self, request: ChatCompletionRequest
    ) -> AsyncGenerator[str]:
        """
        Forward the request to the configured provider as a stream.
        """
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        if "anthropic" in self.config.base_url.lower():
            headers["anthropic-version"] = "2023-06-01"

        # The router dictates the actual model being used for the backend provider
        request.model = self.config.model

        payload = request.model_dump(exclude_none=True)

        async with (
            httpx.AsyncClient() as client,
            client.stream(
                "POST",
                self.config.base_url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout_seconds,
            ) as response,
        ):
            response.raise_for_status()
            async for chunk in response.aiter_text():
                yield chunk
