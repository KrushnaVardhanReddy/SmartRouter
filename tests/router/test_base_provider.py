import pytest

from smartrouter.api.models import ChatCompletionRequest, ChatCompletionResponse
from smartrouter.router.base_provider import BaseProvider


def test_base_provider_is_abstract():
    """
    Test that BaseProvider cannot be instantiated directly.
    """
    with pytest.raises(
        TypeError, match="Can't instantiate abstract class BaseProvider"
    ):
        BaseProvider()


class DummyProvider(BaseProvider):
    async def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        return ChatCompletionResponse(
            id="dummy_id", created=1234567890, model="dummy_model", choices=[]
        )


def test_dummy_provider_can_be_instantiated():
    """
    Test that a class implementing BaseProvider can be instantiated.
    """
    provider = DummyProvider()
    assert isinstance(provider, BaseProvider)
