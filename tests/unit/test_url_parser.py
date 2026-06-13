"""Tests for URL parsing and platform detection."""

import pytest

from app.core.exceptions import InvalidUrlError
from app.models.platform import Platform
from app.utils.url_parser import detect_platform, normalize_url


@pytest.mark.parametrize(
    ("url", "platform"),
    [
        ("https://www.youtube.com/watch?v=abc", Platform.YOUTUBE),
        ("https://youtu.be/abc", Platform.YOUTUBE),
        ("https://m.facebook.com/video/1", Platform.FACEBOOK),
        ("https://www.instagram.com/reel/abc/", Platform.INSTAGRAM),
        ("https://vm.tiktok.com/abc/", Platform.TIKTOK),
        ("https://x.com/user/status/1", Platform.TWITTER),
        ("https://player.vimeo.com/video/1", Platform.VIMEO),
        ("https://dai.ly/abc", Platform.DAILYMOTION),
    ],
)
def test_detect_platform(url: str, platform: Platform) -> None:
    """Known domains map to their expected platform."""
    assert detect_platform(url) is platform


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "ftp://youtube.com/video",
        "https://youtube.com.evil.example/video",
        "https://user:pass@youtube.com/video",
        "https://example.com/video",
    ],
)
def test_invalid_or_unsupported_url(url: str) -> None:
    """Malformed and deceptive URLs are rejected."""
    with pytest.raises(InvalidUrlError):
        detect_platform(url)


def test_normalize_url_trims_whitespace() -> None:
    """Outer whitespace does not affect valid URLs."""
    assert normalize_url("  https://youtu.be/abc  ") == "https://youtu.be/abc"
