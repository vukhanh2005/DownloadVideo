"""Tests for YAML configuration loading."""

from pathlib import Path

import pytest

from app.config.settings import load_config
from app.core.exceptions import ConfigurationError
from app.models.quality import Quality


def test_load_config_and_create_directories(tmp_path: Path) -> None:
    """Configured values are validated and runtime folders are prepared."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "download_path: media\nmax_threads: 5\ndefault_quality: 720p\n"
        "log_path: runtime/app.log\n",
        encoding="utf-8",
    )
    config = load_config(config_file)
    assert config.download_path == Path("media")
    assert config.max_threads == 5
    assert config.default_quality is Quality.P720
    assert config.download_path.is_dir()
    assert config.log_path.parent.is_dir()


def test_missing_config_uses_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing optional config file falls back to defaults."""
    monkeypatch.chdir(tmp_path)
    config = load_config("missing.yaml")
    assert config.default_quality is Quality.BEST
    assert config.download_path.is_dir()


def test_invalid_config_raises_domain_error(tmp_path: Path) -> None:
    """Invalid YAML shape is reported as a configuration error."""
    path = tmp_path / "config.yaml"
    path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(path)


def test_ffmpeg_path_is_loaded(tmp_path: Path) -> None:
    """An optional FFmpeg override is normalized as a Path."""
    path = tmp_path / "config.yaml"
    path.write_text("ffmpeg_path: tools/ffmpeg.exe\n", encoding="utf-8")
    assert load_config(path).ffmpeg_path == Path("tools/ffmpeg.exe")
