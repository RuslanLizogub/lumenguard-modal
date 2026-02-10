from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from logic import (
    SavedState,
    check_ip,
    compare_states,
    format_ua_message,
    load_state,
    save_state,
)


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
        "state_path": os.getenv("STATE_PATH", "state.json"),
        "timezone_name": os.getenv("TIMEZONE", "Europe/Kyiv"),
    }

    try:
        return RuntimeConfig.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError(f"Некоректна конфігурація: {exc}") from exc


def send_telegram_message(bot_token: str, chat_id: str, text: str) -> bool:
    """Send message to Telegram channel/chat."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        print(f"Помилка Telegram API для chat_id={chat_id}: {exc}")
        return False


def run_cycle(
    config: RuntimeConfig,
    state: dict[str, SavedState],
    *,
    now: datetime | None = None,
) -> tuple[dict[str, SavedState], bool]:
    """Run one full monitoring cycle for all targets."""
    run_time = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)
    has_state_update = False

    for target in config.monitor_config:
        is_online = check_ip(target.host, target.port, timeout=config.check_timeout_seconds)
        comparison = compare_states(state.get(target.id), is_online, now=run_time)

        status_ua = "онлайн" if is_online else "офлайн"
        if comparison.is_first_observation:
            print(f"[{target.id}] Перше спостереження: {status_ua}.")
            state[target.id] = comparison.new_state
            has_state_update = True
            continue

        if not comparison.changed:
            print(f"[{target.id}] Без змін: {status_ua}.")
            continue

        message = format_ua_message(
            target_name=target.name,
            is_online=is_online,
            duration_seconds=comparison.duration_seconds,
            now=run_time,
            timezone_name=config.timezone_name,
        )
        sent = send_telegram_message(config.telegram_bot_token, target.chat_id, message)
        if not sent:
            continue

        state[target.id] = comparison.new_state
        has_state_update = True
        print(f"[{target.id}] Статус змінився, повідомлення надіслано.")

    return state, has_state_update


def run_once_file_state() -> None:
    """Run one cycle with local JSON persistence."""
    config = load_runtime_config()
    state = load_state(config.state_path)
    state, has_state_update = run_cycle(config, state)
    if has_state_update:
        save_state(config.state_path, state)


def run_forever() -> None:
    """Run cycles every N seconds (default 5 minutes)."""
    while True:
        config = load_runtime_config()
        state = load_state(config.state_path)

        state, has_state_update = run_cycle(config, state)
        if has_state_update:
            save_state(config.state_path, state)

        time.sleep(config.check_interval_seconds)


def _coerce_state(raw_state: Any) -> dict[str, SavedState]:
    if not isinstance(raw_state, dict):
        return {}

    cleaned: dict[str, SavedState] = {}
    for target_id, value in raw_state.items():
        if not isinstance(target_id, str) or not isinstance(value, dict):
            continue

        status = value.get("status")
        changed_at = value.get("changed_at")
        if status in {"online", "offline"} and isinstance(changed_at, str):
            cleaned[target_id] = {"status": status, "changed_at": changed_at}

    return cleaned


try:
    import modal
except Exception:  # pragma: no cover - optional integration in local runs
    modal = None


if modal is not None:
    app = modal.App("lumenguard-modal")
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .pip_install_from_requirements("requirements.txt")
        # Ensure `import logic` works in Modal runtime.
        .add_local_python_source("logic", copy=True)
    )
    config_secret = modal.Secret.from_name(
        "lumenguard-config",
        required_keys=["TELEGRAM_BOT_TOKEN", "MONITOR_CONFIG"],
    )
    state_dict = modal.Dict.from_name("lumenguard-state", create_if_missing=True)

    @app.function(
        image=image,
        schedule=modal.Cron("*/5 * * * *"),
        secrets=[config_secret],
    )
    def monitor_with_modal() -> None:
        """Modal cron entrypoint: every 5 minutes."""
        config = load_runtime_config()

        raw_state = state_dict.get("state")
        state = _coerce_state(raw_state)

        state, has_state_update = run_cycle(config, state)
        if has_state_update:
            state_dict["state"] = state

    @app.local_entrypoint()
    def run(once: bool = True) -> None:
        if once:
            run_once_file_state()
        else:
            run_forever()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LUMENGUARD monitor")
    parser.add_argument("--once", action="store_true", help="Виконати один цикл і завершити")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.once:
        run_once_file_state()
    else:
        run_forever()
