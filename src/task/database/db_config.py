from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from task.helpers import get_env_path


class DB_Config(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=get_env_path(),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @computed_field
    @property
    def get_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
