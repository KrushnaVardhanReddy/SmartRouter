import httpx
from fastapi import APIRouter, HTTPException, Response

from smartrouter.api.models import ChatCompletionRequest, ChatCompletionResponse
from smartrouter.router.dispatcher import RouterDispatcher

router = APIRouter()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    response: Response,
) -> ChatCompletionResponse:
    try:
        dispatcher = RouterDispatcher()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        completion_response, model_id, score = await dispatcher.dispatch(request)
        response.headers["X-SmartRouter-Model"] = model_id
        response.headers["X-SmartRouter-Score"] = f"{score:.3f}"
        return completion_response
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        detail = f"Upstream API error: {e.response.text}"
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
