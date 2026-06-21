"""Tests for browser media URL and MIME detection."""

import pytest

from app.browser.detector import MediaDetector
from app.browser.models import BrowserMediaType


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://cdn.example/video.mp4?token=1", BrowserMediaType.VIDEO),
        ("https://cdn.example/stream/master.m3u8", BrowserMediaType.HLS),
        ("https://cdn.example/audio.MP3", BrowserMediaType.AUDIO),
        ("https://cdn.example/file.webm", BrowserMediaType.VIDEO),
        ("https://cdn.example/audio.aac", BrowserMediaType.AUDIO),
    ],
)
def test_detect_media_by_extension(url: str, expected: BrowserMediaType) -> None:
    """Supported media extensions are recognized despite query parameters."""
    media = MediaDetector().detect(url)
    assert media is not None
    assert media.media_type is expected


def test_detect_extensionless_media_by_mime() -> None:
    """Response MIME can classify signed URLs without file extensions."""
    media = MediaDetector().detect(
        "https://cdn.example/signed/abc?token=1",
        mime_type="video/mp4; charset=binary",
        size=1234,
    )
    assert media is not None
    assert media.media_type is BrowserMediaType.VIDEO
    assert media.mime_type == "video/mp4"
    assert media.size == 1234


def test_resource_hint_detects_extensionless_media() -> None:
    """Chromium's media resource type provides a safe fallback hint."""
    media = MediaDetector().detect(
        "https://cdn.example/playback?id=1",
        media_type_hint=BrowserMediaType.VIDEO,
    )
    assert media is not None
    assert media.media_type is BrowserMediaType.VIDEO


@pytest.mark.parametrize(
    "url", ["blob:https://example.com/1", "file:///video.mp4", "bad"]
)
def test_reject_non_http_urls(url: str) -> None:
    """Internal, local, and malformed URLs are ignored."""
    assert MediaDetector().detect(url) is None


def test_infer_quality_from_url() -> None:
    """Common resolution tokens are exposed to the media table."""
    media = MediaDetector().detect("https://cdn.example/video_1080_.mp4")
    assert media is not None
    assert media.quality == "1080p"
