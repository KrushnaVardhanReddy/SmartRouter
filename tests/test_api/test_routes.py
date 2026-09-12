import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_completions_mock(async_client: AsyncClient):
    payload = {"messages": [{"role": "user", "content": "Hi"}]}
    response = await async_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["content"] == "Hello from SmartRouter mock!"


@pytest.mark.asyncio
async def test_chat_completions_invalid_payload(async_client: AsyncClient):
    payload = {
        # missing messages
        "model": "some-model"
    }
    response = await async_client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 422
