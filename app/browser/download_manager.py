"""Pauseable browser-media downloads backed by yt-dlp."""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadCancelled, DownloadError

from app.browser.models import (
    BrowserDownloadSnapshot,
    BrowserMedia,
    DownloadState,
)
from app.config.settings import AppConfig
from app.core.exceptions import DownloadFailedError
from app.utils.ffmpeg import resolve_ffmpeg

LOGGER = logging.getLogger("browser")
DownloadListener = Callable[[BrowserDownloadSnapshot], None]


@dataclass(slots=True)
class _Task:
    snapshot: BrowserDownloadSnapshot
    pause_requested: threading.Event = field(default_factory=threading.Event)
    cancel_requested: threading.Event = field(default_factory=threading.Event)
    worker: threading.Thread | None = None


class BrowserDownloadManager:
    """Manage browser media downloads with pause, resume, and cancellation."""

    def __init__(self, config: AppConfig, listener: DownloadListener | None = None):
        self.config = config
        self.listener = listener
        self._tasks: dict[str, _Task] = {}
        self._lock = threading.RLock()

    def start(self, media: BrowserMedia, destination: Path) -> str:
        """Create and start a new media download."""
        task_id = uuid.uuid4().hex
        destination.mkdir(parents=True, exist_ok=True)
        snapshot = BrowserDownloadSnapshot(
            task_id=task_id,
            media=media,
            destination=destination,
            state=DownloadState.QUEUED,
        )
        task = _Task(snapshot=snapshot)
        with self._lock:
            self._tasks[task_id] = task
        LOGGER.info("download start | task=%s | url=%s", task_id, media.url)
        self._launch(task)
        return task_id

    def pause(self, task_id: str) -> None:
        """Request a running task to stop after preserving partial files."""
        task = self._task(task_id)
        if task.snapshot.state is DownloadState.DOWNLOADING:
            task.pause_requested.set()

    def resume(self, task_id: str) -> None:
        """Resume a paused task from yt-dlp's partial file."""
        task = self._task(task_id)
        if task.snapshot.state is not DownloadState.PAUSED:
            return
        task.pause_requested.clear()
        task.cancel_requested.clear()
        self._launch(task)

    def cancel(self, task_id: str) -> None:
        """Cancel a task and remove partial files produced by that task."""
        task = self._task(task_id)
        task.cancel_requested.set()
        if task.snapshot.state in {
            DownloadState.PAUSED,
            DownloadState.QUEUED,
        }:
            self._set_state(task, DownloadState.CANCELLED)
            self._cleanup_partials(task)

    def snapshot(self, task_id: str) -> BrowserDownloadSnapshot:
        """Return the latest immutable task snapshot."""
        return self._task(task_id).snapshot

    def snapshots(self) -> tuple[BrowserDownloadSnapshot, ...]:
        """Return all task snapshots."""
        with self._lock:
            return tuple(task.snapshot for task in self._tasks.values())

    def _launch(self, task: _Task) -> None:
        worker = threading.Thread(
            target=self._run,
            args=(task,),
            daemon=True,
            name=f"browser-download-{task.snapshot.task_id[:8]}",
        )
        task.worker = worker
        self._set_state(task, DownloadState.DOWNLOADING)
        worker.start()

    def _run(self, task: _Task) -> None:
        media = task.snapshot.media
        options: dict[str, Any] = {
            "outtmpl": str(task.snapshot.destination / "%(title).60B [%(id)s].%(ext)s"),
            "continuedl": True,
            "nopart": False,
            "overwrites": False,
            "noplaylist": True,
            "retries": self.config.retries,
            "fragment_retries": self.config.fragment_retries,
            "socket_timeout": self.config.socket_timeout,
            "concurrent_fragment_downloads": self.config.concurrent_fragments,
            "merge_output_format": "mp4",
            "progress_hooks": [lambda data: self._progress(task, data)],
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }
        ffmpeg = resolve_ffmpeg(self.config.ffmpeg_path)
        if ffmpeg:
            options["ffmpeg_location"] = str(ffmpeg)
        headers = {}
        if media.referer:
            headers["Referer"] = media.referer
        if media.user_agent:
            headers["User-Agent"] = media.user_agent
        if media.cookies:
            headers["Cookie"] = media.cookies
        if headers:
            options["http_headers"] = headers

        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(media.url, download=True)
                output = self._output_path(info, downloader)
            self._update(
                task,
                state=DownloadState.COMPLETED,
                percent=100,
                output_path=output,
            )
            LOGGER.info(
                "download complete | task=%s | path=%s", task.snapshot.task_id, output
            )
        except DownloadCancelled:
            if task.cancel_requested.is_set():
                self._set_state(task, DownloadState.CANCELLED)
                self._cleanup_partials(task)
            else:
                self._set_state(task, DownloadState.PAUSED)
        except DownloadError as exc:
            self._update(task, state=DownloadState.FAILED, error=str(exc))
            LOGGER.exception("download failed | task=%s", task.snapshot.task_id)
        except OSError as exc:
            self._update(task, state=DownloadState.FAILED, error=str(exc))
            LOGGER.exception("download failed | task=%s", task.snapshot.task_id)

    def _progress(self, task: _Task, data: dict[str, Any]) -> None:
        if task.pause_requested.is_set() or task.cancel_requested.is_set():
            raise DownloadCancelled("Browser download interrupted")
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = int(data.get("downloaded_bytes") or 0)
        percent = downloaded / total * 100 if total else task.snapshot.percent
        self._update(
            task,
            percent=min(percent, 100),
            downloaded_bytes=downloaded,
            total_bytes=total,
            speed=data.get("speed"),
            eta=data.get("eta"),
        )

    def _update(self, task: _Task, **changes: Any) -> None:
        with self._lock:
            task.snapshot = task.snapshot.model_copy(update=changes)
            snapshot = task.snapshot
        if self.listener:
            self.listener(snapshot)

    def _set_state(self, task: _Task, state: DownloadState) -> None:
        self._update(task, state=state)

    def _task(self, task_id: str) -> _Task:
        with self._lock:
            try:
                return self._tasks[task_id]
            except KeyError as exc:
                raise DownloadFailedError(f"Unknown download task: {task_id}") from exc

    @staticmethod
    def _output_path(
        info: dict[str, Any] | None, downloader: yt_dlp.YoutubeDL
    ) -> Path | None:
        if not info:
            return None
        requested = info.get("requested_downloads") or ()
        for item in requested:
            candidate = item.get("filepath") if item else None
            if candidate and Path(candidate).exists():
                return Path(candidate)
        candidate = info.get("filepath") or info.get("_filename")
        return Path(candidate) if candidate else Path(downloader.prepare_filename(info))

    @staticmethod
    def _cleanup_partials(task: _Task) -> None:
        destination = task.snapshot.destination.resolve()
        for partial in destination.glob("*.part*"):
            if partial.resolve().parent == destination:
                partial.unlink(missing_ok=True)
