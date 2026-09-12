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


def compress_context(messages: list[ChatMessage], max_tokens: int) -> list[ChatMessage]:
    """
    Compresses chat history by removing messages (starting from index 1)
    if the token count exceeds max_tokens.
    Preserves the first message (index 0) and the two most recent messages.
    """
    current_tokens = estimate_token_count(messages)
    if len(messages) <= 3 or current_tokens <= max_tokens:
        return messages

    compressed_messages = list(messages)

    while len(compressed_messages) > 3 and current_tokens > max_tokens:
        # Remove message at index 1
        removed_message = compressed_messages.pop(1)
        # Deduct its token count
        removed_tokens = (len(removed_message.content) // 4) + 5
        current_tokens -= removed_tokens

    return compressed_messages
