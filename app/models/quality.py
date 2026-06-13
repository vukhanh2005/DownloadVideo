"""Download quality choices."""

from enum import StrEnum


class Quality(StrEnum):
    """User-facing quality presets."""

    BEST = "best"
    P1080 = "1080p"
    P720 = "720p"
    P480 = "480p"
    AUDIO = "audio"
