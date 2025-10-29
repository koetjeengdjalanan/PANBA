"""Tests for helper.config module.

Validates default creation, load/save resilience, merge semantics, and
Windows DPAPI encryption (conditionally executed on supported platforms).
"""

import sys
from pathlib import Path

import pytest

from helper.config import (
    _merge_defaults,
    decrypt_secret,
    default_config,
    encrypt_secret,
    load_config,
    save_config,
)
from models import Config


def test_default_config_structure():
    """Ensure default_config returns expected structure and sane defaults."""
    cfg = default_config()
    assert isinstance(cfg, Config)
    assert cfg.version == "1.0.0"
    assert cfg.ui.default_theme in {"dark", "light", "Dark", "Light"}


def test_load_config_returns_defaults_when_missing(tmp_path: Path, monkeypatch):
    """Loading when file absent should yield defaults."""
    target = tmp_path / "config.json"
    monkeypatch.setattr("helper.config.get_config_path", lambda: target)
    cfg = load_config()
    assert cfg.version == "1.0.0"


def test_save_and_load_round_trip(tmp_path: Path, monkeypatch):
    """Saved config should load back with modifications intact."""
    target = tmp_path / "config.json"
    monkeypatch.setattr("helper.config.get_config_path", lambda: target)
    cfg = default_config()
    cfg.ui.default_theme = "light"
    save_config(cfg)
    loaded = load_config()
    assert loaded.ui.default_theme == "light"


def test_merge_preserves_version():
    """_merge_defaults should not overwrite provided version or fields."""
    data = {"version": "2.3.4", "ui": {"remember_me": False}}
    merged = _merge_defaults(data)
    assert merged.version == "2.3.4"
    assert merged.ui.remember_me is False


def test_corrupt_json_fallback(tmp_path: Path, monkeypatch, caplog):
    """Corrupt JSON should log a warning and fall back to defaults."""
    target = tmp_path / "config.json"
    target.write_text("{not: valid}", encoding="utf-8")
    monkeypatch.setattr("helper.config.get_config_path", lambda: target)
    cfg = load_config()
    assert cfg.version == "1.0.0"
    assert any("Failed to load" in rec.message for rec in caplog.records)


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI only available on Windows")
@pytest.mark.skipif("win32crypt" not in sys.modules, reason="pywin32 not installed")
def test_encrypt_decrypt_round_trip():
    """Secret encryption should round-trip via DPAPI on Windows."""
    secret = "SuperSecret123!"
    enc = encrypt_secret(secret)
    assert enc and isinstance(enc, str)
    dec = decrypt_secret(enc)
    assert dec == secret


def test_merge_paths_without_existence():
    """Non-existent paths should be retained as provided (no existence filtering)."""
    data = {
        "paths": {
            "last_open_dir": str(Path("Z:/nonexistent/path")),
            "last_import_file": str(Path("C:/tmp/file.txt")),
        }
    }
    merged = _merge_defaults(data)
    norm_open = str(merged.paths.last_open_dir).replace("\\", "/")
    norm_file = str(merged.paths.last_import_file).replace("\\", "/")
    assert norm_open.endswith("nonexistent/path")
    assert norm_file.endswith("file.txt")


@pytest.mark.parametrize("value", [None, "", "   "])
def test_encrypt_secret_empty(value):
    """Empty or whitespace secrets should produce empty encrypted output."""
    if sys.platform == "win32":  # ensure dependency if on Windows
        from helper.config import win32crypt  # type: ignore

        if win32crypt is None and value:
            pytest.skip("win32crypt not available")
    assert encrypt_secret((value or "").strip()) == ""
