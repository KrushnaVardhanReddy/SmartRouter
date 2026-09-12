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
    from smartrouter.core.usage import usage_tracker

    usage_tracker.clear()
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


@pytest.fixture
def mock_provider_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")


@pytest.mark.asyncio
async def test_chat_completions_e2e(
    async_client: AsyncClient, mock_provider_api_keys: None
) -> None:
    request_payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "What is the capital of France?"}],
    }

    mock_response_payload = {
        "id": "chatcmpl-e2e",
        "object": "chat.completion",
        "created": 1677652289,
        "model": "dummy-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Paris"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12},
    }

    import respx
    from httpx import Response

    with respx.mock(assert_all_called=False, base_url=None) as respx_mock:
        # Mock the URLs from smartrouter.yaml
        respx_mock.route(host="api.groq.com").mock(
            return_value=Response(200, json=mock_response_payload)
        )
        respx_mock.route(host="api.openai.com").mock(
            return_value=Response(200, json=mock_response_payload)
        )
        # Pass through huggingface requests for model downloads
        respx_mock.route(host="huggingface.co").pass_through()
        respx_mock.route(host="test").pass_through()

        response = await async_client.post("/v1/chat/completions", json=request_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Paris"

        # Verify headers were injected by the real dispatcher
        assert "x-smartrouter-model" in response.headers
        assert "x-smartrouter-score" in response.headers

        # The score should be parsable as a float
        score_str = response.headers["x-smartrouter-score"]
        score = float(score_str)
        assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_chat_completions_streaming(
    async_client: AsyncClient, mock_provider_api_keys: None
) -> None:
    request_payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Tell me a joke."}],
        "stream": True,
    }

    from unittest.mock import patch

    import respx

    async def dummy_generator():
        yield "data: chunk1\n\n"
        yield "data: chunk2\n\n"

    with patch(
        "smartrouter.router.clients.RouterClient.stream_generate"
    ) as mock_stream_generate:
        mock_stream_generate.return_value = dummy_generator()

        with respx.mock(assert_all_called=False, base_url=None) as respx_mock:
            # We don't actually need the httpx mock if we mock stream_generate directly,
            # but we pass through huggingface just in case the classifier loads.
            respx_mock.route(host="huggingface.co").pass_through()
            respx_mock.route(host="test").pass_through()

            response = await async_client.post(
                "/v1/chat/completions", json=request_payload
            )

            assert response.status_code == 200
            assert (
                response.headers["content-type"] == "text/event-stream; charset=utf-8"
            )

            # Verify headers were injected by the real dispatcher
            assert "x-smartrouter-model" in response.headers
            assert "x-smartrouter-score" in response.headers

            content = response.text
            assert "data: chunk1\n\n" in content
            assert "data: chunk2\n\n" in content
