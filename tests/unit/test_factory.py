"""Tests for downloader selection."""

import pytest

from app.config.settings import AppConfig
from app.downloaders.factory import DownloaderFactory
from app.downloaders.platforms import (
    DailymotionDownloader,
    FacebookDownloader,
    InstagramDownloader,
    TikTokDownloader,
    TwitterDownloader,
    VimeoDownloader,
    YouTubeDownloader,
)


@pytest.mark.parametrize(
    ("url", "downloader_type"),
    [
        ("https://youtube.com/watch?v=1", YouTubeDownloader),
        ("https://facebook.com/watch?v=1", FacebookDownloader),
        ("https://instagram.com/reel/1", InstagramDownloader),
        ("https://tiktok.com/@user/video/1", TikTokDownloader),
        ("https://twitter.com/user/status/1", TwitterDownloader),
        ("https://vimeo.com/1", VimeoDownloader),
        ("https://dailymotion.com/video/1", DailymotionDownloader),
    ],
)
def test_factory_selects_downloader(
    config: AppConfig, url: str, downloader_type: type
) -> None:
    """Factory returns the explicitly registered platform adapter."""
    assert isinstance(DownloaderFactory(config).create(url), downloader_type)
