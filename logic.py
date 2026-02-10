from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypedDict

Status = Literal["online", "offline"]


class SavedState(TypedDict):
    status: Status
    changed_at: str


@dataclass(slots=True, frozen=True)
class StateComparison:
    changed: bool
    is_first_observation: bool
    current_status: Status
    previous_status: Status | None
    duration_seconds: int
    new_state: SavedState


def check_ip(host: str, port: int, timeout: float = 3.0) -> bool:
    """Return True when TCP connection can be established."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def compare_states(
    previous_state: SavedState | None,
    is_online: bool,
    *,
    now: datetime | None = None,
) -> StateComparison:
    """Compare current status against stored state and prepare next state."""
    current_time = _normalize_datetime(now) if now else datetime.now(timezone.utc)
    current_iso = current_time.isoformat()
    current_status: Status = "online" if is_online else "offline"

    if not previous_state:
        return StateComparison(
            changed=False,
            is_first_observation=True,
            current_status=current_status,
            previous_status=None,
            duration_seconds=0,
            new_state={"status": current_status, "changed_at": current_iso},
        )

    previous_status_raw = previous_state.get("status")
    previous_status: Status | None = (
        previous_status_raw
        if previous_status_raw in {"online", "offline"}
        else None
    )
    if previous_status is None:
        return StateComparison(
            changed=False,
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
    changed = previous_status != current_status
    duration_seconds = (
        max(0, int((current_time - previous_changed_at).total_seconds()))
        if changed
        else 0
    )

    if changed:
        new_state: SavedState = {"status": current_status, "changed_at": current_iso}
    else:
        new_state = {
            "status": current_status,
            "changed_at": previous_changed_at.isoformat(),
        }

    return StateComparison(
        changed=changed,
        is_first_observation=False,
        current_status=current_status,
        previous_status=previous_status,
        duration_seconds=duration_seconds,
        new_state=new_state,
    )


def format_ua_message(
    target_name: str,
    is_online: bool,
    duration_seconds: int,
    *,
    now: datetime | None = None,
) -> str:
    """Build notification text in Ukrainian for Telegram."""
    current_time = _normalize_datetime(now) if now else datetime.now(timezone.utc)
    time_label = current_time.strftime("%H:%M")
    duration_text = _format_duration_ua(duration_seconds)

    if is_online:
        header = f"✅ {target_name}: об'єкт знову в мережі о {time_label}."
        details = f"До цього був недоступний: {duration_text}."
    else:
        header = f"⚠️ {target_name}: об'єкт недоступний з {time_label}."
        details = f"До цього був доступний: {duration_text}."

    return f"{header}\n{details}"


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
        if not isinstance(target_id, str) or not isinstance(item, dict):
            continue

        status = item.get("status")
        changed_at = item.get("changed_at")
        if status in {"online", "offline"} and isinstance(changed_at, str):
            state[target_id] = {"status": status, "changed_at": changed_at}

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


def _format_duration_ua(total_seconds: int) -> str:
    total_minutes = max(0, total_seconds) // 60
    days, remainder = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days} д")
    if days or hours:
        parts.append(f"{hours} год")
    parts.append(f"{minutes} хв")
    return " ".join(parts)
