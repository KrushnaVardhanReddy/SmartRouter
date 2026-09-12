import httpx
import pytest
import respx

from smartrouter.api.models import ChatMessage
from smartrouter.router.context_guard import (
    check_context_limit,
    compress_context,
    estimate_token_count,
)


def test_estimate_token_count_empty_messages():
    assert estimate_token_count([]) == 0


def test_estimate_token_count_single_message():
    message = ChatMessage(
        role="user", content="This is a test message. It has 44 characters!!"
    )  # 44 chars -> 11 tokens + 5 = 16
    assert estimate_token_count([message]) == 16


def test_estimate_token_count_multiple_messages():
    messages = [
        ChatMessage(
            role="system", content="System msg"
        ),  # 10 chars -> 2 tokens + 5 = 7
        ChatMessage(role="user", content="Hi"),  # 2 chars -> 0 tokens + 5 = 5
        ChatMessage(role="assistant", content="Hello!"),  # 6 chars -> 1 token + 5 = 6
    ]
    # Total: 7 + 5 + 6 = 18
    assert estimate_token_count(messages) == 18


def test_check_context_limit_no_limit():
    messages = [ChatMessage(role="user", content="Hello")]
    assert check_context_limit(messages, None) is True


def test_check_context_limit_within_limit():
    message = ChatMessage(
        role="user", content="This is a test message. It has 44 characters!!"
    )  # 16 tokens
    assert check_context_limit([message], 16) is True
    assert check_context_limit([message], 20) is True


def test_check_context_limit_exceeds_limit():
    message = ChatMessage(
        role="user", content="This is a test message. It has 44 characters!!"
    )  # 16 tokens
    assert check_context_limit([message], 15) is False


@pytest.mark.asyncio
async def test_compress_context_few_messages():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="User 1"),
        ChatMessage(role="assistant", content="Assistant 1"),
    ]
    # No compression should occur because there are <= 5 messages
    compressed = await compress_context(messages, 0, "http://fake", "model", "key")
    assert compressed == messages


@pytest.mark.asyncio
async def test_compress_context_within_limit():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="User 1"),
        ChatMessage(role="assistant", content="Assistant 1"),
        ChatMessage(role="user", content="User 2"),
    ]
    # Limit is 1000 tokens, which this easily fits within. No compression.
    compressed = await compress_context(messages, 1000, "http://fake", "model", "key")
    assert compressed == messages


@pytest.mark.asyncio
async def test_compress_context_exceeds_limit_successful_compression():
    messages = [
        ChatMessage(role="system", content="System"),  # index 0
        ChatMessage(
            role="user",
            content="A very very very very very long message that should be removed",
        ),  # index 1 - dropped
        ChatMessage(role="assistant", content="Yes"),  # index 2 - kept
        ChatMessage(
            role="user", content="Another long one that should be removed to fit"
        ),  # index 3 - kept
        ChatMessage(role="assistant", content="Indeed"),  # index 4 - kept
        ChatMessage(role="user", content="Short user"),  # index 5 - kept
    ]
    # Total 6 messages.
    # With new logic, it should drop message at index 1 because we keep last 4.

    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post("http://fake/chat/completions").respond(
            json={"choices": [{"message": {"content": "Summary text"}}]}
        )
        compressed = await compress_context(messages, 30, "http://fake", "model", "key")

    # The summary is inserted. Total messages should be:
    # [system, summary, messages[-4:]] -> length 6
    assert len(compressed) == 6
    assert compressed[0] == messages[0]  # System kept
    assert compressed[1].content == "[Context Summary] Summary text"
    assert compressed[2] == messages[-4]
    assert compressed[-1] == messages[-1]  # Last user kept
    assert compressed[-2] == messages[-2]  # Last assistant kept


@pytest.mark.asyncio
async def test_compress_context_exceeds_limit_unsuccessful_compression():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="Old"),
        ChatMessage(role="assistant", content="Old"),
        ChatMessage(role="user", content="Old"),
        ChatMessage(
            role="assistant",
            content="A very very long assistant reply that takes up all the tokens by itself and causes the total limit to still be exceeded even if we drop all older messages."
            * 10,
        ),
        ChatMessage(role="user", content="Short user"),
        ChatMessage(role="assistant", content="Dummy"),
        ChatMessage(role="user", content="Dummy"),
    ]
    # Need at least 6 messages to trigger dropping.
    # Set a very low limit. The last 4 messages alone exceed this limit.
    limit = 50
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post("http://fake/chat/completions").respond(
            json={"choices": [{"message": {"content": "Summary of old stuff"}}]}
        )
        compressed = await compress_context(
            messages, limit, "http://fake", "model", "key"
        )

    # It should compress down to exactly 6 messages now (system, summary, last 4)
    assert len(compressed) == 6
    assert compressed[0] == messages[0]
    assert compressed[1].content == "[Context Summary] Summary of old stuff"
    assert compressed[2] == messages[-4]
    assert compressed[5] == messages[-1]


@pytest.mark.asyncio
async def test_compress_context_summarizes_dropped_messages():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="Drop me 1"),
        ChatMessage(role="assistant", content="Drop me 2"),
        ChatMessage(role="user", content="Keep me 1"),
        ChatMessage(role="assistant", content="Keep me 2"),
        ChatMessage(role="user", content="Keep me 3"),
        ChatMessage(role="assistant", content="Keep me 4"),
    ]

    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.post("http://fake/chat/completions").respond(
            json={"choices": [{"message": {"content": "I am a summary"}}]}
        )
        # Limit 0 forces it to drop as much as possible, leaving only system and last 4 messages + summary
        compressed = await compress_context(messages, 0, "http://fake", "model", "key")

        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer key"

        # Checking that the prompt contains the dropped messages
        payload = request.content.decode("utf-8")
        assert "Drop me 1" in payload
        assert "Drop me 2" in payload
        assert "Keep me 1" not in payload  # kept
        assert "Keep me 2" not in payload  # kept
        assert "Keep me 3" not in payload  # kept
        assert "Keep me 4" not in payload  # kept

    assert len(compressed) == 6
    assert compressed[1].role == "assistant"
    assert compressed[1].content == "[Context Summary] I am a summary"


@pytest.mark.asyncio
async def test_compress_context_falls_back_on_summarizer_failure():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="Drop me 1"),
        ChatMessage(role="assistant", content="Drop me 2"),
        ChatMessage(role="user", content="Keep me 1"),
        ChatMessage(role="assistant", content="Keep me 2"),
        ChatMessage(role="user", content="Keep me 3"),
        ChatMessage(role="assistant", content="Keep me 4"),
    ]

    with respx.mock(assert_all_called=True) as respx_mock:
        route = respx_mock.post("http://fake/chat/completions").mock(
            side_effect=httpx.RequestError("Network failure")
        )
        # Should catch the error and fallback to naive compression (no summary message)
        compressed = await compress_context(messages, 0, "http://fake", "model", "key")

        assert route.called

    assert len(compressed) == 5
    assert compressed[0] == messages[0]
    assert compressed[1] == messages[-4]
    assert compressed[2] == messages[-3]
    assert compressed[3] == messages[-2]
    assert compressed[4] == messages[-1]
