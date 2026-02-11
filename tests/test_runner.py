from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lumenguard.config import RuntimeConfig
from lumenguard.runner import run_cycle


def _config() -> RuntimeConfig:
    return RuntimeConfig.model_validate(
        {
            "telegram_bot_token": "123456789:AAExampleToken",
            "monitor_config": [
                {
                    "id": "home",
                    "name": "Квартира",
                    "host": "1.2.3.4",
                    "port": 443,
                    "chat_id": "-100123456789",
                }
            ],
            "check_interval_seconds": 300,
            "check_timeout_seconds": 2.0,
            "state_path": "state.json",
            "timezone_name": "Europe/Kyiv",
        }
    )


def test_run_cycle_first_observation_saves_state_without_notification(monkeypatch) -> None:
    config = _config()
    now = datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc)

    sent = {"called": False}

    monkeypatch.setattr("lumenguard.runner.check_ip", lambda *args, **kwargs: True)

    def fake_send(*args, **kwargs):
        sent["called"] = True
        return True

    monkeypatch.setattr("lumenguard.runner.send_telegram_message", fake_send)

    state, has_state_update = run_cycle(config, {}, now=now)

    assert has_state_update is True
    assert sent["called"] is False
    assert state["home"]["status"] == "online"
    assert state["home"]["changed_at"] == now.isoformat()


def test_run_cycle_updates_state_when_status_changed_and_sent(monkeypatch) -> None:
    config = _config()
    now = datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc)
    previous_state = {
        "home": {
            "status": "online",
            "changed_at": (now - timedelta(minutes=8)).isoformat(),
        }
    }

    monkeypatch.setattr("lumenguard.runner.check_ip", lambda *args, **kwargs: False)
    monkeypatch.setattr("lumenguard.runner.send_telegram_message", lambda *args, **kwargs: True)

    state, has_state_update = run_cycle(config, previous_state, now=now)

    assert has_state_update is True
    assert state["home"]["status"] == "offline"
    assert state["home"]["changed_at"] == now.isoformat()


def test_run_cycle_does_not_update_state_when_telegram_fails(monkeypatch) -> None:
    config = _config()
    now = datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc)
    previous_changed_at = (now - timedelta(minutes=5)).isoformat()
    previous_state = {
        "home": {
            "status": "online",
            "changed_at": previous_changed_at,
        }
    }

    monkeypatch.setattr("lumenguard.runner.check_ip", lambda *args, **kwargs: False)
    monkeypatch.setattr("lumenguard.runner.send_telegram_message", lambda *args, **kwargs: False)

    state, has_state_update = run_cycle(config, previous_state, now=now)

    assert has_state_update is False
    assert state["home"]["status"] == "online"
    assert state["home"]["changed_at"] == previous_changed_at


def test_run_cycle_no_change_keeps_state_and_skips_notification(monkeypatch) -> None:
    config = _config()
    now = datetime(2026, 2, 11, 10, 0, tzinfo=timezone.utc)
    previous_state = {
        "home": {
            "status": "offline",
            "changed_at": (now - timedelta(minutes=3)).isoformat(),
        }
    }

    sent = {"count": 0}
    monkeypatch.setattr("lumenguard.runner.check_ip", lambda *args, **kwargs: False)

    def fake_send(*args, **kwargs):
        sent["count"] += 1
        return True

    monkeypatch.setattr("lumenguard.runner.send_telegram_message", fake_send)

    state, has_state_update = run_cycle(config, previous_state, now=now)

    assert has_state_update is False
    assert sent["count"] == 0
    assert state == previous_state
