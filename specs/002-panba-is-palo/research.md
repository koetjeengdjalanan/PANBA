# Research: Persisting user preferences and credentials in Windows AppData

Decision: Use a single JSON config file at `%LOCALAPPDATA%/PANBA/config.json` (resolved via platformdirs). Encrypt secrets with Windows DPAPI (user scope) and store as base64 strings. Keep non-sensitive preferences as verbose JSON.

Rationale:
- Simple, robust, no external services; works for PyInstaller/Nuitka builds.
- JSON is developer-editable, diffable, and easy to inspect.
- DPAPI leverages OS-level protection and avoids hardcoding keys; aligns with “editable by dev, not required for end user.”
- Platformdirs ensures correct per-user location without hardcoding paths.

Alternatives considered:
- INI/TOML/YAML: More human-readable but not necessary; JSON is sufficient and already a project dependency.
- Keyring library: Good UX, but adds dependency and requires per-provider backends; DPAPI is built-in on Windows (via pywin32).
- Plaintext .env: Already used for dev; not suitable for storing secrets in production.

File Path:
- Windows: `%LOCALAPPDATA%\\PANBA\\config.json` (preferred) or `%APPDATA%\\PANBA\\config.json` as fallback.

Schema Highlights:
- version (semver string)
- ui.defaults (placeholders, durations, toggles)
- paths.last_export_dir, paths.last_open_dir
- auth: { username, tsg_id, secret_enc (DPAPI) }
- telemetry/logging toggles if needed later

Security Notes:
- Encrypt only sensitive fields (secret). Username and TSG ID can be plain.
- Fail gracefully on decryption errors; do not crash UI.
- Never log secrets; redact in error messages.

Migration Strategy:
- Include `version` in config. On read, if missing/older, upgrade structure with sane defaults and write back.

Testing:
- Unit tests for load/save round-trip (sans DPAPI) and encrypt/decrypt on Windows only (skip if platform != win32).
