# Progress

## Completed
- Реалізовано ядро моніторингу: `check_ip`, `compare_states`, `format_ua_message`.
- Додано збереження/читання стану через JSON файл.
- Реалізовано оркестратор циклу в `main.py` з інтервалом 5 хв (за замовчуванням).
- Додано інтеграцію з Telegram API (`httpx`).
- Додано Modal bridge: `modal.Cron("*/5 * * * *")` + `modal.Dict` як state store.
- Оновлено контракти AI-рев'ю в `docs/contracts`.
- Додано та оновлено unit-тести для логіки.

## Next Step
- Підключити реальні секрети/змінні середовища в Modal (`TELEGRAM_BOT_TOKEN`, `MONITOR_CONFIG`).
