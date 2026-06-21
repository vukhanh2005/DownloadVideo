"""Domain-scoped browser cookie handling."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class BrowserCookie:
    """Minimal cookie fields needed for safe request forwarding."""

    name: str
    value: str
    domain: str
    path: str = "/"
    secure: bool = False


class BrowserCookieJar:
    """Store cookies and build headers only for matching media URLs."""

    def __init__(self) -> None:
        self._cookies: dict[tuple[str, str, str], BrowserCookie] = {}

    def add(self, cookie: BrowserCookie) -> None:
        """Add or replace a cookie with the same domain, path, and name."""
        key = (cookie.domain.lower(), cookie.path or "/", cookie.name)
        self._cookies[key] = cookie

    def header_for(self, url: str) -> str | None:
        """Return a Cookie header restricted by domain, path, and secure flag."""
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        request_path = parsed.path or "/"
        matches = []
        for cookie in self._cookies.values():
            domain = cookie.domain.lower().lstrip(".")
            domain_matches = host == domain or host.endswith(f".{domain}")
            path_matches = request_path.startswith(cookie.path or "/")
            secure_matches = not cookie.secure or parsed.scheme == "https"
            if domain_matches and path_matches and secure_matches:
                matches.append(f"{cookie.name}={cookie.value}")
        return "; ".join(matches) or None
