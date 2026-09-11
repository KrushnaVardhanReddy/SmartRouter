import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from smartrouter.main import app


@pytest_asyncio.fixture(loop_scope="function")
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
