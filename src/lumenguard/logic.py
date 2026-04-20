from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypedDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

Status = Literal["online", "offline"]


class SavedState(TypedDict, total=False):
    status: Status
    changed_at: str
    pending_status: Status
    pending_count: int
    pending_since: str


@dataclass(slots=True, frozen=True)
class StateComparison:
    changed: bool
    state_updated: bool
    is_first_observation: bool
    current_status: Status
    previous_status: Status | None
    duration_seconds: int
    new_state: SavedState


@dataclass(slots=True, frozen=True)
class ProbeResult:
    is_online: bool
    successful_attempts: int
    total_attempts: int
    errors: tuple[str, ...]


def check_ip(host: str, port: int, timeout: float = 3.0) -> bool:
    """Return True when TCP connection can be established."""
    is_online, _ = check_ip_once(host, port, timeout=timeout)
    return is_online


def check_ip_once(host: str, port: int, timeout: float = 3.0) -> tuple[bool, str | None]:
    """Run a single TCP check and return status plus error details."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, None
    except OSError as exc:
        return False, str(exc)


def probe_target(
    host: str,
    port: int,
    *,
    timeout: float = 3.0,
    attempts: int = 1,
    delay_seconds: float = 0.0,
) -> ProbeResult:
    """Run multiple TCP checks to reduce transient false negatives."""
    total_attempts = max(1, attempts)
    successful_attempts = 0
    errors: list[str] = []

    for attempt_index in range(total_attempts):
        is_online, error = check_ip_once(host, port, timeout=timeout)
        if is_online:
            successful_attempts += 1
        elif error:
            errors.append(error)

        if attempt_index + 1 < total_attempts and delay_seconds > 0:
            time.sleep(delay_seconds)

    return ProbeResult(
        is_online=successful_attempts > 0,
        successful_attempts=successful_attempts,
        total_attempts=total_attempts,
        errors=tuple(errors),
    )


def compare_states(
    previous_state: SavedState | None,
    is_online: bool,
    *,
    now: datetime | None = None,
    offline_confirmation_cycles: int = 1,
    online_confirmation_cycles: int = 1,
) -> StateComparison:
    """Compare current status against stored state and prepare next state."""
    current_time = _normalize_datetime(now) if now else datetime.now(timezone.utc)
    current_iso = current_time.isoformat()
    current_status: Status = "online" if is_online else "offline"

    if not previous_state:
        return StateComparison(
            changed=False,
            state_updated=True,
            is_first_observation=True,
            current_status=current_status,
            previous_status=None,
            duration_seconds=0,
            new_state={"status": current_status, "changed_at": current_iso},
        )

    previous_status_raw = previous_state.get("status")
    previous_status: Status | None = (
        previous_status_raw if previous_status_raw in {"online", "offline"} else None
    )
    if previous_status is None:
        return StateComparison(
            changed=False,
            state_updated=True,
            is_first_observation=True,
            current_status=current_status,
            previous_status=None,
            duration_seconds=0,
            new_state={"status": current_status, "changed_at": current_iso},
        )

    previous_changed_at = _parse_iso_datetime(
        previous_state.get("changed_at"),
        fallback=current_time,
    )

    if previous_status == current_status:
        new_state: SavedState = {
            "status": current_status,
            "changed_at": previous_changed_at.isoformat(),
        }
        return StateComparison(
            changed=False,
            state_updated=_has_pending_transition(previous_state),
            is_first_observation=False,
            current_status=current_status,
            previous_status=previous_status,
            duration_seconds=0,
            new_state=new_state,
        )

    pending_status_raw = previous_state.get("pending_status")
    pending_status: Status | None = (
        pending_status_raw if pending_status_raw in {"online", "offline"} else None
    )
    pending_count_raw = previous_state.get("pending_count")
    pending_count = pending_count_raw if isinstance(pending_count_raw, int) else 0
    pending_since_raw = previous_state.get("pending_since")
    pending_since = pending_since_raw if isinstance(pending_since_raw, str) else current_iso

    if pending_status == current_status:
        current_pending_count = pending_count + 1
        current_pending_since = pending_since
    else:
        current_pending_count = 1
        current_pending_since = current_iso

    required_confirmations = (
        offline_confirmation_cycles if current_status == "offline" else online_confirmation_cycles
    )

    if current_pending_count >= max(1, required_confirmations):
        duration_seconds = max(0, int((current_time - previous_changed_at).total_seconds()))
        new_state = {"status": current_status, "changed_at": current_iso}
        return StateComparison(
            changed=True,
            state_updated=True,
            is_first_observation=False,
            current_status=current_status,
            previous_status=previous_status,
            duration_seconds=duration_seconds,
            new_state=new_state,
        )

    new_state = {
        "status": previous_status,
        "changed_at": previous_changed_at.isoformat(),
        "pending_status": current_status,
        "pending_count": current_pending_count,
        "pending_since": current_pending_since,
    }
    return StateComparison(
        changed=False,
        state_updated=True,
        is_first_observation=False,
        current_status=current_status,
        previous_status=previous_status,
        duration_seconds=0,
        new_state=new_state,
    )


def format_ua_message(
    target_name: str,
    is_online: bool,
    duration_seconds: int,
    *,
    now: datetime | None = None,
    timezone_name: str = "Europe/Kyiv",
    include_target_name: bool = False,
) -> str:
    """Build notification text in Ukrainian for Telegram."""
    current_time_utc = _normalize_datetime(now) if now else datetime.now(timezone.utc)
    display_timezone = _get_timezone(timezone_name)
    current_time = current_time_utc.astimezone(display_timezone)
    time_label = current_time.strftime("%H:%M")
    duration_text = _format_duration_ua(duration_seconds)

    lines: list[str]
    if is_online:
        lines = [
            "🟢 <b>Світло з'явилося</b>",
            f"⏰ Час появи: <b>{time_label}</b>",
            f"⏳ Світло було відсутнє <b>{duration_text}</b>",
        ]
    else:
        lines = [
            "🔴 <b>Світло зникло</b>",
            f"⏰ Час зникнення: <b>{time_label}</b>",
            f"⏳ Світло було присутнє <b>{duration_text}</b>",
        ]

    if include_target_name:
        lines.insert(1, f"🏠 Об'єкт: <b>{target_name}</b>")

    return "\n".join(lines)


def load_state(path: str | Path) -> dict[str, SavedState]:
    """Load JSON state file, return empty dict when file is missing or invalid."""
    state_path = Path(path)
    if not state_path.exists():
        return {}

    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(raw, dict):
        return {}

    state: dict[str, SavedState] = {}
    for target_id, item in raw.items():
        if not isinstance(target_id, str):
            continue

        normalized = _normalize_saved_state_entry(item)
        if normalized:
            state[target_id] = normalized

    return state


def save_state(path: str | Path, state: dict[str, SavedState]) -> None:
    """Persist state to JSON atomically."""
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
    temp_path = state_path.with_suffix(f"{state_path.suffix}.tmp")
    temp_path.write_text(payload, encoding="utf-8")
    temp_path.replace(state_path)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_iso_datetime(raw_value: object, *, fallback: datetime) -> datetime:
    if not isinstance(raw_value, str):
        return fallback

    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        return fallback

    return _normalize_datetime(parsed)


def _normalize_saved_state_entry(item: object) -> SavedState | None:
    if not isinstance(item, dict):
        return None

    status = item.get("status")
    changed_at = item.get("changed_at")
    if status not in {"online", "offline"} or not isinstance(changed_at, str):
        return None

    state: SavedState = {"status": status, "changed_at": changed_at}
    pending_status = item.get("pending_status")
    pending_count = item.get("pending_count")
    pending_since = item.get("pending_since")
    if (
        pending_status in {"online", "offline"}
        and isinstance(pending_count, int)
        and pending_count > 0
        and isinstance(pending_since, str)
    ):
        state["pending_status"] = pending_status
        state["pending_count"] = pending_count
        state["pending_since"] = pending_since

    return state


def _has_pending_transition(state: SavedState) -> bool:
    return (
        state.get("pending_status") in {"online", "offline"}
        and isinstance(state.get("pending_count"), int)
        and isinstance(state.get("pending_since"), str)
    )


def _format_duration_ua(total_seconds: int) -> str:
    total_minutes = max(0, int(total_seconds)) // 60
    hours, minutes = divmod(total_minutes, 60)
    if hours:
        return f"{hours} год {minutes} хв"
    return f"{minutes} хв"


def _get_timezone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return timezone.utc
