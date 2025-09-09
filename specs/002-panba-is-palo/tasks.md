# Tasks: PANBA UX baseline — 4-click tasks and defaulted inputs

**Input**: Design documents from `C:\\Users\\marti\\Documents\\playground\\PANBA\\specs\\002-panba-is-palo\\`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Phase 3.1: Setup
- [ ] T001 Ensure dependency available: platformdirs, pywin32 (DPAPI). If missing, add to `C:\\Users\\marti\\Documents\\playground\\PANBA\\requirements.txt` and install in the venv.
- [ ] T002 [P] Create `helper/config.py` module skeleton with typed signatures and docstrings only (no logic yet):
  - get_config_path() -> Path
  - load_config() -> dict[str, any]
  - save_config(cfg: dict[str, any]) -> None
  - encrypt_secret(plain: str) -> str
  - decrypt_secret(cipher_b64: str) -> str

## Phase 3.2: Tests First (TDD)
- [ ] T003 [P] Contract test for config schema: validate a sample config against `C:\\Users\\marti\\Documents\\playground\\PANBA\\specs\\002-panba-is-palo\\contracts\\config-schema.json` in `tests/contract/test_config_schema.py`.
- [ ] T004 [P] Unit tests for encrypt/decrypt using DPAPI in `tests/unit/test_config_crypto.py` (skip on non-Windows).
- [ ] T005 [P] Unit tests for load/save round-trip in `tests/unit/test_config_io.py` using a temp directory; ensure version field defaulting and path creation.
- [ ] T006 Integration test scenario: pre-fill credentials and defaults in UI from config in `tests/integration/test_ui_prefill.py` (smoke-level, import config and simulate values; no GUI automation).

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T007 [P] Implement `helper/config.py::get_config_path` using platformdirs.user_config_dir('PANBA','NTTIndonesia'); ensure directory creation.
- [ ] T008 [P] Implement `helper/config.py::encrypt_secret` and `decrypt_secret` using Windows DPAPI via pywin32; base64 encode/decode; handle errors.
- [ ] T009 Implement `helper/config.py::load_config`:
  - Read JSON if exists; else return in-memory defaults per data-model.md.
  - Validate basic shape against `contracts/config-schema.json` (optional lenient check); add missing defaults; set version.
- [ ] T010 Implement `helper/config.py::save_config`:
  - Write JSON atomically; ensure directories; do not log secrets.

## Phase 3.4: Integration
- [ ] T011 Wire config load into `C:\\Users\\marti\\Documents\\playground\\PANBA\\app.py`: on startup, call load_config() and pass values to views (without functional change yet). WARNING: This modifies existing file; requires confirmation.
- [ ] T012 In `C:\\Users\\marti\\Documents\\playground\\PANBA\\view\\accountncredentials.py`, pre-fill username/tsg_id/secret from config (decrypting secret). Add a "Remember me" checkbox default ON, saving back on successful login. WARNING: This modifies existing file; requires confirmation.
- [ ] T013 In `C:\\Users\\marti\\Documents\\playground\\PANBA\\helper\\filehandler.py`, update to remember last open/export directories via config on picker success. WARNING: This modifies existing file; requires confirmation.

## Phase 3.5: Polish
- [ ] T014 [P] Add minimal logging to config operations; redact secrets.
- [ ] T015 [P] Update `quickstart.md` with any integration nuances discovered.
- [ ] T016 Manual test notes: Verify four-click flows benefit from defaults; verify first-run and corrupted-config recovery.

## Dependencies
- Setup (T001-T002) before Tests (T003-T006)
- Tests (T003-T006) before Implementation (T007-T010)
- Config module (T007-T010) before Integration (T011-T013)

## Parallel Example
```
# Run in parallel:
Task: "Contract test for config schema in tests/contract/test_config_schema.py"
Task: "Unit tests for encrypt/decrypt in tests/unit/test_config_crypto.py"
Task: "Unit tests for load/save round-trip in tests/unit/test_config_io.py"
```

## Notes
- [P] tasks are independent files; keep them parallelizable
- Integration tasks marked WARNING require your confirmation before changes are applied to existing files