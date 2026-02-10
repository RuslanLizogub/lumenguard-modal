# Контракт State Store

Стан зберігається як JSON (`state.json`) локально або як один об'єкт у `modal.Dict` (`lumenguard-state`).

## Схема стану (мінімум)
```json
{
  "home_kyiv": {
    "status": "online",
    "changed_at": "2026-02-10T19:15:00+00:00"
  },
  "dacha_lviv": {
    "status": "offline",
    "changed_at": "2026-02-10T18:20:00+00:00"
  }
}
```

## Поля по цілі
- `status`: `"online" | "offline"`
- `changed_at`: рядок дати/часу у форматі ISO-8601

## Правила оновлення
- Перше спостереження: створити стан без повідомлення в Telegram.
- Без зміни статусу: зберегти попередній `changed_at`.
- Статус змінився + Telegram success: записати новий стан з поточним часом.
- Статус змінився + Telegram failure: залишити попередній стан.
