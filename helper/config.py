"""PANBA user configuration utilities.

This module provides fast and robust helpers to persist user preferences and
credentials into the Windows per-user AppData config directory using a single
JSON file. Sensitive fields (secrets) are protected with Windows DPAPI and
encoded as base64 strings in the config.

Notes
-----
- No changes are made to existing files by importing this module.
- Integration into UI (app.py, views) will require code changes and your
  confirmation before proceeding.
"""

from __future__ import annotations

from base64 import b64decode, b64encode
from pathlib import Path
from typing import Any, Dict, TypedDict, cast
import json
import logging
import os
import sys

from platformdirs import user_config_dir

try:
    # pywin32
    import win32crypt  # type: ignore
except Exception:  # pragma: no cover - platform dependent
    win32crypt = None  # type: ignore


log = logging.getLogger(__name__)


class UIOverrides(TypedDict, total=False):
    """UI-related defaults and flags.

    Attributes
    ----------
    remember_me: bool
        Whether to persist credentials on successful login.
    defaults: dict
        Collection of task defaults (duration, plotting, debug).
    """

    remember_me: bool
    defaults: Dict[str, Any]


class Paths(TypedDict, total=False):
    """Last used directories for dialogs.

    Attributes
    ----------
    last_open_dir: str
        Last directory used for opening files.
    last_export_dir: str
        Last directory used for exports.
    last_import_dir: str
        Last directory used for importing files.
    last_import_file: str
        Last file path selected for import.
    """

    last_open_dir: str
    last_export_dir: str
    last_import_dir: str
    last_import_file: str


class Auth(TypedDict, total=False):
    """Authentication profile (username, tenant, secret).

    Attributes
    ----------
    username: str
        Last used username (non-sensitive).
    tsg_id: str | int
        Tenant/TSG identifier.
    secret_enc: str
        Base64-encoded DPAPI-protected secret.
    """

    username: str
    tsg_id: str | int
    secret_enc: str


class Config(TypedDict, total=False):
    """Top-level configuration shape.

    Attributes
    ----------
    version: str
        Semantic version of the config schema, for future migrations.
    ui: UIOverrides
        UI defaults and remember-me flag.
    paths: Paths
        Last used directories.
    auth: Auth
        Authentication profile.
    """

    version: str
    ui: UIOverrides
    paths: Paths
    auth: Auth


def get_config_path() -> Path:
    """Return absolute path to PANBA config file (does not create the file).

    Uses platformdirs to resolve a per-user config directory on Windows, e.g.::

        %LOCALAPPDATA%\\PANBA\\config.json

    Returns
    -------
    Path
        The path to the JSON configuration file.
    """

    config_dir: str = user_config_dir(appname="PANBA", appauthor="NTTIndonesia")
    path: Path = Path(config_dir).expanduser().absolute()
    # Ensure directory exists quickly; this is idempotent and fast
    path.mkdir(parents=True, exist_ok=True)
    return path / "config.json"


def default_config() -> Config:
    """Return in-memory default configuration.

    Provides sensible defaults to minimize user input on first run.
    """

    return cast(
        Config,
        {
            "version": "1.0.0",
            "ui": {
                "remember_me": True,
                "defaults": {
                    "duration_days": 90,
                    "generate_plots": False,
                    "debug_mode": False,
                },
            },
            "paths": {
                "last_open_dir": str(Path.home()),
                "last_export_dir": str(Path.cwd()),
                "last_import_dir": str(Path.home()),
                "last_import_file": "",
            },
            "auth": {
                "username": "",
                "tsg_id": "",
                # secret_enc intentionally omitted until a value is saved
            },
        },
    )


def _merge_defaults(cfg: Dict[str, Any]) -> Config:
    """Merge missing fields into an existing config dict.

    Parameters
    ----------
    cfg : dict
        Partially populated configuration loaded from disk.

    Returns
    -------
    Config
        A config with all required keys present.
    """

    base: Config = default_config()
    # Shallow merge first-level keys quickly
    for key, value in base.items():
        if key not in cfg:
            cfg[key] = value
    # Merge nested structures (ui.defaults, paths, auth)
    if isinstance(cfg.get("ui"), dict) and isinstance(base.get("ui"), dict):
        ui = cfg["ui"]
        for k, v in base["ui"].items():
            if k not in ui:
                ui[k] = v
        if isinstance(ui.get("defaults"), dict):
            for k, v in base["ui"]["defaults"].items():
                if k not in ui["defaults"]:
                    ui["defaults"][k] = v
    if isinstance(cfg.get("paths"), dict):
        for k, v in base["paths"].items():
            if k not in cfg["paths"]:
                cfg["paths"][k] = v
    if isinstance(cfg.get("auth"), dict):
        for k, v in base["auth"].items():
            if k not in cfg["auth"]:
                cfg["auth"][k] = v
    # Ensure version present
    if not isinstance(cfg.get("version"), str):
        cfg["version"] = base["version"]
    return cast(Config, cfg)


def encrypt_secret(plain: str) -> str:
    """Protect a secret string using Windows DPAPI and return base64 text.

    Fast path: DPAPI via pywin32. Robust path: raise with clear message on
    non-Windows or missing dependency.

    Parameters
    ----------
    plain : str
        The secret to encrypt.

    Returns
    -------
    str
        Base64-encoded DPAPI-protected bytes suitable for JSON storage.

    Raises
    ------
    RuntimeError
        If DPAPI is unavailable (non-Windows or pywin32 missing).
    """

    if sys.platform != "win32" or win32crypt is None:  # pragma: no cover
        raise RuntimeError("DPAPI encryption requires Windows and pywin32 installed")
    if plain == "":
        return ""
    blob = win32crypt.CryptProtectData(plain.encode("utf-8"), None, None, None, None, 0)
    return b64encode(blob).decode("ascii")


def decrypt_secret(cipher_b64: str) -> str:
    """Decrypt a DPAPI-protected base64 string back to plaintext.

    Parameters
    ----------
    cipher_b64 : str
        Base64 string returned by :func:`encrypt_secret`.

    Returns
    -------
    str
        Decrypted secret. Empty string if input is empty.

    Raises
    ------
    RuntimeError
        If DPAPI is unavailable.
    """

    if cipher_b64 == "":
        return ""
    if sys.platform != "win32" or win32crypt is None:  # pragma: no cover
        raise RuntimeError("DPAPI decryption requires Windows and pywin32 installed")
    raw = b64decode(cipher_b64.encode("ascii"))
    res = win32crypt.CryptUnprotectData(raw, None, None, None, 0)
    return cast(bytes, res[1]).decode("utf-8")


def load_config(path: Path | None = None) -> Config:
    """Load configuration from disk or return defaults if missing/corrupt.

    Fast path: if file exists and parses, merge defaults and return.
    Robust path: on errors, log and return defaults without raising.

    Parameters
    ----------
    path : Path | None
        Optional override path; defaults to :func:`get_config_path`.

    Returns
    -------
    Config
        A usable configuration dictionary.
    """

    cfg_path: Path = path or get_config_path()
    if not cfg_path.exists():
        return default_config()
    try:
        with cfg_path.open("r", encoding="utf-8") as fh:
            data: Dict[str, Any] = json.load(fh)
        return _merge_defaults(data)
    except Exception as err:  # pragma: no cover
        log.warning("Failed to load config at %s: %s", cfg_path, err)
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
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
        # On Windows, replace is atomic when same volume
        os.replace(tmp_path, cfg_path)
    except Exception as err:  # pragma: no cover
        log.error("Failed to save config at %s: %s", cfg_path, err)
        # Attempt cleanup of temp file if present
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
