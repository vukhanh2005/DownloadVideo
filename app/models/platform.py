"""Supported platform identifiers."""

from enum import StrEnum


class Platform(StrEnum):
    """Platforms with an explicitly registered downloader."""

    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    VIMEO = "vimeo"
    DAILYMOTION = "dailymotion"
