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
    assert client.api_keys == ["test_key"]
    assert client.base_url == "https://openrouter.ai/api/v1/chat/completions"


def test_openrouter_client_init_multiple_keys(monkeypatch):
    """
    Test that OpenRouterClient initializes correctly with multiple API keys and
    rotates them correctly.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "key1, key2,key3 ")
    client = OpenRouterClient()
    assert client.api_keys == ["key1", "key2", "key3"]
    assert client._get_next_api_key() == "key1"
    assert client._get_next_api_key() == "key2"
    assert client._get_next_api_key() == "key3"
    assert client._get_next_api_key() == "key1"


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

    mock_response.status_code = 200

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


@pytest.mark.asyncio
async def test_openrouter_client_generate_retries(monkeypatch):
    """
    Test that OpenRouterClient retries on 429 and 500 status codes, using round-robin keys.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "key1,key2,key3")
    client = OpenRouterClient()
    request = ChatCompletionRequest(
        model="openrouter-test-model",
        messages=[ChatMessage(role="user", content="Hello")],
    )

    from unittest.mock import MagicMock

    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429

    mock_response_500 = MagicMock()
    mock_response_500.status_code = 500

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.raise_for_status.return_value = None
    mock_response_200.json.return_value = {
        "id": "test_id",
        "created": 1234567890,
        "model": "openrouter-test-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Success!"},
                "finish_reason": "stop",
            }
        ],
    }

    with (
        patch("httpx.AsyncClient.post", side_effect=[mock_response_429, mock_response_500, mock_response_200]) as mock_post,
        patch("asyncio.sleep") as mock_sleep,
    ):
        response = await client.generate(request)

        assert mock_post.call_count == 3

        # Check headers in calls to ensure round-robin
        assert mock_post.call_args_list[0][1]["headers"]["Authorization"] == "Bearer key1"
        assert mock_post.call_args_list[1][1]["headers"]["Authorization"] == "Bearer key2"
        assert mock_post.call_args_list[2][1]["headers"]["Authorization"] == "Bearer key3"

        # Check exponential backoff calls
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)

        # Ensure successful parsing at the end
        assert response.choices[0].message.content == "Success!"


@pytest.mark.asyncio
async def test_openrouter_client_max_retries_exceeded(monkeypatch):
    """
    Test that OpenRouterClient raises an error after max retries are exceeded.
    """
    monkeypatch.setenv("OPENROUTER_API_KEY", "key1")
    client = OpenRouterClient()
    request = ChatCompletionRequest(
        model="openrouter-test-model",
        messages=[ChatMessage(role="user", content="Hello")],
    )

    from unittest.mock import MagicMock

    import httpx

    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="Too Many Requests", request=MagicMock(), response=mock_response_429
    )

    with (
        patch("httpx.AsyncClient.post", return_value=mock_response_429) as mock_post,
        patch("asyncio.sleep") as mock_sleep,
    ):
        with pytest.raises(httpx.HTTPStatusError):
            await client.generate(request)

        # 1 initial + 3 retries
        assert mock_post.call_count == 4
        assert mock_sleep.call_count == 3
