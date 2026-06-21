"""Qt WebEngine request interception adapter."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWebEngineCore import (
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)

from app.browser.detector import MediaDetector
from app.browser.models import BrowserMedia, BrowserMediaType
from app.browser.player_capture import CAPTURE_ORIGIN, parse_captured_source


class MediaRequestInterceptor(QWebEngineUrlRequestInterceptor):
    """Emit media resources observed by Chromium's request pipeline."""

    media_detected = Signal(object)
    candidate_detected = Signal(str, str)
    player_source_detected = Signal(str, str, str, str)

    def __init__(self, detector: MediaDetector, parent=None) -> None:
        super().__init__(parent)
        self.detector = detector

    def interceptRequest(  # noqa: N802  # pylint: disable=invalid-name
        self, info: QWebEngineUrlRequestInfo
    ) -> None:
        """Inspect a request without blocking or modifying it."""
        url = info.requestUrl().toString()
        first_party = info.firstPartyUrl().toString()
        if url.startswith(CAPTURE_ORIGIN):
            captured = parse_captured_source(url, first_party)
            info.block(True)
            if captured:
                source, frame_url, media_type, label = captured
                self.player_source_detected.emit(source, frame_url, media_type, label)
            return
        media_hint = (
            BrowserMediaType.VIDEO
            if info.resourceType()
            is QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMedia
            else None
        )
        media = self.detector.detect(
            url,
            source_page=first_party or None,
            referer=first_party or None,
            media_type_hint=media_hint,
        )
        if isinstance(media, BrowserMedia):
            self.media_detected.emit(media)
        elif (
            info.resourceType() is QWebEngineUrlRequestInfo.ResourceType.ResourceTypeXhr
        ):
            self.candidate_detected.emit(url, first_party)
