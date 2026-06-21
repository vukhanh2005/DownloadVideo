"""Small HTTP helpers for media metadata and HLS retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.exceptions import NetworkError


@dataclass(frozen=True, slots=True)
class HttpMetadata:
    """Response metadata needed by the media detector."""

    mime_type: str | None
    size: int | None
    final_url: str


class BrowserHttpClient:
    """HTTP client with bounded requests and browser-compatible headers."""

    def probe(
        self,
        url: str,
        *,
        referer: str | None = None,
        user_agent: str | None = None,
        cookies: str | None = None,
        timeout: int = 15,
    ) -> HttpMetadata:
        """Read response headers without downloading the full media."""
        request = Request(
            url, method="HEAD", headers=self._headers(referer, user_agent, cookies)
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return HttpMetadata(
                    mime_type=response.headers.get_content_type(),
                    size=_content_length(response.headers.get("Content-Length")),
                    final_url=response.geturl(),
                )
        except HTTPError as exc:
            if exc.code not in {403, 405}:
                raise NetworkError(
                    f"Cannot inspect media URL: HTTP {exc.code}"
                ) from exc
        except URLError as exc:
            raise NetworkError(f"Cannot inspect media URL: {exc.reason}") from exc

        fallback = Request(
            url,
            headers={
                **self._headers(referer, user_agent, cookies),
                "Range": "bytes=0-0",
            },
        )
        try:
            with urlopen(fallback, timeout=timeout) as response:
                return HttpMetadata(
                    mime_type=response.headers.get_content_type(),
                    size=_total_size(
                        response.headers.get("Content-Range"),
                        response.headers.get("Content-Length"),
                    ),
                    final_url=response.geturl(),
                )
        except (HTTPError, URLError) as exc:
            raise NetworkError(f"Cannot inspect media URL: {exc}") from exc

    def get_text(
        self,
        url: str,
        *,
        referer: str | None = None,
        user_agent: str | None = None,
        cookies: str | None = None,
        timeout: int = 20,
        max_bytes: int = 2_000_000,
    ) -> str:
        """Fetch a bounded UTF-8 text response such as an HLS manifest."""
        request = Request(url, headers=self._headers(referer, user_agent, cookies))
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read(max_bytes + 1)
        except (HTTPError, URLError) as exc:
            raise NetworkError(f"Cannot load playlist: {exc}") from exc
        if len(payload) > max_bytes:
            raise NetworkError("Playlist exceeds the allowed size.")
        return payload.decode("utf-8", errors="replace")

    @staticmethod
    def _headers(
        referer: str | None, user_agent: str | None, cookies: str | None
    ) -> dict[str, str]:
        headers = {"Accept": "*/*"}
        if referer:
            headers["Referer"] = referer
        if user_agent:
            headers["User-Agent"] = user_agent
        if cookies:
            headers["Cookie"] = cookies
        return headers


def _content_length(value: str | None) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _total_size(content_range: str | None, content_length: str | None) -> int | None:
    if content_range and "/" in content_range:
        return _content_length(content_range.rsplit("/", 1)[-1])
    return _content_length(content_length)
