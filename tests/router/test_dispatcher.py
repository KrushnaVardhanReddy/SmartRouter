from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from smartrouter.api.models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
)
from smartrouter.router.dispatcher import RouterDispatcher


@pytest.fixture
def mock_settings():
    with patch("smartrouter.router.dispatcher.get_settings") as mock_get_settings:
        settings = MagicMock()
        settings.router.low_threshold = 0.4
        settings.router.high_threshold = 0.8
        settings.router.shadow_mode = False

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
        response = await dispatcher.dispatch(dummy_request)

        assert response == dummy_response
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
        await dispatcher.dispatch(dummy_request)

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
        await dispatcher.dispatch(dummy_request)

        assert MockClient.call_args[1]["config"].model == "smart-model"


@pytest.mark.asyncio
async def test_dispatch_upgrades_tier_due_to_context_limit(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_classifier.score_prompt.return_value = 0.3  # Initially picks cheap

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.check_context_limit", return_value=False),
    ):  # Force context limit exceed
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        await dispatcher.dispatch(dummy_request)

        # Upgrades to 'mid' and then 'mid' also exceeds, so upgrades to 'smart'
        assert MockClient.call_args[1]["config"].model == "smart-model"


@pytest.mark.asyncio
async def test_dispatch_shadow_mode_logging(
    mock_settings, mock_classifier, dummy_request, dummy_response
):
    mock_settings.return_value.router.shadow_mode = True

    with (
        patch("smartrouter.router.dispatcher.RouterClient") as MockClient,
        patch("smartrouter.router.dispatcher.logger") as mock_logger,
    ):
        instance = MockClient.return_value
        instance.generate = AsyncMock(return_value=dummy_response)

        dispatcher = RouterDispatcher()
        await dispatcher.dispatch(dummy_request)

        # Verify logger was called with shadow mode message
        mock_logger.info.assert_any_call(
            "Shadow mode is enabled. Proceeding with standard routing for now."
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
        response = await dispatcher.dispatch(dummy_request)

        assert response == dummy_response
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
