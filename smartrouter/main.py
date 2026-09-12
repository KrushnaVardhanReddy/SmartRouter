import httpx
from fastapi import FastAPI, Header, HTTPException

from smartrouter.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from smartrouter.router.dispatcher import RouterDispatcher

app = FastAPI(title="SmartRouter", version="1.0.0")


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    x_smartrouter_shadow: bool = Header(default=False, alias="X-SmartRouter-Shadow"),
) -> ChatCompletionResponse:
    try:
        dispatcher = RouterDispatcher()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        response = await dispatcher.dispatch(request, is_shadow_mode=x_smartrouter_shadow)
        return response
    except httpx.HTTPStatusError as e:
        # Pass through the upstream HTTP error status code and details if possible
        status_code = e.response.status_code
        detail = f"Upstream API error: {e.response.text}"
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
