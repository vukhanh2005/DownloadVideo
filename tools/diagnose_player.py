"""Temporarily inspect the embedded player request flow."""

from __future__ import annotations

import json
import sys

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineScript,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

PLAYER_URL = "https://animevietsub.pl/phim/" "doraemon-new-series-i2-a908/xem-phim.html"


class RequestLog(QWebEngineUrlRequestInterceptor):
    """Collect Chromium requests for diagnostic output."""

    def __init__(self) -> None:
        super().__init__()
        self.items: list[tuple[int, str]] = []

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        url = info.requestUrl().toString()
        self.items.append((info.resourceType().value, url))
        if url.startswith("https://media-capture.invalid/"):
            print("CAPTURE", url, flush=True)
            info.block(True)


app = QApplication(sys.argv)
app.setQuitOnLastWindowClosed(False)
profile = QWebEngineProfile("player-diagnostic", app)
capture_script = QWebEngineScript()
capture_script.setName("capture-jwplayer-sources")
capture_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
capture_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
capture_script.setRunsOnSubFrames(True)
capture_script.setSourceCode("""
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
            if (player && typeof player.setup === "function" && !player.__captured) {
              const originalSetup = player.setup;
              player.setup = function(options) {
                try {
                  const payload = encodeURIComponent(JSON.stringify(options || {}));
                  fetch("https://media-capture.invalid/jwplayer?payload=" + payload)
                    .catch(() => {});
                } catch (_) {}
                return originalSetup.apply(this, arguments);
              };
              player.__captured = true;
            }
            return player;
          };
          Object.assign(wrapped, value);
          assigned = wrapped;
        }
      });
    })();
    """)
profile.scripts().insert(capture_script)
requests = RequestLog()
profile.setUrlRequestInterceptor(requests)
view = QWebEngineView()
view.resize(1280, 800)
view.setPage(QWebEnginePage(profile, view))
view.show()


def inspect() -> None:
    """Dump player DOM state before playback."""
    script = """
    (() => ({
      title: document.title,
      frames: [...document.querySelectorAll("iframe")].map(frame => ({
        src: frame.src, rect: frame.getBoundingClientRect().toJSON()
      })),
      buttons: [...document.querySelectorAll("button,[role=button]")].map(node => ({
        className: node.className, ariaLabel: node.getAttribute("aria-label"),
        text: node.innerText
      })).slice(0, 30)
    }))()
    """
    view.page().runJavaScript(
        script,
        lambda result: print(
            "DOM", json.dumps(result, ensure_ascii=False)[:12000], flush=True
        ),
    )
    view.page().runJavaScript(
        """
        (() => {
          const frame = document.querySelector('#media-player iframe');
          if (!frame) return false;
          frame.scrollIntoView({block: 'center'});
          return true;
        })()
        """,
        lambda result: print("SCROLL", result, flush=True),
    )
    QTimer.singleShot(2500, start_playback)


def start_playback() -> None:
    """Activate the ordinary player control."""
    view.grab().save("player-before.png")
    from PySide6.QtCore import QPoint
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt

    QTest.mouseClick(
        view.focusProxy() or view,
        Qt.MouseButton.LeftButton,
        pos=QPoint(view.width() // 2, min(view.height() - 80, 700)),
    )
    print("CLICK", view.width() // 2, min(view.height() - 80, 700), flush=True)
    QTimer.singleShot(20000, finish)


def finish() -> None:
    """Print requests relevant to media delivery."""
    view.grab().save("player-after.png")
    print("REQUESTS", len(requests.items), flush=True)
    for resource_type, url in requests.items:
        lowered = url.lower()
        if (
            "stream.googleapiscdn.com" in lowered
            or "googleusercontent.com" in lowered
            or "googlevideo.com" in lowered
            or "m3u8" in lowered
            or ".mp4" in lowered
            or ".ts" in lowered
        ):
            print(resource_type, url, flush=True)
    app.quit()


view.loadFinished.connect(
    lambda ok: (
        print("LOADED", ok, view.url().toString(), flush=True),
        QTimer.singleShot(3000, inspect),
    )
)
view.setUrl(QUrl(PLAYER_URL))
QTimer.singleShot(45000, app.quit)
raise SystemExit(app.exec())
