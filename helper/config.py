"""PANBA user configuration utilities.

This module provides fast and robust helpers to persist user preferences and
credentials into the Windows per-user AppData config directory using a single
JSON file. Sensitive fields (secrets) are protected with Windows DPAPI and
encoded as base64 strings in the config.

Notes:
-----
- No changes are made to existing files by importing this module.
- Integration into UI (app.py, views) will require code changes and your
    confirmation before proceeding.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from base64 import b64decode, b64encode
from pathlib import Path
from typing import Any, Dict, Iterable, cast

from platformdirs import user_config_dir

from models import Config, Creds, LastOpenPath, UIDefaults

try:
    # pywin32
    import win32crypt  # type: ignore
except Exception:  # pragma: no cover - platform dependent
    win32crypt = None  # type: ignore


log = logging.getLogger(__name__)


def get_config_path() -> Path:
    r"""Return absolute path to PANBA config file (creates parent dir if needed).

    Uses platformdirs to resolve a per-user config directory on Windows, e.g.:
        %LOCALAPPDATA%\\PANBA\\config.json

    Returns:
        Path: Absolute path to the JSON configuration file (file may not yet exist).
    """
    config_dir: str = user_config_dir(appname="PANBA", appauthor="NTTIndonesia")
    path = Path(config_dir).expanduser().absolute()
    path.mkdir(parents=True, exist_ok=True)
    return path / "config.json"


def default_config() -> Config:
    """Return an in-memory default configuration.

    The defaults minimize initial user input while establishing a schema
    foundation for potential future migrations.
    """
    return Config(
        version="1.0.0",
        ui=UIDefaults(remember_me=True, default_theme="dark"),
        paths=LastOpenPath(
            last_open_dir=Path.home(),
            last_export_dir=Path.cwd(),
            last_import_dir=Path.home(),
            last_import_file=None,
            last_import_topology_file=None,
            last_import_segment_db_file=None,
        ),
        auth=Creds(username="", tsg_id="", secret_enc=""),
    )


def _coerce_path_maybe(val: Any) -> Path | None:
    """Return Path if val is a non-empty string, else None.

    We do NOT check existence here; consumers decide how to handle missing paths.
    This preserves user intent (e.g., removable drive that is currently detached).

    Examples:
        >>> _coerce_path_maybe("C:/Users/test")
        Path('C:/Users/test')

        >>> _coerce_path_maybe("")
        None
    """
    if isinstance(val, str) and val.strip():
        try:
            return Path(val)
        except Exception:  # pragma: no cover - extremely rare (bad characters)
            return None
    if isinstance(val, Path):  # already a Path
        return val
    return None


def _assign_paths(base: LastOpenPath, overrides: Dict[str, Any], fields: Iterable[str]) -> None:
    for name in fields:
        if name in overrides:
            coerced = _coerce_path_maybe(overrides.get(name))
            if coerced is not None:
                setattr(base, name, coerced)


def _merge_defaults(cfg: Dict[str, Any]) -> Config:
    """Return a new Config combining defaults with user-provided values.

    This does not mutate the incoming dictionary. Unknown keys are ignored.
    Paths are retained even if they do not (currently) exist on disk.
    """
    base = default_config()

    # Version
    version_val = cfg.get("version")
    if version_val is not None:
        base.version = str(version_val)

    # UI
    ui = cfg.get("ui")
    if isinstance(ui, dict):
        remember = ui.get("remember_me")
        if isinstance(remember, bool):
            base.ui.remember_me = remember
        theme = ui.get("default_theme")
        if isinstance(theme, str) and theme:
            theme_lower = str(theme).lower()
            if theme_lower in ("dark", "light"):
                base.ui.default_theme = theme_lower

    # Paths
    paths = cfg.get("paths")
    if isinstance(paths, dict):
        _assign_paths(
            base.paths,
            paths,
            (
                "last_open_dir",
                "last_export_dir",
                "last_import_dir",
                "last_import_file",
                "last_import_topology_file",
                "last_import_segment_db_file",
            ),
        )

    # Auth
    auth = cfg.get("auth")
    if isinstance(auth, dict):
        if base.auth is None:
            base.auth = Creds(username="", tsg_id="", secret_enc="")
        username = auth.get("username")
        if isinstance(username, str):
            base.auth.username = username
        tsg_id = auth.get("tsg_id")
        if isinstance(tsg_id, (str, int)):
            base.auth.tsg_id = tsg_id
        secret_enc = auth.get("secret_enc")
        if isinstance(secret_enc, str):
            base.auth.secret_enc = secret_enc

    return base


def encrypt_secret(plain: str) -> str:
    """Protect a secret string using Windows DPAPI and return base64 text.

    Fast path: DPAPI via pywin32. Robust path: raise with clear message on
    non-Windows or missing dependency.

    Parameters
    ----------
    plain : str
        The secret to encrypt.

    Returns:
        str: Base64-encoded DPAPI-protected bytes suitable for JSON storage.

    Raises:
    ------
    RuntimeError
        If DPAPI is unavailable (non-Windows or pywin32 missing).
    """
    if sys.platform != "win32" or win32crypt is None:  # pragma: no cover
        raise RuntimeError("DPAPI encryption requires Windows and pywin32 installed")
    if not plain:
        return ""
    # pywin32 returns a tuple; encrypted bytes are at index 1
    protected = win32crypt.CryptProtectData(plain.encode("utf-8"), None, None, None, None, 0)
    encrypted_bytes: bytes | None = None
    # Typical pywin32: (description, encrypted_bytes)
    if isinstance(protected, tuple):
        if len(protected) >= 2 and isinstance(protected[1], (bytes, bytearray)):
            encrypted_bytes = bytes(protected[1])
        else:
            # Search tuple for any bytes-like component
            for part in protected:
                if isinstance(part, (bytes, bytearray)):
                    encrypted_bytes = bytes(part)
                    break
                # Some pywin32 variants may wrap the data in an object with 'buffer' attribute
                if hasattr(part, "buffer"):
                    buf = getattr(part, "buffer")
                    if isinstance(buf, (bytes, bytearray)):
                        encrypted_bytes = bytes(buf)
                        break
    elif isinstance(protected, (bytes, bytearray)):
        encrypted_bytes = bytes(protected)

    if encrypted_bytes is None:
        raise RuntimeError("Unexpected DPAPI return format; unable to extract encrypted bytes")
    return b64encode(encrypted_bytes).decode("ascii")


def decrypt_secret(cipher_b64: str) -> str:
    """Decrypt a DPAPI-protected base64 string back to plaintext.

    Parameters
    ----------
    cipher_b64 : str
        Base64 string returned by :func:`encrypt_secret`.

    Returns:
    -------
        str: Decrypted secret. Empty string if input is empty.

    Raises:
    ------
    RuntimeError
        If DPAPI is unavailable.
    """
    if not cipher_b64:
        return ""
    if sys.platform != "win32" or win32crypt is None:  # pragma: no cover
        raise RuntimeError("DPAPI decryption requires Windows and pywin32 installed")
    raw = b64decode(cipher_b64.encode("ascii"))
    _, decrypted = win32crypt.CryptUnprotectData(raw, None, None, None, 0)
    return cast(bytes, decrypted).decode("utf-8")


def load_config(path: Path | None = None) -> Config:
    """Load configuration from disk or return defaults if missing/corrupt.

    Fast path: if file exists and parses, merge defaults and return.
    Robust path: on errors, log and return defaults without raising.

    Parameters
    ----------
    path : Path | None
        Optional override path; defaults to :func:`get_config_path`.

    Returns:
        Config: A usable configuration dictionary.
    """
    cfg_path: Path = path or get_config_path()
    if not cfg_path.exists():
        return default_config()
    try:
        with cfg_path.open("r", encoding="utf-8") as fh:
            data: Dict[str, Any] = json.load(fh)
        # Future: data = _migrate_if_needed(data)
        return _merge_defaults(data)
    except Exception as err:  # pragma: no cover
        log.warning("Failed to load config at %s (%s): %s", cfg_path, type(err).__name__, err)
        return default_config()


def save_config(cfg: Config, path: Path | None = None) -> None:
    """Persist configuration JSON to disk atomically.

    Writes to a temporary file in the same directory and renames it into place
    to minimize the risk of partial writes.

    Parameters
    ----------
    cfg : Config
        The configuration to persist (secrets must already be encrypted as
        `auth.secret_enc`).
    path : Path | None
        Optional override path; defaults to :func:`get_config_path`.
    """
    cfg_path: Path = path or get_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path = cfg_path.with_suffix(".json.tmp")
    try:
        # pydantic BaseModel -> dict via .model_dump() (pydantic v2) or .dict()
        if hasattr(cfg, "model_dump"):
            model_dict: Dict[str, Any] = cfg.model_dump()  # type: ignore[attr-defined]
        else:  # pydantic v1 fallback
            model_dict = cfg.dict()  # type: ignore[attr-defined]

        # Convert Path objects to strings for JSON stability
        def _normalize(obj: Any) -> Any:
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, dict):
                return {k: _normalize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_normalize(v) for v in obj]
            return obj

        payload = _normalize(model_dict)
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, cfg_path)
    except Exception as err:  # pragma: no cover
        log.error("Failed to save config at %s (%s): %s", cfg_path, type(err).__name__, err)
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:  # pragma: no cover - best effort
            pass


def _migrate_if_needed(data: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - placeholder until versions change
    """Placeholder for future schema migrations.

    Example pattern:
        version = str(data.get("version", "1.0.0"))
        if version < "1.1.0":
            # transform fields
            data["version"] = "1.1.0"
    """
    return data
