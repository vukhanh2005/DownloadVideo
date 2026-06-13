"""Application use cases for metadata, downloads, playlists, and batches."""

from __future__ import annotations

import logging
import shutil
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config.settings import AppConfig
from app.core.exceptions import InsufficientStorageError, VideoDownloaderError
from app.core.protocols import ProgressCallback
from app.downloaders.factory import DownloaderFactory
from app.models.download import BatchResult, DownloadResult
from app.models.quality import Quality
from app.models.video import VideoInfo

LOGGER = logging.getLogger(__name__)


class DownloadService:
    """Coordinate downloader adapters without exposing infrastructure details."""

    def __init__(
        self, config: AppConfig, factory: DownloaderFactory | None = None
    ) -> None:
        self.config = config
        self.config.prepare_directories()
        self.factory = factory or DownloaderFactory(config)

    def get_info(self, url: str, *, playlist: bool = False) -> list[VideoInfo]:
        """Return normalized metadata for a URL."""
        return self.factory.create(url).get_info(url, playlist=playlist)

    def download(
        self,
        url: str,
        quality: Quality | str | None = None,
        *,
        playlist: bool = False,
        progress_callback: ProgressCallback | None = None,
    ) -> list[DownloadResult]:
        """Download one URL after a best-effort disk-space preflight."""
        selected = Quality(quality or self.config.default_quality)
        metadata = self.get_info(url, playlist=playlist)
        self._check_storage(metadata)
        return self.factory.create(url).download(
            url,
            selected.value,
            playlist=playlist,
            progress_callback=progress_callback,
        )

    def download_many(
        self,
        urls: Iterable[str],
        quality: Quality | str | None = None,
        *,
        parallel: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> BatchResult:
        """Download multiple URLs and retain independent failure details."""
        clean_urls = tuple(dict.fromkeys(url.strip() for url in urls if url.strip()))
        if not parallel or self.config.max_threads == 1:
            return self._download_sequential(clean_urls, quality, progress_callback)

        completed: list[DownloadResult] = []
        failures: dict[str, str] = {}
        with ThreadPoolExecutor(
            max_workers=self.config.max_threads, thread_name_prefix="download"
        ) as executor:
            futures = {
                executor.submit(
                    self.download,
                    url,
                    quality,
                    progress_callback=progress_callback,
                ): url
                for url in clean_urls
            }
            for future in as_completed(futures):
                url = futures[future]
                try:
                    completed.extend(future.result())
                except VideoDownloaderError as exc:
                    LOGGER.error("batch item failed | url=%s | error=%s", url, exc)
                    failures[url] = str(exc)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    # Third-party extractors can raise errors outside our hierarchy.
                    LOGGER.exception("unexpected batch failure | url=%s", url)
                    failures[url] = f"Unexpected error: {exc}"
        return BatchResult(completed=tuple(completed), failures=failures)

    def _download_sequential(
        self,
        urls: tuple[str, ...],
        quality: Quality | str | None,
        progress_callback: ProgressCallback | None,
    ) -> BatchResult:
        completed: list[DownloadResult] = []
        failures: dict[str, str] = {}
        for url in urls:
            try:
                completed.extend(
                    self.download(url, quality, progress_callback=progress_callback)
                )
            except VideoDownloaderError as exc:
                LOGGER.error("batch item failed | url=%s | error=%s", url, exc)
                failures[url] = str(exc)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                # Third-party extractors can raise errors outside our hierarchy.
                LOGGER.exception("unexpected batch failure | url=%s", url)
                failures[url] = f"Unexpected error: {exc}"
        return BatchResult(completed=tuple(completed), failures=failures)

    def _check_storage(self, metadata: list[VideoInfo]) -> None:
        known_size = sum(item.estimated_size or 0 for item in metadata)
        if known_size == 0:
            return
        free = shutil.disk_usage(self.config.download_path).free
        required = int(known_size * 1.2)
        if free < required:
            raise InsufficientStorageError(
                f"Insufficient disk space: need about {required} bytes, "
                f"but only {free} bytes are free."
            )
