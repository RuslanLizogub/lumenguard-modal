# Контракт Runtime Config

Backend читає конфігурацію зі змінних середовища.

## Обов'язкові змінні
- `TELEGRAM_BOT_TOKEN`: токен Telegram-бота
- `MONITOR_CONFIG`: JSON-масив цілей моніторингу

## Опційні змінні
- `CHECK_INTERVAL_SECONDS` (default: `300`, мінімум: `60`)
- `CHECK_TIMEOUT_SECONDS` (default: `3`)
- `STATE_PATH` (default: `state.json`)
- `TIMEZONE` (default: `Europe/Kyiv`)

## Схема `MONITOR_CONFIG` (мінімум)
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

## Обмеження полів
- `id`: непорожній рядок (унікальний ключ стану)
- `name`: непорожній рядок
- `host`: непорожній рядок
- `port`: ціле число `1..65535`
- `chat_id`: непорожній рядок
