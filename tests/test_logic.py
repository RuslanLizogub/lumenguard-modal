from __future__ import annotations

import socket
from datetime import datetime, timedelta, timezone

from lumenguard.logic import check_ip, compare_states, format_ua_message, load_state, save_state


class _DummySocket:
    def __enter__(self) -> "_DummySocket":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_check_ip_returns_true_when_connection_is_available(monkeypatch) -> None:
    def fake_create_connection(address, timeout):
        assert address == ("1.2.3.4", 443)
        assert timeout == 1.5
        return _DummySocket()

    monkeypatch.setattr(socket, "create_connection", fake_create_connection)

    assert check_ip("1.2.3.4", 443, timeout=1.5) is True


def test_check_ip_returns_false_when_connection_fails(monkeypatch) -> None:
    def fake_create_connection(address, timeout):
        raise OSError("network error")

    monkeypatch.setattr(socket, "create_connection", fake_create_connection)

    assert check_ip("8.8.8.8", 53, timeout=1.0) is False


def test_compare_states_marks_first_observation() -> None:
    now = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)

    result = compare_states(None, is_online=True, now=now)

    assert result.is_first_observation is True
    assert result.changed is False
    assert result.state_updated is True
    assert result.current_status == "online"
    assert result.new_state == {"status": "online", "changed_at": now.isoformat()}


def test_compare_states_detects_status_change_and_duration() -> None:
    now = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    previous = {
        "status": "offline",
        "changed_at": (now - timedelta(minutes=15)).isoformat(),
    }

    result = compare_states(previous, is_online=True, now=now)

    assert result.is_first_observation is False
    assert result.changed is True
    assert result.state_updated is True
    assert result.previous_status == "offline"
    assert result.duration_seconds == 900
    assert result.new_state["status"] == "online"
    assert result.new_state["changed_at"] == now.isoformat()


def test_compare_states_keeps_timestamp_when_status_is_same() -> None:
    now = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    earlier = (now - timedelta(hours=2)).isoformat()
    previous = {"status": "online", "changed_at": earlier}

    result = compare_states(previous, is_online=True, now=now)

    assert result.changed is False
    assert result.state_updated is False
    assert result.duration_seconds == 0
    assert result.new_state == previous


def test_compare_states_requires_two_cycles_to_confirm_offline() -> None:
    now = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    previous = {"status": "online", "changed_at": (now - timedelta(hours=1)).isoformat()}

    first = compare_states(
        previous,
        is_online=False,
        now=now,
        offline_confirmation_cycles=2,
    )

    assert first.changed is False
    assert first.state_updated is True
    assert first.new_state["status"] == "online"
    assert first.new_state["pending_status"] == "offline"
    assert first.new_state["pending_count"] == 1

    second = compare_states(
        first.new_state,
        is_online=False,
        now=now + timedelta(minutes=5),
        offline_confirmation_cycles=2,
    )

    assert second.changed is True
    assert second.state_updated is True
    assert second.new_state == {
        "status": "offline",
        "changed_at": (now + timedelta(minutes=5)).isoformat(),
    }


def test_compare_states_requires_two_cycles_to_confirm_online() -> None:
    now = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    previous = {"status": "offline", "changed_at": (now - timedelta(hours=1)).isoformat()}

    first = compare_states(
        previous,
        is_online=True,
        now=now,
        online_confirmation_cycles=2,
    )

    assert first.changed is False
    assert first.state_updated is True
    assert first.new_state["status"] == "offline"
    assert first.new_state["pending_status"] == "online"
    assert first.new_state["pending_count"] == 1

    second = compare_states(
        first.new_state,
        is_online=True,
        now=now + timedelta(minutes=5),
        online_confirmation_cycles=2,
    )

    assert second.changed is True
    assert second.state_updated is True
    assert second.new_state == {
        "status": "online",
        "changed_at": (now + timedelta(minutes=5)).isoformat(),
    }


def test_compare_states_clears_pending_transition_when_target_recovers() -> None:
    now = datetime(2026, 2, 10, 12, 0, tzinfo=timezone.utc)
    previous = {
        "status": "online",
        "changed_at": (now - timedelta(hours=1)).isoformat(),
        "pending_status": "offline",
        "pending_count": 1,
        "pending_since": now.isoformat(),
    }

    result = compare_states(
        previous,
        is_online=True,
        now=now + timedelta(minutes=5),
        offline_confirmation_cycles=2,
    )

    assert result.changed is False
    assert result.state_updated is True
    assert result.new_state == {
        "status": "online",
        "changed_at": (now - timedelta(hours=1)).isoformat(),
    }


def test_format_ua_message_for_online_event() -> None:
    now = datetime(2026, 2, 10, 12, 30, tzinfo=timezone.utc)

    message = format_ua_message(
        target_name="Квартира",
        is_online=True,
        duration_seconds=3660,
        now=now,
        include_target_name=True,
    )

    assert "🟢 <b>Світло з'явилося</b>" in message
    assert "🏠 Об'єкт: <b>Квартира</b>" in message
    assert "⏰ Час появи: <b>14:30</b>" in message
    assert "⏳ Світло було відсутнє <b>1 год 1 хв</b>" in message


def test_format_ua_message_for_offline_event() -> None:
    now = datetime(2026, 2, 10, 12, 30, tzinfo=timezone.utc)

    message = format_ua_message(
        target_name="Дача",
        is_online=False,
        duration_seconds=1800,
        now=now,
        include_target_name=True,
    )

    assert "🔴 <b>Світло зникло</b>" in message
    assert "🏠 Об'єкт: <b>Дача</b>" in message
    assert "⏰ Час зникнення: <b>14:30</b>" in message
    assert "⏳ Світло було присутнє <b>30 хв</b>" in message


def test_format_ua_message_uses_kyiv_timezone_by_default() -> None:
    now_utc = datetime(2026, 2, 10, 19, 4, tzinfo=timezone.utc)

    message = format_ua_message(
        target_name="Локальний тест",
        is_online=True,
        duration_seconds=60,
        now=now_utc,
    )

    assert "⏰ Час появи: <b>21:04</b>" in message


def test_format_ua_message_hides_target_name_by_default() -> None:
    now = datetime(2026, 2, 10, 12, 30, tzinfo=timezone.utc)

    message = format_ua_message(
        target_name="Квартира",
        is_online=True,
        duration_seconds=600,
        now=now,
    )

    assert "🏠 Об'єкт:" not in message


def test_format_ua_message_ignores_seconds_in_duration() -> None:
    now = datetime(2026, 2, 10, 12, 30, tzinfo=timezone.utc)

    message = format_ua_message(
        target_name="Тест",
        is_online=False,
        duration_seconds=9993,
        now=now,
    )

    assert "⏳ Світло було присутнє <b>2 год 46 хв</b>" in message
    assert "33с" not in message


def test_save_and_load_state_roundtrip(tmp_path) -> None:
    state_path = tmp_path / "state.json"
    state = {
        "home": {
            "status": "online",
            "changed_at": "2026-02-10T12:00:00+00:00",
        }
    }

    save_state(state_path, state)
    loaded = load_state(state_path)

    assert loaded == state
