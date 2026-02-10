# Backend <-> Logic Module Contract

This contract describes interaction between `main.py` (orchestrator) and `logic.py` (pure logic).

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
  "now": "2026-02-10T19:15:00+00:00"
}
```

### Output
```json
{
  "message_ua": "✅ Квартира: об'єкт знову в мережі о 19:15.\nДо цього був недоступний: 15 хв."
}
```

## 4) Rule
- Message is generated **only** when `changed == true` and `is_first_observation == false`.
