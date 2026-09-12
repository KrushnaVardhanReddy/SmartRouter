from smartrouter.api.models import ChatMessage
from smartrouter.router.context_guard import check_context_limit, estimate_token_count


def test_estimate_token_count_empty_messages():
    assert estimate_token_count([]) == 0

def test_estimate_token_count_single_message():
    message = ChatMessage(role="user", content="This is a test message. It has 44 characters!!") # 44 chars -> 11 tokens + 5 = 16
    assert estimate_token_count([message]) == 16

def test_estimate_token_count_multiple_messages():
    messages = [
        ChatMessage(role="system", content="System msg"), # 10 chars -> 2 tokens + 5 = 7
        ChatMessage(role="user", content="Hi"),           # 2 chars -> 0 tokens + 5 = 5
        ChatMessage(role="assistant", content="Hello!")   # 6 chars -> 1 token + 5 = 6
    ]
    # Total: 7 + 5 + 6 = 18
    assert estimate_token_count(messages) == 18

def test_check_context_limit_no_limit():
    messages = [ChatMessage(role="user", content="Hello")]
    assert check_context_limit(messages, None) is True

def test_check_context_limit_within_limit():
    message = ChatMessage(role="user", content="This is a test message. It has 44 characters!!") # 16 tokens
    assert check_context_limit([message], 16) is True
    assert check_context_limit([message], 20) is True

def test_check_context_limit_exceeds_limit():
    message = ChatMessage(role="user", content="This is a test message. It has 44 characters!!") # 16 tokens
    assert check_context_limit([message], 15) is False
