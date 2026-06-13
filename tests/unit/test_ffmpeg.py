"""Tests for FFmpeg executable discovery."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.exceptions import ConfigurationError
from app.utils.ffmpeg import resolve_ffmpeg


def test_resolve_configured_ffmpeg_file(tmp_path: Path) -> None:
    """An explicit executable path takes priority over automatic discovery."""
    executable = tmp_path / "ffmpeg.exe"
    executable.write_bytes(b"binary")
    assert resolve_ffmpeg(executable) == executable.resolve()


def test_resolve_configured_ffmpeg_directory(tmp_path: Path) -> None:
    """A configured directory resolves its platform executable."""
    executable = tmp_path / "ffmpeg.exe"
    executable.write_bytes(b"binary")
    assert resolve_ffmpeg(tmp_path) == executable.resolve()


def test_invalid_configured_ffmpeg_raises(tmp_path: Path) -> None:
    """A bad explicit path is reported instead of silently ignored."""
    with pytest.raises(ConfigurationError, match="FFmpeg was not found"):
        resolve_ffmpeg(tmp_path / "missing.exe")


def test_resolve_ffmpeg_from_path(tmp_path: Path) -> None:
    """System PATH is preferred over the bundled wheel."""
    executable = tmp_path / "ffmpeg.exe"
    executable.write_bytes(b"binary")
    with patch("app.utils.ffmpeg.shutil.which", return_value=str(executable)):
        assert resolve_ffmpeg() == executable.resolve()
