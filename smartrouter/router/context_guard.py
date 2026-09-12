from smartrouter.api.models import ChatMessage


def estimate_token_count(messages: list[ChatMessage]) -> int:
    """
    Estimates the token count of a list of ChatMessages.
    Heuristic: 1 token ≈ 4 characters of text, plus 5 tokens overhead per message.
    """
    total_tokens = 0
    for message in messages:
        total_tokens += (len(message.content) // 4) + 5
    return total_tokens

def check_context_limit(messages: list[ChatMessage], max_tokens: int | None) -> bool:
    """
    Checks if the estimated token count of messages is within the max_tokens limit.
    Returns True if safe (or no limit), False if it exceeds the limit.
    """
    if max_tokens is None:
        return True
    return estimate_token_count(messages) <= max_tokens
