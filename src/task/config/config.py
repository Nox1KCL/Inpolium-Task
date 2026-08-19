from pathlib import Path
import tomllib
from typing import Self

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from task.helpers import get_logs_dir


class AppConfig(BaseModel):
    app_name: str
    steam_api_url: str
    steam_base_url: str
    http_timeout: float
    max_retries: int
    browser_timeout_ms: float
    browser_viewport_width: int
    browser_viewport_height: int

class LoggerConfig(BaseModel):
    level: str = Field(default="INFO")
    logs_dir: str = Field(default_factory=get_logs_dir)
    max_size: str = Field(default="10 MB")
    retention: str = Field(default="30 days")
    compression: str = Field(default="zip")
    json_format: bool = Field(default=True)

class Config(BaseSettings):
    app: AppConfig
    logger: LoggerConfig

    @classmethod
    def load_config(cls, config_path: str | Path = "config.toml") -> Self:
        path = Path(config_path)
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data)
