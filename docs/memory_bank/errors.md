# Errors

## Інциденти та виправлення

1. `ModuleNotFoundError: No module named 'logic'` у Modal runtime.
- Причина: у контейнер потрапляв `main.py`, але `logic.py` не додавався як Python source.
- Виправлення: у `main.py` додано `.add_local_python_source("logic", copy=True)` в опис image.

2. Неправильний час у Telegram (UTC замість локального).
- Причина: форматування часу без конвертації у локальну часову зону.
- Виправлення: додано `TIMEZONE` і конвертацію через `zoneinfo`.

3. Жирний текст не відображався в Telegram.
- Причина: відсутній `parse_mode`.
- Виправлення: додано `"parse_mode": "HTML"`; шаблони переведені на `<b>...</b>`.

4. Очікування повідомлення на першому запуску.
- Причина: це нормальна поведінка (`is_first_observation`), а не помилка.
- Виправлення: документовано в README та memory bank.
