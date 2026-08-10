"""Unit tests for path_helper location selection and persistence."""

from pathlib import Path

from PySide6.QtCore import QSettings

from app.config.settings import AppConfig
from app.utils.path_helper import get_initial_save_dir, set_last_save_dir


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
