from smartrouter.core.config import RouterConfig, Settings, TierConfig, get_settings


def test_tier_config_defaults():
    config = TierConfig(base_url="http://test", model="test-model")
    assert config.base_url == "http://test"
    assert config.model == "test-model"
    assert config.api_key is None
    assert config.timeout_seconds == 30


def test_tier_config_env_expansion(monkeypatch):
    monkeypatch.setenv("TEST_API_KEY", "super_secret")
    config = TierConfig(
        base_url="http://test", model="test-model", api_key="${TEST_API_KEY}"
    )
    assert config.api_key == "super_secret"


def test_router_config_defaults():
    config = RouterConfig()
    assert config.low_threshold == 0.4
    assert config.high_threshold == 0.8


def test_get_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("MY_FAKE_KEY", "12345")
    yaml_content = """
    router:
      low_threshold: 0.3
      high_threshold: 0.9
    tiers:
      cheap:
        base_url: "http://cheap"
        model: "cheap-model"
      mid:
        base_url: "http://mid"
        model: "mid-model"
        api_key: "${MY_FAKE_KEY}"
      smart:
        base_url: "http://smart"
        model: "smart-model"
        timeout_seconds: 60
    """

    config_file = tmp_path / "test_smartrouter.yaml"
    config_file.write_text(yaml_content)

    # Need to clear lru_cache since get_settings might be cached across tests
    get_settings.cache_clear()

    settings = get_settings(str(config_file))

    assert isinstance(settings, Settings)
    assert settings.router.low_threshold == 0.3
    assert settings.router.high_threshold == 0.9

    assert settings.tiers.cheap.base_url == "http://cheap"
    assert settings.tiers.cheap.api_key is None

    assert settings.tiers.mid.api_key == "12345"

    assert settings.tiers.smart.timeout_seconds == 60
