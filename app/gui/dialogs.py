"""Custom Qt dialogs for Video Downloader."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.gui.settings_tab import BROWSER_CHOICES


class BrowserRetryDialog(QDialog):
    """Dialog for retrying downloads with cookies from installed browsers."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.selected_browser: str | None = None
        self.open_settings: bool = False

        self.setWindowTitle("Authentication Required")
        self.setFixedWidth(500)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #181a2a;
                color: #e0e0e0;
            }
            QPushButton[cssClass="secondary"] {
                background-color: #1e2030;
                color: #c0c6d6;
                border: 1px solid #2a2d40;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton[cssClass="secondary"]:hover {
                background-color: #2a2d40;
                border-color: #e94560;
                color: #ffffff;
            }
            QPushButton[cssClass="secondary"]:pressed {
                background-color: #e94560;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Header ──
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel("This video requires login")
        title_label.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #ffffff;"
            " background: transparent;"
        )

        desc_label = QLabel(
            "yt-dlp detected that this content requires authentication.<br>"
            "Choose a browser you are logged in to for automatic retry:"
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            "font-size: 12px; color: #a0a8c0; line-height: 1.4;"
            " background: transparent;"
        )

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        header_layout.addWidget(icon_label)
        header_layout.addLayout(text_layout)
        layout.addLayout(header_layout)

        # ── Separator ──
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        sep1.setStyleSheet("background-color: #252840; max-height: 1px; border: none;")
        layout.addWidget(sep1)

        # ── Browser Grid ──
        available_browsers = [
            (lbl, key) for lbl, key in BROWSER_CHOICES if key is not None
        ]
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        cols = 2
        for idx, (label, key) in enumerate(available_browsers):
            btn = QPushButton(label)
            btn.setProperty("cssClass", "secondary")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("browserKey", key)
            btn.clicked.connect(self._make_browser_handler(key))
            row = idx // cols
            col = idx % cols
            if idx == len(available_browsers) - 1 and idx % cols == 0:
                grid_layout.addWidget(btn, row, col, 1, cols)
            else:
                grid_layout.addWidget(btn, row, col)

        layout.addLayout(grid_layout)

        # ── Separator ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        sep2.setStyleSheet("background-color: #252840; max-height: 1px; border: none;")
        layout.addWidget(sep2)

        # ── Footer ──
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        settings_btn = QPushButton("⚙️  Manual Setup (Settings)")
        settings_btn.setProperty("cssClass", "secondary")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._on_settings_clicked)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("cssClass", "secondary")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        footer_layout.addWidget(settings_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(cancel_btn)

        layout.addLayout(footer_layout)

    def _make_browser_handler(self, key: str):
        def handler() -> None:
            self.selected_browser = key
            self.open_settings = False
            self.accept()

        return handler

    def _on_settings_clicked(self) -> None:
        self.selected_browser = None
        self.open_settings = True
        self.accept()
