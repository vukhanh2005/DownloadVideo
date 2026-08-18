"""Tests for browser download task lifecycle."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.browser.download_manager import BrowserDownloadManager
from app.browser.models import BrowserMedia, BrowserMediaType, DownloadState
from app.config.settings import AppConfig


def _media() -> BrowserMedia:
    return BrowserMedia(
        url="https://cdn.example/video.mp4",
        media_type=BrowserMediaType.VIDEO,
        name="video.mp4",
    )


def _wait_for_state(
    manager: BrowserDownloadManager, task_id: str, state: DownloadState
) -> None:
    deadline = time.time() + 3
    while time.time() < deadline:
        if manager.snapshot(task_id).state is state:
            return
        time.sleep(0.01)
    raise AssertionError(f"Task did not reach {state}")


def test_download_workflow_completes(config: AppConfig, tmp_path: Path) -> None:
    """A yt-dlp result becomes a completed immutable task snapshot."""
    output = tmp_path / "video.mp4"
    output.write_bytes(b"media")
    ydl = MagicMock()
    ydl.extract_info.return_value = {
        "id": "1",
        "title": "Video",
        "requested_downloads": [{"filepath": str(output)}],
    }
    constructor = MagicMock()
    constructor.return_value.__enter__.return_value = ydl
    constructor.return_value.__exit__.return_value = False
    manager = BrowserDownloadManager(config)
    with patch("app.browser.download_manager.yt_dlp.YoutubeDL", constructor):
        task_id = manager.start(_media(), tmp_path)
        _wait_for_state(manager, task_id, DownloadState.COMPLETED)
    assert manager.snapshot(task_id).output_path == output
    options = constructor.call_args.args[0]
    assert options["continuedl"] is True
    assert options["nopart"] is False


def test_paused_task_can_resume(config: AppConfig, tmp_path: Path) -> None:
    """Pause preserves state and resume starts the same task again."""
    manager = BrowserDownloadManager(config)
    task = MagicMock()
    with patch.object(manager, "_launch") as launch:
        task_id = manager.start(_media(), tmp_path)
        internal = manager._tasks[task_id]  # pylint: disable=protected-access
        internal.snapshot = internal.snapshot.model_copy(
            update={"state": DownloadState.PAUSED}
        )
        manager.resume(task_id)
        launch.assert_called_with(internal)
    del task


def test_cancel_paused_task_removes_partial(config: AppConfig, tmp_path: Path) -> None:
    """Cancelling a paused task removes its partial data."""
    manager = BrowserDownloadManager(config)
    with patch.object(manager, "_launch"):
        task_id = manager.start(_media(), tmp_path)
    internal = manager._tasks[task_id]  # pylint: disable=protected-access
    internal.snapshot = internal.snapshot.model_copy(
        update={"state": DownloadState.PAUSED}
    )
    partial = tmp_path / "video.mp4.part"
    partial.write_bytes(b"partial")
    manager.cancel(task_id)
    assert manager.snapshot(task_id).state is DownloadState.CANCELLED
    assert not partial.exists()


def test_progress_with_float_values(config: AppConfig, tmp_path: Path) -> None:
    """Browser progress hook handles float estimates and formats cleanly."""
    manager = BrowserDownloadManager(config)
    with patch.object(manager, "_launch"):
        task_id = manager.start(_media(), tmp_path)
    task = manager._tasks[task_id]  # pylint: disable=protected-access
    manager._progress(  # pylint: disable=protected-access
        task,
        {
            "status": "downloading",
            "downloaded_bytes": 100.2,
            "total_bytes_estimate": 1000.8,
            "speed": 500.5,
            "eta": 2.0,
        },
    )
    snap = manager.snapshot(task_id)
    assert snap.downloaded_bytes == 100
    assert snap.total_bytes == 1001
    assert snap.speed == 500.5
    assert snap.eta == 2.0
    assert snap.percent > 0
