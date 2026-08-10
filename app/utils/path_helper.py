"""Helper functions for location selection and path persistence."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

from app.config.settings import AppConfig


def get_initial_save_dir(config: AppConfig | None = None) -> Path:
    """Get the initial directory for file/folder pickers.

    Returns the last saved directory if it exists on disk and is a directory.
    If the path does not exist, falls back to the configured download path
    or the default user Downloads directory.
    """
    settings = QSettings("MultiPlatformVideoDownloader", "VideoDownloader")
    last_dir_str = settings.value("last_save_dir", None)

    if last_dir_str:
        last_dir = Path(str(last_dir_str))
        if last_dir.exists() and last_dir.is_dir():
            return last_dir.resolve()

    # Fallback to configured download directory
    if config and config.download_path:
        default_dir = config.download_path.expanduser().resolve()
        if default_dir.exists() and default_dir.is_dir():
            return default_dir

    downloads_dir = Path.home() / "Downloads"
    if downloads_dir.exists() and downloads_dir.is_dir():
        return downloads_dir.resolve()

    return Path.home().resolve()


def set_last_save_dir(path: Path | str) -> None:
    """Persist the last selected save location directory."""
    if not path:
        return
    p = Path(path)
    directory = p if p.is_dir() else p.parent
    if directory.exists() and directory.is_dir():
        settings = QSettings("MultiPlatformVideoDownloader", "VideoDownloader")
        settings.setValue("last_save_dir", str(directory.resolve()))
