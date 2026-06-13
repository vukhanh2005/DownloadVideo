"""Factory selecting a downloader from a source URL."""

from collections.abc import Callable

from app.config.settings import AppConfig
from app.core.protocols import Downloader
from app.downloaders.platforms import (
    DailymotionDownloader,
    FacebookDownloader,
    InstagramDownloader,
    TikTokDownloader,
    TwitterDownloader,
    VimeoDownloader,
    YouTubeDownloader,
)
from app.models.platform import Platform
from app.utils.url_parser import detect_platform

DownloaderBuilder = Callable[[AppConfig], Downloader]


class DownloaderFactory:
    """Create downloader instances while keeping services platform-agnostic."""

    def __init__(
        self,
        config: AppConfig,
        registry: dict[Platform, DownloaderBuilder] | None = None,
    ) -> None:
        self.config = config
        self.registry = registry or {
            Platform.YOUTUBE: YouTubeDownloader,
            Platform.FACEBOOK: FacebookDownloader,
            Platform.INSTAGRAM: InstagramDownloader,
            Platform.TIKTOK: TikTokDownloader,
            Platform.TWITTER: TwitterDownloader,
            Platform.VIMEO: VimeoDownloader,
            Platform.DAILYMOTION: DailymotionDownloader,
        }

    def create(self, url: str) -> Downloader:
        """Return the downloader registered for the detected URL platform."""
        return self.registry[detect_platform(url)](self.config)
