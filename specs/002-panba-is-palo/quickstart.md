# Quickstart: User preferences and credentials

1) Location
- Config lives at: `%LOCALAPPDATA%/PANBA/config.json`
- Created on first successful save; directories auto-created

2) Structure (excerpt)
```json
{
  "version": "1.0.0",
  "ui": {"remember_me": true, "defaults": {"duration_days": 90, "generate_plots": false, "debug_mode": false}},
  "paths": {"last_open_dir": "C:/Users/<you>", "last_export_dir": "C:/Users/<you>/Documents"},
  "auth": {"username": "user@example.com", "tsg_id": 123456, "secret_enc": "<base64-dpapi>"}
}
```

3) Lifecycle
- App start: load config; if missing, use defaults in memory
- Login success: save username, tsg_id, secret_enc (DPAPI)
- File pickers: remember last directories
- Toggles: update defaults on change

4) Safety
- Secret is DPAPI-encrypted and only decryptable by the same user profile on the same machine.
- If decryption fails, show a non-blocking warning and treat secret as empty.
