from smartrouter.api.models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    ChatMessage,
)


def test_chat_message_valid() -> None:
    msg = ChatMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_chat_completion_request_defaults() -> None:
    req = ChatCompletionRequest(messages=[ChatMessage(role="user", content="Test")])
    assert req.temperature == 1.0
    assert req.stream is False
    assert req.max_tokens is None
    assert req.model is None


def test_chat_completion_choice() -> None:
    choice = ChatCompletionChoice(
        index=0,
        message=ChatMessage(role="assistant", content="Hi"),
        finish_reason="stop",
    )
    assert choice.index == 0
    assert choice.message.content == "Hi"
    assert choice.finish_reason == "stop"


def test_chat_completion_usage() -> None:
    usage = ChatCompletionUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    assert usage.prompt_tokens == 10
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 30


def test_chat_completion_response_valid() -> None:
    resp = ChatCompletionResponse(
        id="chatcmpl-123",
        created=1677652288,
        model="gpt-3.5-turbo-0301",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content="Hello there"),
                finish_reason="stop",
            )
        ],
    )
    assert resp.id == "chatcmpl-123"
    assert resp.object == "chat.completion"
    assert resp.created == 1677652288
    assert resp.model == "gpt-3.5-turbo-0301"
    assert len(resp.choices) == 1
    assert resp.usage is None
