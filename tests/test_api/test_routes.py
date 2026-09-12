from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
def mock_openrouter_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")


@pytest.mark.asyncio
async def test_chat_completions_e2e(async_client: AsyncClient, mock_openrouter_api_key):
    payload = {
        "messages": [{"role": "user", "content": "Hi"}],
        "model": "openrouter-model",
    }

    mock_response_data = {
        "id": "test_id",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "openrouter-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello from OpenRouter!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = mock_response_data

    original_post = AsyncClient.post

    async def mock_post(self, url, *args, **kwargs):
        if "openrouter.ai" in str(url):
            return mock_response
        return await original_post(self, url, *args, **kwargs)

    with patch("httpx.AsyncClient.post", new=mock_post):
        response = await async_client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["content"] == "Hello from OpenRouter!"


@pytest.mark.asyncio
async def test_chat_completions_invalid_payload(async_client: AsyncClient):
    payload = {
        # missing messages
        "model": "some-model"
    }
    response = await async_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 422
