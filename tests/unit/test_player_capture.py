"""Tests for embedded-player source capture parsing."""

from urllib.parse import urlencode

from app.browser.player_capture import parse_captured_source


def test_parse_captured_source_resolves_relative_url() -> None:
    """Player URLs are resolved against the iframe that configured them."""
    query = urlencode(
        {
            "url": "/playlist/main.m3u8?token=abc",
            "base": "https://player.example/embed/123",
            "type": "hls",
            "label": "720p",
        }
    )
    result = parse_captured_source(
        f"https://media-capture.invalid/source?{query}",
        "https://player.example/embed/123",
    )
    assert result == (
        "https://player.example/playlist/main.m3u8?token=abc",
        "https://player.example/embed/123",
        "hls",
        "720p",
    )


def test_parse_captured_source_rejects_untrusted_or_unsafe_url() -> None:
    """Only observer requests and HTTP media targets are accepted."""
    assert (
        parse_captured_source(
            "https://example.com/source?url=https://cdn.example/video.mp4",
            "https://player.example/embed",
        )
        is None
    )
    unsafe_base = urlencode({"url": "/media.m3u8", "base": "javascript:alert(1)"})
    assert (
        parse_captured_source(
            f"https://media-capture.invalid/source?{unsafe_base}",
            "https://player.example/embed",
        )
        is None
    )
    assert (
        parse_captured_source(
            "https://media-capture.invalid/source?url=javascript%3Aalert(1)",
            "https://player.example/embed",
        )
        is None
    )
