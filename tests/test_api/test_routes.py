import httpx
import pytest
import respx
from httpx import AsyncClient

from smartrouter.api.models import ChatCompletionResponse


@pytest.fixture
def mock_openrouter_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")


@pytest.mark.asyncio
async def test_chat_completions_route(async_client: AsyncClient, mock_openrouter_api_key):
    request_payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}],
    }

    mock_response_payload = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "openai/gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello there!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
    }

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=mock_response_payload)
        )

        response = await async_client.post("/v1/chat/completions", json=request_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Hello there!"
        assert data["id"] == "chatcmpl-123"

        # Verify it parses correctly into the response model
        parsed = ChatCompletionResponse(**data)
        assert parsed.object == "chat.completion"


@pytest.mark.asyncio
async def test_chat_completions_invalid_payload(async_client: AsyncClient):
    payload = {
        # missing messages
        "model": "some-model"
    }
    response = await async_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 422
