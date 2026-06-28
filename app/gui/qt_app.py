"""Qt application bootstrap and main window."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from app.config.settings import AppConfig, load_config
from app.gui.browser_tab import BrowserDownloaderTab
from app.gui.classic_tab import ClassicDownloaderTab
from app.gui.history_tab import HistoryTab
from app.gui.settings_tab import SettingsTab
from app.utils.logging import configure_browser_logging, configure_logging

DARK_STYLESHEET = """
/* ── Global ── */
QWidget {
    background-color: #0f111a;
    color: #e0e0e0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

/* ── Main Window ── */
QMainWindow {
    background-color: #0f111a;
}

/* ── Tab Widget ── */
QTabWidget::pane {
    border: 1px solid #1e2030;
    border-radius: 6px;
    background: #181a2a;
    top: -1px;
}
QTabBar::tab {
    background: #1e2030;
    color: #8890a4;
    padding: 10px 28px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #1e2030;
    border-bottom: none;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #181a2a;
    color: #e94560;
    border-color: #1e2030;
}
QTabBar::tab:hover:!selected {
    background: #252840;
    color: #c0c6d6;
}

/* ── Buttons ── */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e94560, stop:1 #c73650);
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 12px;
    min-height: 20px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #ff5a78, stop:1 #e94560);
}
QPushButton:pressed {
    background: #b02e4a;
}
QPushButton:disabled {
    background: #2a2d40;
    color: #555;
}

/* ── Secondary / small buttons ── */
QPushButton[cssClass="secondary"] {
    background: #1e2030;
    color: #c0c6d6;
    border: 1px solid #2a2d40;
}
QPushButton[cssClass="secondary"]:hover {
    background: #2a2d40;
    color: #fff;
}

/* ── Line Edits ── */
QLineEdit {
    background: #1a1c2e;
    color: #e0e0e0;
    border: 1px solid #2a2d40;
    border-radius: 6px;
    padding: 7px 12px;
    selection-background-color: #e94560;
    font-size: 13px;
}
QLineEdit:focus {
    border-color: #e94560;
}

/* ── Combo Box ── */
QComboBox {
    background: #1a1c2e;
    color: #e0e0e0;
    border: 1px solid #2a2d40;
    border-radius: 6px;
    padding: 7px 12px;
    min-height: 20px;
}
QComboBox:hover {
    border-color: #e94560;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #1a1c2e;
    color: #e0e0e0;
    border: 1px solid #2a2d40;
    selection-background-color: #e94560;
}

/* ── Progress Bar (compact) ── */
QProgressBar {
    background: #1a1c2e;
    border: none;
    border-radius: 5px;
    height: 10px;
    max-height: 10px;
    text-align: center;
    font-size: 0px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e94560, stop:0.5 #ff6b81, stop:1 #e94560);
    border-radius: 5px;
}

/* ── Text Edit (log area) ── */
QTextEdit {
    background: #12132200;
    background-color: #121322;
    color: #b0b8c8;
    border: 1px solid #1e2030;
    border-radius: 6px;
    padding: 8px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
}

/* ── Tables ── */
QTableWidget {
    background: #13152200;
    background-color: #131522;
    color: #d0d4e0;
    border: 1px solid #1e2030;
    border-radius: 6px;
    gridline-color: #1e2030;
    selection-background-color: #2a1525;
    selection-color: #ff6b81;
    font-size: 12px;
}
QTableWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #1a1c2e;
}
QTableWidget::item:selected {
    background: #2a1525;
}
QHeaderView::section {
    background: #1a1c2e;
    color: #8890a4;
    border: none;
    border-bottom: 2px solid #e94560;
    padding: 6px 10px;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
}

/* ── Splitter ── */
QSplitter::handle {
    background: #1e2030;
    width: 2px;
}

/* ── Status Bar ── */
QStatusBar {
    background: #0d0f18;
    color: #5a6080;
    border-top: 1px solid #1e2030;
    font-size: 11px;
    padding: 4px;
}

/* ── Labels ── */
QLabel {
    color: #c0c6d6;
    font-size: 13px;
    background: transparent;
}
QLabel[cssClass="heading"] {
    color: #e94560;
    font-weight: 700;
    font-size: 14px;
}
QLabel[cssClass="status"] {
    color: #8890a4;
    font-size: 12px;
}

/* ── Scroll Bar ── */
QScrollBar:vertical {
    background: #0f111a;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #2a2d40;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #e94560;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #0f111a;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #2a2d40;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #e94560;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Form Row labels ── */
QFormLayout QLabel {
    font-weight: 600;
    color: #8890a4;
}

/* ── Message Box ── */
QMessageBox {
    background: #181a2a;
}
QMessageBox QLabel {
    color: #e0e0e0;
}
QMessageBox QPushButton {
    min-width: 80px;
}

/* ── File Dialog ── */
QFileDialog {
    background: #181a2a;
}

/* ── Tool Tip ── */
QToolTip {
    background: #1e2030;
    color: #e0e0e0;
    border: 1px solid #2a2d40;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}
"""


class MainWindow(QMainWindow):
    """Top-level window hosting the video downloader."""

    def __init__(self, config: AppConfig, config_path: Path = Path("config.yaml")) -> None:
        super().__init__()
        self.setWindowTitle("🎬 Video Downloader")
        self.resize(740, 520)
        self.setMinimumSize(560, 420)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._downloader = ClassicDownloaderTab(config)
        self._browser = BrowserDownloaderTab(config)
        history = HistoryTab()
        self._settings = SettingsTab(config, config_path)

        # Wire download completion to history
        self._downloader.file_saved.connect(history.add_entry)
        self._browser.file_saved.connect(history.add_entry)

        # Wire config changes to live-reload downloader tabs
        self._settings.config_saved.connect(self._on_config_saved)

        self._tabs.addTab(self._downloader, "⬇  Download")
        self._tabs.addTab(self._browser, "🌐  Browser Downloader")
        self._tabs.addTab(history, "📋  History")
        self._tabs.addTab(self._settings, "⚙  Settings")
        self.setCentralWidget(self._tabs)

        self.statusBar().showMessage(
            "⚠  Download only media you are authorized to access. DRM is not supported."
        )

    def _on_config_saved(self, new_config: AppConfig) -> None:
        """Propagate new config to the downloader tabs without restart."""
        self._downloader.config = new_config
        self._browser.config = new_config
        self.statusBar().showMessage(
            "✅  Settings saved — new downloads will use the updated configuration.",
            4000,
        )


def launch_gui(config_path: Path = Path("config.yaml")) -> None:  # noqa: B008
    """Create and run the PySide6 desktop application."""

    config = load_config(config_path)
    configure_logging(config.log_path)
    configure_browser_logging(config.browser_log_path)

    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("Video Downloader")
    application.setOrganizationName("NVK")
    application.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
    application.setStyleSheet(DARK_STYLESHEET)

    # Set a premium font globally
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    application.setFont(font)

    window = MainWindow(config, config_path)
    window.show()
    application.exec()
