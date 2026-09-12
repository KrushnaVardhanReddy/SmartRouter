from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from smartrouter.api.models import (
    ChatCompletionChoice,
    ChatCompletionResponse,
    ChatMessage,
)


@pytest.fixture
def dummy_response():
    return ChatCompletionResponse(
        id="chatcmpl-123",
        created=1677652288,
        model="openai/gpt-3.5-turbo",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="Hello there!"),
                finish_reason="stop",
            )
        ],
        usage={"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
    )


@pytest.mark.asyncio
async def test_chat_completions_route(async_client: AsyncClient, dummy_response):
    request_payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}],
    }

    with patch("smartrouter.main.RouterDispatcher") as MockDispatcher:
        instance = MockDispatcher.return_value
        instance.dispatch = AsyncMock(return_value=dummy_response)

        response = await async_client.post("/v1/chat/completions", json=request_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Hello there!"
        assert data["id"] == "chatcmpl-123"

        # Verify it passes shadow mode header correctly (default False)
        instance.dispatch.assert_called_once()
        assert instance.dispatch.call_args[1]["is_shadow_mode"] is False


@pytest.mark.asyncio
async def test_chat_completions_route_shadow_mode(async_client: AsyncClient, dummy_response):
    request_payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello shadow mode!"}],
    }

    with patch("smartrouter.main.RouterDispatcher") as MockDispatcher:
        instance = MockDispatcher.return_value
        instance.dispatch = AsyncMock(return_value=dummy_response)

        response = await async_client.post(
            "/v1/chat/completions",
            json=request_payload,
            headers={"X-SmartRouter-Shadow": "true"},
        )

        assert response.status_code == 200
        instance.dispatch.assert_called_once()
        assert instance.dispatch.call_args[1]["is_shadow_mode"] is True


@pytest.mark.asyncio
async def test_chat_completions_invalid_payload(async_client: AsyncClient):
    payload = {
        # missing messages
        "model": "some-model"
    }
    response = await async_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 422
