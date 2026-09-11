import pytest
from httpx import ASGITransport, AsyncClient

from smartrouter.main import app


@pytest.mark.asyncio
async def test_chat_completions_mock_route():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello!"}],
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["content"] == "Hello from SmartRouter mock!"
