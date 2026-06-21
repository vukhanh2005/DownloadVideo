"""Validated YAML configuration loading."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from app.core.exceptions import ConfigurationError
from app.models.quality import Quality


class AppConfig(BaseModel):
    """Runtime settings for metadata extraction and downloads."""

    download_path: Path = Path("downloads")
    max_threads: int = Field(default=3, ge=1, le=16)
    default_quality: Quality = Quality.BEST
    retries: int = Field(default=10, ge=0, le=100)
    fragment_retries: int = Field(default=10, ge=0, le=100)
    socket_timeout: int = Field(default=30, ge=1, le=300)
    concurrent_fragments: int = Field(default=4, ge=1, le=16)
    output_template: str = "%(title).60B [%(id)s].%(ext)s"
    cookies_file: Path | None = None
    ffmpeg_path: Path | None = None
    log_path: Path = Path("logs/app.log")
    browser_log_path: Path = Path("logs/browser.log")

    @field_validator(
        "download_path",
        "log_path",
        "browser_log_path",
        "cookies_file",
        "ffmpeg_path",
        mode="before",
    )
    @classmethod
    def expand_path(cls, value: Any) -> Any:
        """Expand environment-style home markers in configured paths."""
        if value in (None, ""):
            return None
        return Path(value).expanduser()

    def prepare_directories(self) -> None:
        """Create writable runtime directories."""
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.browser_log_path.parent.mkdir(parents=True, exist_ok=True)


def load_config(path: Path | str = "config.yaml") -> AppConfig:
    """Load and validate configuration from YAML.

    Missing configuration files are valid and use documented defaults.
    """
    config_path = Path(path)
    try:
        raw = (
            yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if config_path.exists()
            else {}
        )
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ConfigurationError("config.yaml must contain a YAML mapping")
        config = AppConfig.model_validate(raw)
        config.prepare_directories()
        return config
    except (OSError, yaml.YAMLError, ValueError) as exc:
        if isinstance(exc, ConfigurationError):
            raise
        raise ConfigurationError(f"Cannot load configuration: {exc}") from exc
