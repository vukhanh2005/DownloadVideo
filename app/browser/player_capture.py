"""Capture non-DRM media URLs passed to common JavaScript players."""

from __future__ import annotations

from urllib.parse import parse_qs, urljoin, urlparse

CAPTURE_ORIGIN = "https://media-capture.invalid"

JWPLAYER_CAPTURE_SCRIPT = """
(() => {
  let assigned;
  Object.defineProperty(window, "jwplayer", {
    configurable: true,
    get: () => assigned,
    set: value => {
      if (typeof value !== "function") {
        assigned = value;
        return;
      }
      const wrapped = function(...args) {
        const player = value.apply(this, args);
        if (player && typeof player.setup === "function" && !player.__mediaCaptured) {
          const originalSetup = player.setup;
          player.setup = function(options) {
            try {
              const sources = Array.isArray(options && options.sources)
                ? options.sources : [];
              sources.forEach(source => {
                const file = typeof source === "string"
                  ? source
                  : source && source.file;
                if (!file) return;
                const params = new URLSearchParams({
                  url: file,
                  base: location.href,
                  type: (source && source.type) || "",
                  label: (source && source.label) || ""
                });
                fetch("https://media-capture.invalid/source?" + params).catch(() => {});
              });
            } catch (_) {}
            return originalSetup.apply(this, arguments);
          };
          player.__mediaCaptured = true;
        }
        return player;
      };
      Object.assign(wrapped, value);
      assigned = wrapped;
    }
  });
})();
"""


def parse_captured_source(
    request_url: str, frame_url: str
) -> tuple[str, str, str, str] | None:
    """Parse and resolve a media source emitted by the injected player observer."""
    parsed = urlparse(request_url)
    if f"{parsed.scheme}://{parsed.netloc}" != CAPTURE_ORIGIN:
        return None
    values = parse_qs(parsed.query)
    source = values.get("url", [""])[0].strip()
    if not source:
        return None
    base_url = values.get("base", [frame_url])[0]
    if urlparse(base_url).scheme not in {"http", "https"}:
        return None
    resolved = urljoin(base_url, source)
    if urlparse(resolved).scheme not in {"http", "https"}:
        return None
    return (
        resolved,
        base_url,
        values.get("type", [""])[0],
        values.get("label", [""])[0],
    )
