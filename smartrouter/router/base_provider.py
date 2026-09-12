from abc import ABC, abstractmethod

from smartrouter.api.models import ChatCompletionRequest, ChatCompletionResponse


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.
    """

    @abstractmethod
    async def generate(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Generate a response given a chat completion request.
        """
