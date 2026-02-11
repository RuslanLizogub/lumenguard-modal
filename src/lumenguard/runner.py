from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import httpx

from .config import RuntimeConfig, load_runtime_config
from .logic import (
    SavedState,
    check_ip,
    compare_states,
    format_ua_message,
    load_state,
    save_state,
)


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


def coerce_state(raw_state: Any) -> dict[str, SavedState]:
    """Normalize external state object to SavedState dictionary."""
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
