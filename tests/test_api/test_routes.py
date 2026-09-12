import pytest
from httpx import AsyncClient


@pytest.fixture
def mock_openrouter_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")


@pytest.mark.asyncio
async def test_chat_completions_route(
    async_client: AsyncClient, mock_openrouter_api_key
):
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

    from unittest.mock import AsyncMock, patch

    from smartrouter.api.models import (
        ChatCompletionResponse as ChatCompletionResponseModel,
    )

    mock_resp = ChatCompletionResponseModel.model_validate(mock_response_payload)

    with patch("smartrouter.api.routes.RouterDispatcher") as MockDispatcher:
        instance = MockDispatcher.return_value
        instance.dispatch = AsyncMock(return_value=(mock_resp, "test-model-id", 0.85))

        response = await async_client.post("/v1/chat/completions", json=request_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Hello there!"
        assert data["id"] == "chatcmpl-123"

        # Verify headers were injected
        assert response.headers["x-smartrouter-model"] == "test-model-id"
        assert response.headers["x-smartrouter-score"] == "0.850"

        # Verify it parses correctly into the response model
        parsed = ChatCompletionResponseModel(**data)
        assert parsed.object == "chat.completion"


@pytest.mark.asyncio
async def test_chat_completions_invalid_payload(async_client: AsyncClient):
    payload = {
        # missing messages
        "model": "some-model"
    }
    response = await async_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_usage_report(async_client: AsyncClient):
    response = await async_client.get("/v1/usage")
    assert response.status_code == 200

    data = response.json()
    assert data["total_requests"] == 0
    assert data["total_spent_usd"] == 0.0
    assert data["hypothetical_spent_usd"] == 0.0
    assert data["total_saved_usd"] == 0.0
    assert data["shadow_mode_active"] is False

    from smartrouter.api.models import UsageReportResponse

    parsed = UsageReportResponse.model_validate(data)
    assert parsed.total_requests == 0
