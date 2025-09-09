# Data Model: PANBA user configuration

Entity: Config
- version: string (e.g., "1.0.0")
- ui:
  - remember_me: bool (default true)
  - defaults:
    - duration_days: int (default 90)
    - generate_plots: bool (default false)
    - debug_mode: bool (default false)
- paths:
  - last_open_dir: string (abs path or empty)
  - last_export_dir: string (abs path or empty)
- auth:
  - username: string
  - tsg_id: string | int
  - secret_enc: string (base64 of DPAPI-encrypted bytes)

Validation rules:
- Paths must exist when used; if not, ignore and fall back to user home.
- duration_days within 1..90; enforce in UI.
- secret_enc must decrypt successfully or be treated as empty secret.

State transitions:
- On successful login: update auth.username, auth.tsg_id, secret_enc (DPAPI), write file.
- On export/save dialogs: update paths.last_export_dir / last_open_dir.
- On toggles change: update ui.defaults and write file.
