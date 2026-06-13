"""Integration tests across service and downloader contracts without network I/O."""

from pathlib import Path

from app.config.settings import AppConfig
import pytest

from app.core.exceptions import DownloadFailedError, InsufficientStorageError
from app.models.download import DownloadResult
from app.models.platform import Platform
from app.models.video import VideoInfo
from app.services.download_service import DownloadService


class FakeDownloader:
    """Deterministic downloader used as an infrastructure boundary fake."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def get_info(self, url: str, *, playlist: bool = False) -> list[VideoInfo]:
        del playlist
        return [
            VideoInfo(
                id="1",
                url=url,
                platform=Platform.YOUTUBE,
                title="Fixture video",
                estimated_size=100,
            )
        ]

    def download(
        self,
        url: str,
        quality: str,
        *,
        playlist: bool = False,
        progress_callback=None,
    ) -> list[DownloadResult]:
        del quality, playlist, progress_callback
        if "fail" in url:
            raise DownloadFailedError("fixture failure")
        path = self.config.download_path / "fixture.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
        return [DownloadResult(url=url, title="Fixture video", path=path)]


class FakeFactory:
    """Factory fake preserving the production creation interface."""

    def __init__(self, config: AppConfig) -> None:
        self.downloader = FakeDownloader(config)

    def create(self, url: str) -> FakeDownloader:
        del url
        return self.downloader


def test_service_metadata_and_download(config: AppConfig) -> None:
    """The complete service flow performs metadata preflight and download."""
    service = DownloadService(config, factory=FakeFactory(config))
    url = "https://youtube.com/watch?v=ok"
    assert service.get_info(url)[0].title == "Fixture video"
    result = service.download(url, "best")[0]
    assert result.path.read_bytes() == b"fixture"


def test_batch_isolates_failed_urls(config: AppConfig) -> None:
    """One extractor failure does not cancel other batch items."""
    service = DownloadService(config, factory=FakeFactory(config))
    result = service.download_many(
        [
            "https://youtube.com/watch?v=ok",
            "https://youtube.com/watch?v=fail",
        ],
        parallel=True,
    )
    assert result.successful_count == 1
    assert result.failed_count == 1
    assert "fixture failure" in next(iter(result.failures.values()))


def test_sequential_batch_isolates_failures(config: AppConfig) -> None:
    """Sequential mode follows the same per-URL failure contract."""
    service = DownloadService(config, factory=FakeFactory(config))
    result = service.download_many(
        [
            "https://youtube.com/watch?v=ok",
            "https://youtube.com/watch?v=fail",
        ],
        parallel=False,
    )
    assert result.successful_count == 1
    assert result.failed_count == 1


def test_storage_preflight_rejects_large_download(
    config: AppConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Known media larger than available space is rejected before download."""
    service = DownloadService(config, factory=FakeFactory(config))
    monkeypatch.setattr(
        "app.services.download_service.shutil.disk_usage",
        lambda _path: type("Usage", (), {"free": 10})(),
    )
    with pytest.raises(InsufficientStorageError):
        service.download("https://youtube.com/watch?v=large")
