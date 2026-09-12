from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from smartrouter.api.models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ResponseFormat,
)
from smartrouter.router.dispatcher import RouterDispatcher


@pytest.fixture
def mock_settings():
    with patch("smartrouter.router.dispatcher.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.router.low_threshold = 0.4
        settings.router.high_threshold = 0.8
        settings.router.shadow_mode = False
        settings.router.budget_limit_usd = 0.0

        settings.tiers.cheap.model = "cheap-model"
        settings.tiers.cheap.base_url = "http://cheap.com"
        settings.tiers.cheap.max_context_tokens = 1000

        settings.tiers.mid.model = "mid-model"
        settings.tiers.mid.base_url = "http://mid.com"
        settings.tiers.mid.max_context_tokens = 4000

        settings.tiers.smart.model = "smart-model"
        settings.tiers.smart.base_url = "http://smart.com"
        settings.tiers.smart.max_context_tokens = 8000

        mock_get_settings.return_value = settings
        yield mock_get_settings


@pytest.fixture
def mock_classifier():
    with patch("smartrouter.router.dispatcher.ClassifierEngine") as MockClassifier:
        instance = MockClassifier.return_value
        instance.score_prompt.return_value = 0.2  # default to cheap
        yield instance


@pytest.fixture
def dummy_request():
    return ChatCompletionRequest(
        messages=[
            ChatMessage(role="user", content="Hello, world!"),
        ]
    )


@pytest.fixture
def dummy_response():
    return ChatCompletionResponse(
        id="test-id",
        created=1234567890,
        model="test-model",
        choices=[
            ChatCompletionChoice(
                index=0, message=ChatMessage(role="assistant", content="Test response")
            )
        ],
    )


@pytest.mark.asyncio
async def test_dispatch_picks_cheap_tier(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.3  # < 0.4

    with patch("smartrouter.router.dispatcher.RouterClient") as MockClient:
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        response, model_id, score = await dispatcher.dispatch(dummy_request)

        assert response == dummy_response
        assert model_id == "cheap-model"
        assert score == 0.3
        MockClient.assert_called_once()
        assert MockClient.call_args[1]["config"].model == "cheap-model"


@pytest.mark.asyncio
async def test_dispatch_picks_mid_tier(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.6  # >= 0.4 and < 0.8

    with patch("smartrouter.router.dispatcher.RouterClient") as MockClient:
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        _, model_id, _ = await dispatcher.dispatch(dummy_request)

        assert model_id == "mid-model"
        assert MockClient.call_args[1]["config"].model == "mid-model"


@pytest.mark.asyncio
async def test_dispatch_picks_smart_tier(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.9  # >= 0.8

    with patch("smartrouter.router.dispatcher.RouterClient") as MockClient:
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        _, model_id, _ = await dispatcher.dispatch(dummy_request)

        assert model_id == "smart-model"
        assert MockClient.call_args[1]["config"].model == "smart-model"


@pytest.mark.asyncio
async def test_dispatch_upgrades_tier_due_to_context_limit(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.3  # Initially picks cheap

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.get_token_count", return_value=99999),
    ):  # Force context limit exceed for all tiers
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        _, model_id, _ = await dispatcher.dispatch(dummy_request)

        # Upgrades to 'mid' and then 'mid' also exceeds, so upgrades to 'smart'
        assert model_id == "smart-model"
        assert MockClient.call_args[1]["config"].model == "smart-model"


@pytest.mark.asyncio
async def test_dispatch_compresses_before_upgrading_tier(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.3  # Initially picks cheap

    # Mock get_token_count to exceed cheap limit (1000) before compression, but fit after
    def mock_get_token_count(messages):
        if messages and messages[0].content == "compressed":
            return 800       # Fits cheap
        return 1500  # Exceeds cheap (1000)

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.get_token_count", side_effect=mock_get_token_count),
        patch("smartrouter.router.dispatcher.compress_context", return_value=[ChatMessage(role="user", content="compressed")])
    ):
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        _, model_id, _ = await dispatcher.dispatch(dummy_request)

        # Should stay on cheap tier since compression succeeded
        assert model_id == "cheap-model"
        assert MockClient.call_args[1]["config"].model == "cheap-model"


@pytest.mark.asyncio
async def test_dispatch_upgrades_after_compression_fails(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.3  # Initially picks cheap

    # Mock get_token_count to exceed cheap limit (1000) even after compression, but fit mid (4000)
    def mock_get_token_count(messages):
        if messages and messages[0].content == "compressed":
            return 1500      # Exceeds cheap, fits mid
        return 2000  # Exceeds cheap

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.get_token_count", side_effect=mock_get_token_count),
        patch("smartrouter.router.dispatcher.compress_context", return_value=[ChatMessage(role="user", content="compressed")])
    ):
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        _, model_id, _ = await dispatcher.dispatch(dummy_request)

        # Should upgrade to mid tier because compression failed to fit cheap tier
        assert model_id == "mid-model"
        assert MockClient.call_args[1]["config"].model == "mid-model"


@pytest.mark.asyncio
async def test_dispatch_upgrades_tier_due_to_json_mode(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.2  # Initially picks cheap
    dummy_request.response_format = ResponseFormat(type="json_object")

    with patch("smartrouter.router.dispatcher.RouterClient") as MockClient:
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        await dispatcher.dispatch(dummy_request)

        # Upgrades to 'mid' due to JSON mode
        assert MockClient.call_args[1]["config"].model == "mid-model"


@pytest.mark.asyncio
async def test_dispatch_shadow_mode_forces_smart_tier(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.2  # Normally cheap tier

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.logger") as mock_logger,
    ):
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        response, model_id, score = await dispatcher.dispatch(dummy_request, shadow_mode=True)

        assert response == dummy_response
        assert model_id == "smart-model"
        assert score == 0.2
        MockClient.assert_called_once()
        assert MockClient.call_args[1]["config"].model == "smart-model"

        # Verify logger was called with the correct hypothetical routing message
        mock_logger.info.assert_any_call(
            "Shadow mode is enabled. Score 0.200 would have routed to cheap tier. Forcing route to smart tier."
        )


@pytest.mark.asyncio
async def test_dispatch_fallback_from_smart_to_mid(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.9  # >= 0.8, selects smart

    with patch("smartrouter.router.dispatcher.RouterClient") as MockClient:
        # Create an error mimicking a 500 status code
        error_response = httpx.Response(
            500, request=httpx.Request("POST", "http://smart.com")
        )
        http_error = httpx.HTTPStatusError(
            "500 Error", request=error_response.request, response=error_response
        )

        instance = MockClient.return_value
        instance.generate = AsyncMock(side_effect=[http_error, dummy_response])

        dispatcher = RouterDispatcher()
        response, model, _ = await dispatcher.dispatch(dummy_request)

        assert response == dummy_response
        assert model == "mid-model"
        assert MockClient.call_count == 2
        assert MockClient.call_args_list[0][1]["config"].model == "smart-model"
        assert MockClient.call_args_list[1][1]["config"].model == "mid-model"


@pytest.mark.asyncio
async def test_dispatch_fallback_exhausted(
    mock_settings, mock_classifier, dummy_request
):
    mock_classifier.score_prompt.return_value = 0.9  # >= 0.8, selects smart

    with patch("smartrouter.router.dispatcher.RouterClient") as MockClient:
        # Create an error mimicking a 500 status code
        error_response = httpx.Response(
            500, request=httpx.Request("POST", "http://smart.com")
        )
        http_error = httpx.HTTPStatusError(
            "500 Error", request=error_response.request, response=error_response
        )

        instance = MockClient.return_value
        instance.generate = AsyncMock(side_effect=[http_error, http_error, http_error])

        dispatcher = RouterDispatcher()

        with pytest.raises(httpx.HTTPStatusError):
            await dispatcher.dispatch(dummy_request)

        assert MockClient.call_count == 3
        assert MockClient.call_args_list[0][1]["config"].model == "smart-model"
        assert MockClient.call_args_list[1][1]["config"].model == "mid-model"
        assert MockClient.call_args_list[2][1]["config"].model == "cheap-model"

@pytest.mark.asyncio
async def test_dispatch_budget_circuit_breaker(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_settings.return_value.router.budget_limit_usd = 10.0
    mock_classifier.score_prompt.return_value = 0.9  # Normally selects smart tier

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.usage_tracker") as mock_usage_tracker,
    ):
        mock_usage_tracker.total_spent_usd = 15.0 # Exceeds budget

        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        response, model_id, score = await dispatcher.dispatch(dummy_request)

        assert response == dummy_response
        assert model_id == "cheap-model" # Forced to cheap
        assert score == 0.9
        MockClient.assert_called_once()
        assert MockClient.call_args[1]["config"].model == "cheap-model"

@pytest.mark.asyncio
async def test_cost_recorded_after_dispatch(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.9  # Selects smart tier

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.usage_tracker") as mock_usage_tracker,
    ):
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        await dispatcher.dispatch(dummy_request)

        mock_usage_tracker.record_usage.assert_called_once_with(0.02, 0.02)
