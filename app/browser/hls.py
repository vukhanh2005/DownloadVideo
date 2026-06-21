"""HLS playlist parsing with explicit DRM rejection."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from app.browser.models import HlsVariant
from app.core.exceptions import DownloadFailedError

_ATTRIBUTE_PATTERN = re.compile(r"""(?P<key>[A-Z0-9-]+)=(?P<value>"[^"]*"|[^,]*)""")


def parse_hls_playlist(content: str, base_url: str) -> list[HlsVariant]:
    """Parse variants from an HLS master playlist.

    Media playlists return a single source variant. Streams advertising common
    DRM key formats or SAMPLE-AES are rejected.
    """
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines or lines[0] != "#EXTM3U":
        raise DownloadFailedError("The response is not a valid HLS playlist.")
    _reject_drm(lines)

    variants: list[HlsVariant] = []
    for index, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF:"):
            continue
        attributes = _parse_attributes(line.partition(":")[2])
        stream_url = _next_uri(lines, index + 1)
        if stream_url is None:
            continue
        resolution = attributes.get("RESOLUTION")
        quality = _quality_label(resolution, attributes.get("NAME"))
        bandwidth = _as_int(attributes.get("BANDWIDTH"))
        variants.append(
            HlsVariant(
                url=urljoin(base_url, stream_url),
                quality=quality,
                bandwidth=bandwidth,
                codecs=attributes.get("CODECS"),
            )
        )
    if variants:
        return variants
    return [HlsVariant(url=base_url, quality="Source")]


def _parse_attributes(value: str) -> dict[str, str]:
    return {
        match.group("key"): match.group("value").strip('"')
        for match in _ATTRIBUTE_PATTERN.finditer(value)
    }


def _next_uri(lines: list[str], start: int) -> str | None:
    for line in lines[start:]:
        if not line.startswith("#"):
            return line
        if line.startswith("#EXT-X-STREAM-INF:"):
            return None
    return None


def _quality_label(resolution: str | None, name: str | None) -> str:
    if resolution and "x" in resolution:
        return f"{resolution.rsplit('x', 1)[-1]}p"
    return name or "Variant"


def _as_int(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _reject_drm(lines: list[str]) -> None:
    drm_tokens = (
        "SAMPLE-AES",
        "WIDEVINE",
        "FAIRPLAY",
        "PLAYREADY",
        "STREAMINGKEYDELIVERY",
    )
    for line in lines:
        if line.startswith("#EXT-X-KEY") and any(
            token in line.upper() for token in drm_tokens
        ):
            raise DownloadFailedError("DRM-protected HLS streams are not supported.")
