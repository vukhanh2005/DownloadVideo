"""Tests for domain-scoped browser cookie forwarding."""

from app.browser.cookies import BrowserCookie, BrowserCookieJar


def test_cookie_header_matches_domain_path_and_secure() -> None:
    """Only cookies valid for the target media URL are forwarded."""
    jar = BrowserCookieJar()
    jar.add(BrowserCookie("session", "abc", ".example.com", "/video", secure=True))
    jar.add(BrowserCookie("other", "bad", "other.test"))
    assert jar.header_for("https://cdn.example.com/video/file.mp4") == "session=abc"
    assert jar.header_for("http://cdn.example.com/video/file.mp4") is None
    assert jar.header_for("https://cdn.example.com/audio/file.mp3") is None


def test_cookie_is_replaced_by_identity() -> None:
    """A refreshed cookie replaces its previous value."""
    jar = BrowserCookieJar()
    jar.add(BrowserCookie("session", "old", "example.com"))
    jar.add(BrowserCookie("session", "new", "example.com"))
    assert jar.header_for("https://example.com/file.mp4") == "session=new"
