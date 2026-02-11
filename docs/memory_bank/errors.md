# Errors

## Інциденти та виправлення

1. `ModuleNotFoundError: No module named 'logic'` у Modal runtime.
- Причина: у контейнер потрапляв `main.py`, але `logic.py` не додавався як Python source.
- Виправлення: виконано перехід на `src`-структуру і додано `image.add_local_dir("src", "/root/src", copy=True)` у `modal_app.py`.

2. Неправильний час у Telegram (UTC замість локального).
- Причина: форматування часу без конвертації у локальну часову зону.
- Виправлення: додано `TIMEZONE` і конвертацію через `zoneinfo`.

3. Жирний текст не відображався в Telegram.
- Причина: відсутній `parse_mode`.
- Виправлення: додано `"parse_mode": "HTML"`; шаблони переведені на `<b>...</b>`.

4. Очікування повідомлення на першому запуску.
- Причина: це нормальна поведінка (`is_first_observation`), а не помилка.
- Виправлення: документовано в README та memory bank.

5. `FileNotFoundError: /root/pyproject.toml` у `modal run`.
- Причина: `modal_app.py` читав `pyproject.toml` під час імпорту всередині контейнера, але файл не монтувався в runtime.
- Виправлення: додано безпечний fallback до вбудованого списку залежностей, якщо `pyproject.toml` недоступний.
