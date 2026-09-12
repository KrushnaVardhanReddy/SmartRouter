with open("tests/test_api/test_routes.py", "r") as f:
    content = f.read()

# Add type hints to mock_provider_api_keys and test_chat_completions_e2e
import re

content = re.sub(
    r"def mock_provider_api_keys\(monkeypatch\):",
    r"def mock_provider_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:",
    content,
)

content = re.sub(
    r"async def test_chat_completions_e2e\(\n    async_client: AsyncClient, mock_provider_api_keys\n\):",
    r"async def test_chat_completions_e2e(\n    async_client: AsyncClient, mock_provider_api_keys: None\n) -> None:",
    content,
)

# And add host="test" pass through to respx
content = content.replace(
    'respx_mock.route(host="huggingface.co").pass_through()',
    'respx_mock.route(host="huggingface.co").pass_through()\n        respx_mock.route(host="test").pass_through()',
)

with open("tests/test_api/test_routes.py", "w") as f:
    f.write(content)
