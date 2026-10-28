from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "vobiassist"
    app_version: str = "0.1.0"
    database_url: str = "sqlite:///./vobiassist.db"
    vobiz_auth_id: str = ""
    vobiz_auth_token: str = ""
    vobiz_base_url: str = "https://api.vobiz.ai"
    enable_real_calls: bool = False
    ai_provider: str = "rules"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = ""
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
