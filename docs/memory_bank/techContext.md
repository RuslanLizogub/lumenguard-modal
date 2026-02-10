# Tech Context

## Runtime
- Python: 3.12 у Modal image (локально може бути 3.11/3.12).
- Основні бібліотеки: `httpx`, `python-dotenv`, `pydantic`, `modal`.

## Вхідні налаштування
- `TELEGRAM_BOT_TOKEN`
- `MONITOR_CONFIG`
- `CHECK_INTERVAL_SECONDS` (>=60)
- `CHECK_TIMEOUT_SECONDS`
- `STATE_PATH`
- `TIMEZONE`

## Збереження стану
- Локально: JSON-файл (`state.json`).
- У Modal: `modal.Dict` з ім'ям `lumenguard-state`.

## Планувальник
- `modal.Cron("*/5 * * * *")` для запуску кожні 5 хвилин.

## Команди обслуговування
- Тести: `pytest -q`
- Деплой: `modal deploy main.py`
- Ручний запуск: `modal run main.py::monitor_with_modal`
- Оновлення секретів: `modal secret create lumenguard-config --from-dotenv .env --force`
