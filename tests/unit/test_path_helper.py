"""Unit tests for path_helper location selection and persistence."""

from pathlib import Path

from PySide6.QtCore import QSettings

from app.config.settings import AppConfig
from app.utils.path_helper import (
    get_app_data_dir,
    get_asset_path,
    get_history_file_path,
    get_initial_save_dir,
    get_safe_log_dir,
    is_directory_writable,
    set_last_save_dir,
)



def test_set_last_save_dir_with_directory(tmp_path: Path) -> None:
    """Test persisting an existing directory path."""
    test_dir = tmp_path / "my_custom_folder"
    test_dir.mkdir()

    set_last_save_dir(test_dir)

    settings = QSettings("MultiPlatformVideoDownloader", "VideoDownloader")
    saved = settings.value("last_save_dir", None)
    assert saved is not None
    assert Path(saved).resolve() == test_dir.resolve()


def test_set_last_save_dir_with_file_path(tmp_path: Path) -> None:
    """Test persisting a file path extracts the parent folder."""
    test_dir = tmp_path / "videos"
    test_dir.mkdir()
    file_path = test_dir / "sample.mp4"

    set_last_save_dir(file_path)

    settings = QSettings("MultiPlatformVideoDownloader", "VideoDownloader")
    saved = settings.value("last_save_dir", None)
    assert saved is not None
    assert Path(saved).resolve() == test_dir.resolve()


def test_get_initial_save_dir_returns_saved_if_exists(tmp_path: Path) -> None:
    """Test get_initial_save_dir uses last saved directory if it exists."""
    test_dir = tmp_path / "saved_location"
    test_dir.mkdir()

    set_last_save_dir(test_dir)
    result = get_initial_save_dir()
    assert result == test_dir.resolve()


def test_get_initial_save_dir_fallback_if_saved_does_not_exist(tmp_path: Path) -> None:
    """Test get_initial_save_dir falls back to config download_path if saved dir is missing."""
    non_existent = tmp_path / "deleted_folder"
    # Write invalid path to QSettings directly
    settings = QSettings("MultiPlatformVideoDownloader", "VideoDownloader")
    settings.setValue("last_save_dir", str(non_existent))

    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    config = AppConfig(download_path=download_dir)
    result = get_initial_save_dir(config)

    assert result == download_dir.resolve()


def test_get_initial_save_dir_fallback_to_downloads_or_home(tmp_path: Path) -> None:
    """Test get_initial_save_dir falls back to home or downloads if config path missing."""
    settings = QSettings("MultiPlatformVideoDownloader", "VideoDownloader")
    settings.setValue("last_save_dir", str(tmp_path / "non_existent_folder"))

    config = AppConfig(download_path=tmp_path / "missing_downloads")
    result = get_initial_save_dir(config)

    assert result.exists()


def test_get_app_data_dir() -> None:
    """Test get_app_data_dir returns an existing directory."""
    app_data = get_app_data_dir()
    assert app_data.exists()
    assert app_data.is_dir()


def test_is_directory_writable(tmp_path: Path) -> None:
    """Test is_directory_writable detects writable directories."""
    assert is_directory_writable(tmp_path) is True


def test_get_history_file_path_with_config(tmp_path: Path) -> None:
    """Test get_history_file_path with a writable configured download directory."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    config = AppConfig(download_path=download_dir)
    history_path = get_history_file_path(config)
    assert history_path.parent.resolve() == download_dir.resolve()
    assert history_path.name == "history.json"


def test_get_history_file_path_without_config() -> None:
    """Test get_history_file_path fallback without config."""
    history_path = get_history_file_path(None)
    assert history_path.name == "history.json"
    assert history_path.parent.exists()


def test_get_safe_log_dir(tmp_path: Path) -> None:
    """Test get_safe_log_dir returns writable directory."""
    log_dir = tmp_path / "custom_logs"
    safe = get_safe_log_dir(log_dir)
    assert safe.resolve() == log_dir.resolve()

    safe_default = get_safe_log_dir(None)
    assert safe_default.exists()


def test_get_asset_path() -> None:
    """Test get_asset_path resolves icon asset correctly."""
    icon_path = get_asset_path("icon.png")
    assert icon_path.name == "icon.png"

