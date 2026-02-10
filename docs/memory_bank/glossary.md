# Glossary

- Ціль моніторингу: один запис у `MONITOR_CONFIG` (`id`, `name`, `host`, `port`, `chat_id`).
- Статус: результат TCP-перевірки (`online` або `offline`).
- Зміна статусу: перехід `online -> offline` або `offline -> online`.
- Перше спостереження: перший цикл для цілі без попереднього стану; повідомлення не надсилається.
- Тривалість попереднього стану: час між `previous.changed_at` та моментом зміни.
- State store: шар збереження стану (`state.json` локально, `modal.Dict` у хмарі).
- Modal Secret: захищене сховище змінних (`lumenguard-config`).
- TIMEZONE: часовий пояс для часу в тексті повідомлення (default `Europe/Kyiv`).
