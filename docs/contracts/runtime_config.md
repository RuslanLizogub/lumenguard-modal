# Runtime Config Contract

Backend reads configuration from environment variables.

## Required vars
- `TELEGRAM_BOT_TOKEN`: Telegram bot token (string)
- `MONITOR_CONFIG`: JSON array of monitoring targets

## Optional vars
- `CHECK_INTERVAL_SECONDS` (default `300`)
- `CHECK_TIMEOUT_SECONDS` (default `3`)
- `STATE_PATH` (default `state.json`)

## `MONITOR_CONFIG` JSON schema (minimal)
```json
[
  {
    "id": "home_kyiv",
    "name": "Квартира",
    "host": "1.2.3.4",
    "port": 443,
    "chat_id": "-100123456789"
  }
]
```

## Field constraints
- `id`: non-empty string
- `name`: non-empty string
- `host`: non-empty string
- `port`: integer `1..65535`
- `chat_id`: non-empty string
