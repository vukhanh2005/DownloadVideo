"""URL validation and source-platform detection."""

from urllib.parse import urlparse

from app.core.exceptions import InvalidUrlError
from app.models.platform import Platform

_PLATFORM_DOMAINS: dict[Platform, tuple[str, ...]] = {
    Platform.YOUTUBE: ("youtube.com", "youtu.be", "youtube-nocookie.com"),
    Platform.FACEBOOK: ("facebook.com", "fb.watch"),
    Platform.INSTAGRAM: ("instagram.com",),
    Platform.TIKTOK: ("tiktok.com",),
    Platform.TWITTER: ("twitter.com", "x.com"),
    Platform.VIMEO: ("vimeo.com",),
    Platform.DAILYMOTION: ("dailymotion.com", "dai.ly"),
}


def normalize_url(url: str) -> str:
    """Validate and normalize an HTTP(S) URL."""
    candidate = url.strip()
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise InvalidUrlError("URL must be a valid http:// or https:// address")
    if parsed.username or parsed.password:
        raise InvalidUrlError("URLs containing credentials are not accepted")
    return candidate


def detect_platform(url: str) -> Platform:
    """Detect a supported platform using exact domain suffix matching."""
    candidate = normalize_url(url)
    hostname = (urlparse(candidate).hostname or "").lower().rstrip(".")
    if hostname.startswith("www."):
        hostname = hostname[4:]

    for platform, domains in _PLATFORM_DOMAINS.items():
        if any(
            hostname == domain or hostname.endswith(f".{domain}") for domain in domains
        ):
            return platform
    raise InvalidUrlError(f"Unsupported video platform: {hostname}")
