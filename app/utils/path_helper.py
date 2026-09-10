"""Helper functions for location selection and path persistence."""

from __future__ import annotations

import os
import sys
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


def get_app_data_dir() -> Path:
    """Return the application user data directory (e.g. %APPDATA%/VideoDownloader)."""
    app_data = os.getenv("APPDATA")
    if app_data:
        base = Path(app_data) / "VideoDownloader"
    else:
        base = Path.home() / ".videodownloader"
    base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


def is_directory_writable(path: Path) -> bool:
    """Check whether files can be written to the given directory."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / f".write_test_{os.getpid()}.tmp"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def get_history_file_path(config: AppConfig | None = None) -> Path:
    """Return a safe writable path for the history.json storage."""
    # 1. If configured download folder exists and is writable, check for history.json there
    if config and config.download_path:
        candidate_dir = config.download_path.expanduser().resolve()
        if is_directory_writable(candidate_dir):
            return candidate_dir / "history.json"

    # 2. Check local relative "downloads" folder if writable
    local_dir = Path("downloads").resolve()
    if is_directory_writable(local_dir):
        return local_dir / "history.json"

    # 3. Fallback to user AppData directory
    return get_app_data_dir() / "history.json"


def get_safe_log_dir(configured: Path | None = None) -> Path:
    """Ensure a writable log directory is returned."""
    if configured:
        target = configured.resolve()
        if is_directory_writable(target):
            return target

    local_logs = Path("logs").resolve()
    if is_directory_writable(local_logs):
        return local_logs

    fallback = get_app_data_dir() / "logs"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback.resolve()


def get_asset_path(filename: str) -> Path:
    """Resolve asset paths across development, frozen exe, and installed folders."""
    # 1. PyInstaller single-file temporary directory
    if hasattr(sys, "_MEIPASS"):
        cand = Path(sys._MEIPASS) / "assets" / filename
        if cand.exists():
            return cand

    # 2. Executable folder (e.g. VideoDownloader_Folder/_internal/assets or assets)
    exe_dir = Path(sys.executable).parent
    for sub in ("_internal/assets", "assets"):
        cand = exe_dir / sub / filename
        if cand.exists():
            return cand

    # 3. Source repository directory
    src_cand = Path(__file__).resolve().parent.parent.parent / "assets" / filename
    if src_cand.exists():
        return src_cand

    # 4. Fallback relative
    return (Path("assets") / filename).resolve()

