"""Integration tests for browser HTTP metadata and HLS workflows."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.browser.detector import MediaDetector
from app.browser.hls import parse_hls_playlist
from app.browser.http import BrowserHttpClient
from app.browser.models import BrowserMediaType


class _Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:  # noqa: N802
        if self.path == "/cookie-media":
            if self.headers.get("Cookie") != "session=valid":
                self.send_error(403)
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", "1024")
            self.end_headers()
            return
        if self.path == "/signed":
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", "4096")
            self.end_headers()
            return
        self.send_error(405)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/master.m3u8":
            payload = (
                b"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000,"
                b"RESOLUTION=1280x720\n720/index.m3u8\n"
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.apple.mpegurl")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_error(404)

    def log_message(self, _format: str, *_args: object) -> None:
        return


@pytest.fixture
def local_server():
    """Run a local deterministic HTTP server for integration tests."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_probe_then_detect_extensionless_media(local_server: str) -> None:
    """HTTP MIME enrichment detects signed extensionless media URLs."""
    url = f"{local_server}/signed"
    metadata = BrowserHttpClient().probe(url)
    media = MediaDetector().detect(
        metadata.final_url,
        mime_type=metadata.mime_type,
        size=metadata.size,
    )
    assert media is not None
    assert media.media_type is BrowserMediaType.VIDEO
    assert media.size == 4096


def test_fetch_and_parse_hls(local_server: str) -> None:
    """A real HTTP manifest is fetched and parsed into a quality variant."""
    url = f"{local_server}/master.m3u8"
    content = BrowserHttpClient().get_text(url)
    variants = parse_hls_playlist(content, url)
    assert variants[0].quality == "720p"
    assert variants[0].url == f"{local_server}/720/index.m3u8"


def test_probe_sends_browser_cookie(local_server: str) -> None:
    """Protected media probes retain the browser session cookie."""
    metadata = BrowserHttpClient().probe(
        f"{local_server}/cookie-media", cookies="session=valid"
    )
    assert metadata.mime_type == "video/mp4"
    assert metadata.size == 1024
