import logging

from httpx import AsyncClient

from smartrouter.api.models import ChatMessage

logger = logging.getLogger(__name__)


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


async def compress_context(
    messages: list[ChatMessage],
    max_tokens: int,
    summarizer_base_url: str,
    summarizer_model: str,
    summarizer_api_key: str,
) -> list[ChatMessage]:
    """
    Compresses chat history by removing messages (starting from index 1)
    if the token count exceeds max_tokens.
    Preserves the first message (index 0) and the two most recent turns (4 messages).
    Uses an LLM to generate a rolling summary of the dropped messages.
    """
    current_tokens = estimate_token_count(messages)
    if len(messages) <= 5 or current_tokens <= max_tokens:
        return messages

    # Keep index 0 (system) and last 4 messages. Drop the rest.
    dropped_messages = messages[1:-4]
    if not dropped_messages:
        return messages

    # Base compressed messages format without summary
    compressed_messages = [messages[0]] + messages[-4:]

    # Build the summarization prompt
    dropped_text = "\n".join([f"{msg.role}: {msg.content}" for msg in dropped_messages])
    prompt = (
        "Summarize the following conversation history concisely in 2-3 sentences:\n"
        f"{dropped_text}"
    )

    headers = {
        "Authorization": f"Bearer {summarizer_api_key}",
        "Content-Type": "application/json",
    }
    # Anthropic compatibility
    if "anthropic" in summarizer_base_url.lower():
        headers["anthropic-version"] = "2023-06-01"

    payload = {
        "model": summarizer_model,
        "messages": [{"role": "user", "content": prompt}],
    }

    endpoint = f"{summarizer_base_url.rstrip('/')}/chat/completions"

    try:
        async with AsyncClient() as client:
            response = await client.post(endpoint, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            response_data = response.json()
            summary = response_data["choices"][0]["message"]["content"]

            # Insert the summary as a synthetic assistant message
            summary_message = ChatMessage(
                role="assistant",
                content=f"[Context Summary] {summary}"
            )
            compressed_messages.insert(1, summary_message)

    except Exception as e:
        logger.warning(f"Failed to summarize dropped messages. Falling back to naive trimming. Error: {e}")
        # Return the naively compressed messages without the summary

    return compressed_messages
