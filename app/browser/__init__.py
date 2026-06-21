"""Embedded-browser media detection and download support."""

from app.browser.detector import MediaDetector
from app.browser.download_manager import BrowserDownloadManager
from app.browser.models import BrowserMedia, BrowserMediaType, DownloadState

__all__ = [
    "BrowserDownloadManager",
    "BrowserMedia",
    "BrowserMediaType",
    "DownloadState",
    "MediaDetector",
]
