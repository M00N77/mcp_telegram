import sys
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Config(BaseSettings):
    telegram_bot_token: str = Field(..., description="Telegram Bot API Token")
    db_path: str = Field(default="./data.db", description="Path to SQLite database")
    auto_approve: bool = Field(default=False, description="Disable Human-in-the-Loop for send_message")
    tz: str = Field(default="UTC", description="Timezone for formatting")
    poll_timeout: int = Field(default=25, description="Long-polling timeout in seconds")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

try:
    settings = Config()
except Exception as e:
    sys.stderr.write(f"Configuration error: {e}\n")
    sys.exit(1)
