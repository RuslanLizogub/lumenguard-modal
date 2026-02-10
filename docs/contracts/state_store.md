# State Store Contract

State is stored as JSON (`state.json`) locally or as one object in `modal.Dict`.

## State JSON schema (minimal)
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

## Per-target fields
- `status`: `"online" | "offline"`
- `changed_at`: ISO-8601 datetime string

## Update rules
- First observation: create target state without Telegram notification.
- No status change: keep previous `changed_at`.
- Status changed + Telegram success: write new state with current timestamp.
- Status changed + Telegram failure: keep old state.
