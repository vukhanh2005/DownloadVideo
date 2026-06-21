"""Tests for HLS master and media playlist parsing."""

import pytest

from app.browser.hls import parse_hls_playlist
from app.core.exceptions import DownloadFailedError


def test_parse_master_playlist_variants() -> None:
    """Variant URLs, quality, bandwidth, and codecs are normalized."""
    playlist = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1,mp4a"
low/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1920x1080
https://cdn.example/high.m3u8
"""
    variants = parse_hls_playlist(playlist, "https://cdn.example/master.m3u8")
    assert [variant.quality for variant in variants] == ["360p", "1080p"]
    assert variants[0].url == "https://cdn.example/low/index.m3u8"
    assert variants[0].bandwidth == 800000
    assert variants[0].codecs == "avc1,mp4a"


def test_media_playlist_returns_source_variant() -> None:
    """A non-master HLS playlist remains directly downloadable."""
    playlist = "#EXTM3U\n#EXTINF:5,\nsegment.ts\n#EXT-X-ENDLIST\n"
    variants = parse_hls_playlist(playlist, "https://cdn.example/video.m3u8")
    assert len(variants) == 1
    assert variants[0].quality == "Source"


@pytest.mark.parametrize(
    "key_line",
    [
        '#EXT-X-KEY:METHOD=SAMPLE-AES,URI="key"',
        '#EXT-X-KEY:METHOD=AES-128,KEYFORMAT="com.apple.streamingkeydelivery"',
        '#EXT-X-KEY:METHOD=AES-128,KEYFORMAT="urn:uuid:WIDEVINE"',
        '#EXT-X-KEY:METHOD=AES-128,KEYFORMAT="PLAYREADY"',
    ],
)
def test_reject_drm_hls(key_line: str) -> None:
    """Known DRM HLS key formats are never passed to the downloader."""
    with pytest.raises(DownloadFailedError, match="DRM"):
        parse_hls_playlist(f"#EXTM3U\n{key_line}\nsegment.ts\n", "https://x/a.m3u8")


def test_invalid_playlist_is_rejected() -> None:
    """Non-HLS text does not become a download candidate."""
    with pytest.raises(DownloadFailedError, match="valid HLS"):
        parse_hls_playlist("not a playlist", "https://x/a.m3u8")
