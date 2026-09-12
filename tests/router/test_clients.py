from unittest.mock import patch

import pytest

from smartrouter.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)
from smartrouter.router.clients import OpenRouterClient


@pytest.fixture
def mock_openrouter_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")


def test_openrouter_client_init_no_api_key(monkeypatch):
    """
    Test that OpenRouterClient raises an error if the API key is not set.
    """
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(
        ValueError, match="OPENROUTER_API_KEY environment variable is not set"
    ):
        OpenRouterClient()


def test_openrouter_client_init_with_api_key(mock_openrouter_api_key):
    """
    Test that OpenRouterClient initializes correctly when the API key is set.
    """
    client = OpenRouterClient()
    assert client.api_key == "test_key"
    assert client.base_url == "https://openrouter.ai/api/v1/chat/completions"


@pytest.mark.asyncio
async def test_openrouter_client_generate(mock_openrouter_api_key):
    """
    Test that OpenRouterClient forwards the request and returns a valid response.
    """
    client = OpenRouterClient()
    request = ChatCompletionRequest(
        model="openrouter-test-model",
        messages=[ChatMessage(role="user", content="Hello")],
        temperature=0.5,
        max_tokens=100,
        stream=False,
    )

    mock_response_data = {
        "id": "test_id",
        "created": 1234567890,
        "model": "openrouter-test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hi there!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    # Use MagicMock for the response object itself because json() and raise_for_status()
    # are regular synchronous methods on httpx.Response, not async methods.
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = mock_response_data

    # Mock httpx.AsyncClient.post
    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        response = await client.generate(request)

        # Ensure correct arguments were passed to httpx.post
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == "Bearer test_key"
        assert kwargs["json"] == request.model_dump(exclude_none=True)

        # Ensure the response is properly parsed
        assert isinstance(response, ChatCompletionResponse)
        assert response.id == "test_id"
        assert response.model == "openrouter-test-model"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Hi there!"
        assert response.usage.total_tokens == 15
