from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    whisper_model: str = "base"
    # set to empty string or omit to let Whisper auto-detect language
    whisper_language: Optional[str] = "th"
    audio_base_path: str = "/audio"
    # "path" = read from mounted volume, "url" = download from remote URL
    default_source_type: str = "path"


settings = Settings()
