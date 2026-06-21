"""Media URL and MIME detection for browser network requests."""

from __future__ import annotations

import mimetypes
from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

from app.browser.models import BrowserMedia, BrowserMediaType

_EXTENSION_TYPES: dict[str, BrowserMediaType] = {
    ".mp4": BrowserMediaType.VIDEO,
    ".m4v": BrowserMediaType.VIDEO,
    ".webm": BrowserMediaType.VIDEO,
    ".mov": BrowserMediaType.VIDEO,
    ".m3u8": BrowserMediaType.HLS,
    ".mp3": BrowserMediaType.AUDIO,
    ".m4a": BrowserMediaType.AUDIO,
    ".aac": BrowserMediaType.AUDIO,
    ".ogg": BrowserMediaType.AUDIO,
    ".opus": BrowserMediaType.AUDIO,
}


class MediaDetector:
    """Classify browser requests without making network calls."""

    def detect(
        self,
        url: str,
        *,
        mime_type: str | None = None,
        size: int | None = None,
        source_page: str | None = None,
        referer: str | None = None,
        user_agent: str | None = None,
        media_type_hint: BrowserMediaType | None = None,
    ) -> BrowserMedia | None:
        """Return a media model when URL or MIME indicates supported media."""
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return None

        normalized_mime = self.normalize_mime(mime_type)
        media_type = self.type_from_mime(normalized_mime)
        suffix = PurePosixPath(unquote(parsed.path)).suffix.lower()
        media_type = media_type or _EXTENSION_TYPES.get(suffix) or media_type_hint
        if media_type is None:
            return None

        guessed_mime = normalized_mime or mimetypes.guess_type(parsed.path)[0]
        name = PurePosixPath(unquote(parsed.path)).name or f"media{suffix}"
        quality = self.infer_quality(url)
        return BrowserMedia(
            url=url,
            media_type=media_type,
            name=name[:120],
            mime_type=guessed_mime,
            size=size,
            quality=quality,
            source_page=source_page,
            referer=referer,
            user_agent=user_agent,
        )

    @staticmethod
    def normalize_mime(mime_type: str | None) -> str | None:
        """Remove MIME parameters and normalize casing."""
        if not mime_type:
            return None
        return mime_type.split(";", 1)[0].strip().lower() or None

    @staticmethod
    def type_from_mime(mime_type: str | None) -> BrowserMediaType | None:
        """Map supported MIME families to media types."""
        if not mime_type:
            return None
        if mime_type in {
            "application/vnd.apple.mpegurl",
            "application/x-mpegurl",
            "audio/mpegurl",
        }:
            return BrowserMediaType.HLS
        if mime_type.startswith("video/"):
            return BrowserMediaType.VIDEO
        if mime_type.startswith("audio/"):
            return BrowserMediaType.AUDIO
        return None

    @staticmethod
    def infer_quality(value: str) -> str | None:
        """Infer common vertical resolutions embedded in a media URL."""
        lowered = value.lower()
        for height in (4320, 2160, 1440, 1080, 720, 480, 360, 240, 144):
            tokens = (f"{height}p", f"{height}.", f"_{height}_", f"/{height}/")
            if any(token in lowered for token in tokens):
                return f"{height}p"
        return None
