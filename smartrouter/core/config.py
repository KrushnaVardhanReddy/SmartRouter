import functools
import os

import yaml
from pydantic import BaseModel, field_validator


class TierConfig(BaseModel):
    base_url: str
    model: str
    api_key: str | None = None
    timeout_seconds: int = 30

    @field_validator('api_key', mode='before')
    @classmethod
    def expand_env_vars(cls, v: str | None) -> str | None:
        if v is not None and isinstance(v, str):
            return os.path.expandvars(v)
        return v

class RouterConfig(BaseModel):
    low_threshold: float = 0.4
    high_threshold: float = 0.8

class TiersConfig(BaseModel):
    cheap: TierConfig
    mid: TierConfig
    smart: TierConfig

class Settings(BaseModel):
    router: RouterConfig
    tiers: TiersConfig

@functools.lru_cache
def get_settings(config_path: str = "smartrouter.yaml") -> Settings:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Settings(**data)
