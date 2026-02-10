# Контракт Backend <-> Logic Module

Описує взаємодію між `main.py` (оркестратор) і `logic.py` (чиста логіка).

## 1) `check_ip`

### Input
```json
{
  "host": "1.2.3.4",
  "port": 443,
  "timeout": 3.0
}
```

### Output
```json
{
  "is_online": true
}
```

## 2) `compare_states`

### Input
```json
{
  "previous_state": {
    "status": "offline",
    "changed_at": "2026-02-10T19:00:00+00:00"
  },
  "is_online": true,
  "now": "2026-02-10T19:15:00+00:00"
}
```

### Output
```json
{
  "changed": true,
  "is_first_observation": false,
  "current_status": "online",
  "previous_status": "offline",
  "duration_seconds": 900,
  "new_state": {
    "status": "online",
    "changed_at": "2026-02-10T19:15:00+00:00"
  }
}
```

## 3) `format_ua_message`

### Input
```json
{
  "target_name": "Квартира",
  "is_online": true,
  "duration_seconds": 900,
  "now": "2026-02-10T19:15:00+00:00",
  "timezone_name": "Europe/Kyiv"
}
```

### Output
```json
{
  "message_ua": "🟢 <b>Світло з'явилося</b>\n⏰ Час появи: <b>21:15</b>\n⏳ Світло було відсутнє протягом <b>15 хв</b>"
}
```

## 4) Правила
- Повідомлення генерується лише коли `changed == true` і `is_first_observation == false`.
- Тривалість у повідомленні відображається тільки в годинах/хвилинах.
