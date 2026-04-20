from __future__ import annotations

import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class MonitorTarget(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    chat_id: str = Field(min_length=1)


class RuntimeConfig(BaseModel):
    telegram_bot_token: str = Field(min_length=10)
    monitor_config: list[MonitorTarget] = Field(min_length=1)
    check_interval_seconds: int = Field(default=300, ge=60)
    check_timeout_seconds: float = Field(default=3.0, gt=0)
    check_attempts: int = Field(default=3, ge=1, le=10)
    check_attempt_delay_seconds: float = Field(default=2.0, ge=0, le=30)
    offline_confirmation_cycles: int = Field(default=2, ge=1, le=10)
    online_confirmation_cycles: int = Field(default=2, ge=1, le=10)
    include_target_name_in_message: bool = False
    state_path: str = Field(default="state.json", min_length=1)
    timezone_name: str = Field(default="Europe/Kyiv", min_length=1)


def load_runtime_config() -> RuntimeConfig:
    """Load and validate runtime configuration from environment variables."""
    load_dotenv()

    raw_monitor_config = os.getenv("MONITOR_CONFIG", "[]")
    try:
        monitor_config_data = json.loads(raw_monitor_config)
    except json.JSONDecodeError as exc:
        raise RuntimeError("MONITOR_CONFIG має бути валідним JSON-масивом.") from exc

    data = {
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "monitor_config": monitor_config_data,
        "check_interval_seconds": os.getenv("CHECK_INTERVAL_SECONDS", "300"),
        "check_timeout_seconds": os.getenv("CHECK_TIMEOUT_SECONDS", "3"),
        "check_attempts": os.getenv("CHECK_ATTEMPTS", "3"),
        "check_attempt_delay_seconds": os.getenv("CHECK_ATTEMPT_DELAY_SECONDS", "2"),
        "offline_confirmation_cycles": os.getenv("OFFLINE_CONFIRMATION_CYCLES", "2"),
        "online_confirmation_cycles": os.getenv("ONLINE_CONFIRMATION_CYCLES", "2"),
        "include_target_name_in_message": os.getenv("INCLUDE_TARGET_NAME_IN_MESSAGE", "false"),
        "state_path": os.getenv("STATE_PATH", "state.json"),
        "timezone_name": os.getenv("TIMEZONE", "Europe/Kyiv"),
    }

    try:
        return RuntimeConfig.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(f"Некоректна конфігурація: {exc}") from exc
