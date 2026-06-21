"""Unit tests for yt-dlp normalization and option handling."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadError

from app.config.settings import AppConfig
from app.core.exceptions import PrivateVideoError
from app.downloaders.platforms import YouTubeDownloader
from app.models.download import DownloadProgress


def _ydl_context(instance: MagicMock) -> MagicMock:
    constructor = MagicMock()
    constructor.return_value.__enter__.return_value = instance
    constructor.return_value.__exit__.return_value = False
    return constructor


def test_metadata_is_normalized(config: AppConfig) -> None:
    """Raw extractor dictionaries become stable domain models."""
    ydl = MagicMock()
    ydl.extract_info.return_value = {
        "id": "abc",
        "title": "Example",
        "webpage_url": "https://youtube.com/watch?v=abc",
        "duration": 61,
        "uploader": "Channel",
        "thumbnail": "https://img.example/thumb.jpg",
        "formats": [
            {
                "format_id": "22",
                "ext": "mp4",
                "height": 720,
                "filesize": 1000,
                "vcodec": "h264",
            }
        ],
    }
    with patch("app.downloaders.yt_dlp_downloader.yt_dlp.YoutubeDL", _ydl_context(ydl)):
        info = YouTubeDownloader(config).get_info("https://youtube.com/watch?v=abc")[0]
    assert info.title == "Example"
    assert info.author == "Channel"
    assert info.estimated_size == 1000
    assert info.formats[0].height == 720


def test_download_emits_progress_and_returns_path(
    config: AppConfig, tmp_path: Path
) -> None:
    """Progress hooks and downloaded paths are exposed to application callers."""
    output = tmp_path / "video.mp4"
    output.write_bytes(b"media")
    ydl = MagicMock()
    ydl.extract_info.side_effect = lambda *_args, **_kwargs: {
        "id": "abc",
        "title": "Example",
        "webpage_url": "https://youtube.com/watch?v=abc",
        "requested_downloads": [{"filepath": str(output)}],
    }
    events: list[DownloadProgress] = []
    constructor = _ydl_context(ydl)
    with patch("app.downloaders.yt_dlp_downloader.yt_dlp.YoutubeDL", constructor):
        downloader = YouTubeDownloader(config)
        results = downloader.download(
            "https://youtube.com/watch?v=abc",
            "720p",
            progress_callback=events.append,
        )
        options = constructor.call_args.args[0]
        options["progress_hooks"][0](
            {
                "status": "downloading",
                "downloaded_bytes": 50,
                "total_bytes": 100,
                "speed": 10,
                "eta": 5,
            }
        )
    assert results[0].path == output
    assert events[0].percent == 50
    assert options["continuedl"] is True
    assert "height<=720" in options["format"]
    assert options["format"].startswith(
        "bv*[ext=mp4][vcodec^=avc1][height<=720]+ba[ext=m4a]"
    )


def test_private_video_error_is_classified(config: AppConfig) -> None:
    """Authentication failures become actionable domain errors."""
    ydl = MagicMock()
    ydl.extract_info.side_effect = DownloadError("Private video: login required")
    with (
        patch("app.downloaders.yt_dlp_downloader.yt_dlp.YoutubeDL", _ydl_context(ydl)),
        pytest.raises(PrivateVideoError),
    ):
        YouTubeDownloader(config).get_info("https://youtube.com/watch?v=private")


def test_audio_download_configures_ffmpeg(config: AppConfig, tmp_path: Path) -> None:
    """Audio preset selects best audio and configures MP3 conversion."""
    output = tmp_path / "audio.mp3"
    output.write_bytes(b"audio")
    ydl = MagicMock()
    ydl.extract_info.return_value = {
        "id": "audio",
        "title": "Audio",
        "requested_downloads": [{"filepath": str(output)}],
    }
    constructor = _ydl_context(ydl)
    with patch("app.downloaders.yt_dlp_downloader.yt_dlp.YoutubeDL", constructor):
        YouTubeDownloader(config).download("https://youtu.be/audio", "audio")
    options = constructor.call_args.args[0]
    assert options["format"] == "ba/b"
    assert options["postprocessors"][0]["preferredcodec"] == "mp3"
    assert Path(options["ffmpeg_location"]).is_file()


def test_unsupported_quality_is_rejected(config: AppConfig) -> None:
    """Unknown quality presets fail before constructing yt-dlp."""
    with pytest.raises(Exception, match="Unsupported quality"):
        YouTubeDownloader(config).download("https://youtu.be/abc", "4k")


def test_missing_ffmpeg_error_is_actionable(config: AppConfig) -> None:
    """Raw yt-dlp dependency errors become a stable application message."""
    ydl = MagicMock()
    ydl.extract_info.side_effect = DownloadError("ffmpeg is not installed")
    with (
        patch("app.downloaders.yt_dlp_downloader.yt_dlp.YoutubeDL", _ydl_context(ydl)),
        pytest.raises(Exception, match="FFmpeg is required"),
    ):
        YouTubeDownloader(config).download("https://youtu.be/abc", "best")


def test_best_prefers_windows_compatible_codecs(
    config: AppConfig, tmp_path: Path
) -> None:
    """Best quality prioritizes H.264 video and AAC audio in MP4."""
    output = tmp_path / "compatible.mp4"
    output.write_bytes(b"media")
    ydl = MagicMock()
    ydl.extract_info.return_value = {
        "id": "compatible",
        "title": "Compatible",
        "requested_downloads": [{"filepath": str(output)}],
    }
    constructor = _ydl_context(ydl)
    with patch("app.downloaders.yt_dlp_downloader.yt_dlp.YoutubeDL", constructor):
        YouTubeDownloader(config).download("https://youtu.be/compatible", "best")
    selector = constructor.call_args.args[0]["format"]
    assert selector.startswith("bv*[ext=mp4][vcodec^=avc1]+ba[ext=m4a]")
    assert selector.endswith("bv*+ba/b")


def test_default_output_name_is_short(config: AppConfig) -> None:
    """Default output template caps the title while retaining the video ID."""
    ydl = MagicMock()
    ydl.extract_info.return_value = {
        "id": "short",
        "title": "Short",
        "formats": [],
    }
    constructor = _ydl_context(ydl)
    with patch("app.downloaders.yt_dlp_downloader.yt_dlp.YoutubeDL", constructor):
        YouTubeDownloader(config).get_info("https://youtu.be/short")
    output = constructor.call_args.args[0]["outtmpl"]["default"]
    assert "%(title).60B" in output
    assert "[%(id)s]" in output
