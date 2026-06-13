"""Explicit platform adapters backed by the shared yt-dlp implementation."""

from app.downloaders.yt_dlp_downloader import YtDlpDownloader
from app.models.platform import Platform


class YouTubeDownloader(YtDlpDownloader):
    """YouTube downloader."""

    platform = Platform.YOUTUBE


class FacebookDownloader(YtDlpDownloader):
    """Facebook downloader."""

    platform = Platform.FACEBOOK


class InstagramDownloader(YtDlpDownloader):
    """Instagram downloader."""

    platform = Platform.INSTAGRAM


class TikTokDownloader(YtDlpDownloader):
    """TikTok downloader."""

    platform = Platform.TIKTOK


class TwitterDownloader(YtDlpDownloader):
    """X/Twitter downloader."""

    platform = Platform.TWITTER


class VimeoDownloader(YtDlpDownloader):
    """Vimeo downloader."""

    platform = Platform.VIMEO


class DailymotionDownloader(YtDlpDownloader):
    """Dailymotion downloader."""

    platform = Platform.DAILYMOTION
