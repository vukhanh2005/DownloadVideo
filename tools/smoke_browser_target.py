"""Exercise BrowserDownloaderTab against the reported target page."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QApplication

from app.config.settings import load_config
from app.gui.browser_tab import BrowserDownloaderTab

TARGET = "https://animevietsub.pl/phim/" "doraemon-new-series-i2-a908/xem-phim.html"

app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
tab = BrowserDownloaderTab(load_config())
tab.resize(1400, 900)
tab.show()
view = tab._current_view()  # pylint: disable=protected-access
assert view is not None
view.setUrl(QUrl(TARGET))


def finish() -> None:
    """Report media accepted by the production browser component."""
    matches = [
        media for media in tab.media_by_url.values() if "playlist.m3u8" in media.url
    ]
    for media in matches:
        print("DETECTED", media.url, media.referer, flush=True)
    tab.close()
    app.quit()
    if not matches:
        raise SystemExit(2)


QTimer.singleShot(30000, finish)
raise SystemExit(app.exec())
