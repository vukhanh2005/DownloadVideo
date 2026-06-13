"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from app.config.settings import AppConfig


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    """Return an isolated application configuration."""
    return AppConfig(
        download_path=tmp_path / "downloads",
        log_path=tmp_path / "logs" / "app.log",
    )
