import time
import uuid

from fastapi import FastAPI

from smartrouter.api.models import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    ChatMessage,
)

app = FastAPI(title="SmartRouter", version="1.0.0")


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
) -> ChatCompletionResponse:
    # Phase 1: Return a hardcoded mock response
    message = ChatMessage(role="assistant", content="Hello from SmartRouter mock!")
    choice = ChatCompletionChoice(index=0, message=message, finish_reason="stop")
    usage = ChatCompletionUsage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )

    response = ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4()}",
        object="chat.completion",
        created=int(time.time()),
        model=request.model or "mock-model",
        choices=[choice],
        usage=usage,
    )

    return response
