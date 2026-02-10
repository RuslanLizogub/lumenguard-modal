# Backend <-> Telegram Contract

## 1) Outgoing Request (Backend -> Telegram)
Backend sends `POST` to Telegram Bot API:
`https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage`

### Request JSON
```json
{
  "chat_id": "-100123456789",
  "text": "⚠️ Квартира: об'єкт недоступний з 19:30.\nДо цього був доступний: 2 год 15 хв."
}
```

### Required fields
- `chat_id`: string (chat/channel id)
- `text`: string (UA notification text)

## 2) Incoming Response (Telegram -> Backend)

### Success JSON (minimal)
```json
{
  "ok": true,
  "result": {
    "message_id": 321,
    "chat": { "id": -100123456789 },
    "date": 1760000000,
    "text": "..."
  }
}
```

### Error JSON (minimal)
```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: chat not found"
}
```

## 3) Backend Rule
- If Telegram request fails (HTTP/network/API), backend does **not** persist changed status for this target in the current cycle.
