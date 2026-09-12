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
async def chat_completions_mock(request: ChatCompletionRequest):
    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=request.model or "mock-model",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant", content="Hello from SmartRouter mock!"
                ),
                finish_reason="stop",
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=10, completion_tokens=10, total_tokens=20
        ),
    )
