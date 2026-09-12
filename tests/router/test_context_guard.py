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


def test_compress_context_few_messages():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="User 1"),
        ChatMessage(role="assistant", content="Assistant 1"),
    ]
    # No compression should occur because there are <= 3 messages
    assert compress_context(messages, 0) == messages


def test_compress_context_within_limit():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="User 1"),
        ChatMessage(role="assistant", content="Assistant 1"),
        ChatMessage(role="user", content="User 2"),
    ]
    # Limit is 1000 tokens, which this easily fits within. No compression.
    assert compress_context(messages, 1000) == messages


def test_compress_context_exceeds_limit_successful_compression():
    messages = [
        ChatMessage(role="system", content="System"), # ~ 6 tokens
        ChatMessage(role="user", content="A very very very very very long message that should be removed"), # ~ 20 tokens
        ChatMessage(role="assistant", content="Yes"), # ~ 5 tokens
        ChatMessage(role="user", content="Another long one that should be removed to fit"), # ~ 16 tokens
        ChatMessage(role="assistant", content="Indeed"), # ~ 6 tokens
        ChatMessage(role="user", content="Short user"), # ~ 7 tokens
    ]
    # Total tokens is about 6 + 20 + 5 + 16 + 6 + 7 = 60.
    # Set limit to 30.

    compressed = compress_context(messages, 30)

    # Should drop index 1, then index 1 again, until it fits or reaches 3 messages.
    # We want it to fit.
    # After dropping 2nd message (20 tokens), total = 40.
    # After dropping 3rd message ("Yes", 5 tokens), total = 35.
    # After dropping 4th message (16 tokens), total = 19. Now it fits.
    assert estimate_token_count(compressed) <= 30
    assert compressed[0] == messages[0] # System kept
    assert compressed[-1] == messages[-1] # Last user kept
    assert compressed[-2] == messages[-2] # Last assistant kept


def test_compress_context_exceeds_limit_unsuccessful_compression():
    messages = [
        ChatMessage(role="system", content="System"),
        ChatMessage(role="user", content="Old"),
        ChatMessage(role="assistant", content="Old"),
        ChatMessage(role="user", content="Old"),
        ChatMessage(role="assistant", content="A very very long assistant reply that takes up all the tokens by itself and causes the total limit to still be exceeded even if we drop all older messages." * 10),
        ChatMessage(role="user", content="Short user"),
    ]
    # Set a very low limit. The last 2 messages alone exceed this limit.
    limit = 50
    compressed = compress_context(messages, limit)

    # It should compress down to exactly 3 messages, but no further
    assert len(compressed) == 3
    assert compressed[0] == messages[0]
    assert compressed[1] == messages[-2]
    assert compressed[2] == messages[-1]

    # And it will still exceed the limit
    assert estimate_token_count(compressed) > limit
