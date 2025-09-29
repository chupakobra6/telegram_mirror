"""Settings configuration using Pydantic."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class TelegramSettings(BaseModel):
    """Telegram client settings."""
    
    api_id: int
    api_hash: str
    session_name: str = "telegram_mirror"


class DatabaseSettings(BaseModel):
    """Database connection settings."""
    
    url: str = Field(default="sqlite+aiosqlite:///./telegram_mirror.db")
    echo: bool = Field(default=False)
    pool_size: int = Field(default=10)
    max_overflow: int = Field(default=20)


class BotSettings(BaseModel):
    """Telegram bot settings."""
    
    token: str | None = None
    webhook_url: str | None = None
    webhook_secret_token: str | None = None


class MirrorSettings(BaseModel):
    """Mirror configuration settings."""
    
    source_chat_ids: list[int] = Field(default_factory=list)
    target_chat_ids: list[int] = Field(default_factory=list)
    admin_user_ids: list[int] = Field(default_factory=list)
    allowed_user_ids: list[int] = Field(default_factory=list)
    render_images: bool = Field(default=True)
    max_image_width: int = Field(default=800)
    max_image_height: int = Field(default=1200)
    
    @field_validator('source_chat_ids', 'target_chat_ids', 'admin_user_ids', 'allowed_user_ids', mode='before')
    @classmethod
    def parse_int_list(cls, v):
        """Parse comma-separated string or list of integers."""
        if isinstance(v, str):
            if not v.strip():  # Empty string
                return []
            # Handle both comma-separated and bracket formats
            v = v.strip().strip('[]')
            if not v:
                return []
            return [int(x.strip()) for x in v.split(',') if x.strip()]
        elif isinstance(v, (list, tuple)):
            return [int(x) for x in v if str(x).strip()]
        elif isinstance(v, int):
            return [v]  # Single integer to list
        return v or []


class RenderSettings(BaseModel):
    """Message rendering settings."""
    
    font_family: str = Field(default="Arial")
    font_size: int = Field(default=14)
    background_color: str = Field(default="#FFFFFF")
    text_color: str = Field(default="#000000")
    padding: int = Field(default=20)
    border_radius: int = Field(default=10)


class LoggingSettings(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_path: str | None = None
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    backup_count: int = Field(default=5)


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
    )
    
    # Core settings
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    
    # Component settings
    telegram: TelegramSettings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    bot: BotSettings = Field(default_factory=BotSettings)
    mirror: MirrorSettings = Field(default_factory=MirrorSettings)
    render: RenderSettings = Field(default_factory=RenderSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "production", "testing"}
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()
    
    @field_validator("telegram")
    @classmethod
    def validate_telegram_settings(cls, v: TelegramSettings) -> TelegramSettings:
        """Validate Telegram settings."""
        if not v.api_id or not v.api_hash:
            raise ValueError("Telegram API_ID and API_HASH must be provided")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def configure_logging(settings: Settings) -> None:
    """Configure application logging."""
    level_map = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'NOTSET': logging.NOTSET,
    }
    logging.basicConfig(
        level=level_map.get(settings.logging.level.upper(), logging.INFO),
        format=settings.logging.format,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    if settings.logging.file_path:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            settings.logging.file_path,
            maxBytes=settings.logging.max_file_size,
            backupCount=settings.logging.backup_count,
        )
        file_handler.setFormatter(
            logging.Formatter(settings.logging.format)
        )
        logging.getLogger().addHandler(file_handler)
    
    # Set specific loggers
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if settings.database.echo else logging.WARNING) 