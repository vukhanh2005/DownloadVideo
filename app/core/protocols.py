"""Protocols shared by services and downloader adapters."""

from collections.abc import Callable
from typing import Protocol

from app.models.download import DownloadProgress, DownloadResult
from app.models.video import VideoInfo

ProgressCallback = Callable[[DownloadProgress], None]


class Downloader(Protocol):
    """Contract implemented by every platform downloader."""

    def get_info(self, url: str, *, playlist: bool = False) -> list[VideoInfo]:
        """Return metadata for one video or all playlist entries."""

    def download(
        self,
        url: str,
        quality: str,
        *,
        download_type: str = "video+audio",
        audio_format: str = "mp3",
        playlist: bool = False,
        progress_callback: ProgressCallback | None = None,
    ) -> list[DownloadResult]:
        """Download a video or playlist and return produced files."""
