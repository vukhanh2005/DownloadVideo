"""Application-specific exception hierarchy."""


class VideoDownloaderError(Exception):
    """Base exception for errors that can be shown safely to users."""


class InvalidUrlError(VideoDownloaderError):
    """Raised when an input URL is malformed or unsupported."""


class UnsupportedPlatformError(VideoDownloaderError):
    """Raised when no downloader is registered for a platform."""


class MetadataError(VideoDownloaderError):
    """Raised when video metadata cannot be retrieved."""


class DownloadFailedError(VideoDownloaderError):
    """Raised when a download fails."""


class PrivateVideoError(DownloadFailedError):
    """Raised when authentication is required."""


class VideoUnavailableError(DownloadFailedError):
    """Raised when a video was removed or is unavailable."""


class GeoRestrictedError(DownloadFailedError):
    """Raised when a video is unavailable in the current region."""


class NetworkError(DownloadFailedError):
    """Raised for network-related failures."""


class InsufficientStorageError(DownloadFailedError):
    """Raised when the destination does not have enough free space."""


class ConfigurationError(VideoDownloaderError):
    """Raised when configuration cannot be loaded or validated."""
