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


class AboutDialog(QDialog):
    """About & Diagnostic dialog displaying system information and component health."""

    def __init__(self, config=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("About Video Downloader")
        self.setFixedWidth(520)
        self.setModal(True)
        self._build()

    def _build(self) -> None:
        import platform
        import subprocess
        import sys
        import PySide6
        import yt_dlp
        from PySide6.QtGui import QPixmap
        from app.utils.ffmpeg import resolve_ffmpeg
        from app.utils.path_helper import get_asset_path

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── Header with Icon & Title ──
        header = QHBoxLayout()
        header.setSpacing(16)

        icon_label = QLabel()
        icon_path = get_asset_path("icon.png")
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(
                56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pix)
        else:
            icon_label.setText("🎬")
            icon_label.setStyleSheet("font-size: 36px;")
        header.addWidget(icon_label)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        app_title = QLabel("Video Downloader")
        app_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        app_sub = QLabel("Multi-platform Video & Audio Downloader v1.0.0")
        app_sub.setStyleSheet("font-size: 12px; color: #8890a4;")
        author_lbl = QLabel("Developed by NVK • Open Source & Authorized Media Utility")
        author_lbl.setStyleSheet("font-size: 11px; color: #5a6080;")
        title_vbox.addWidget(app_title)
        title_vbox.addWidget(app_sub)
        title_vbox.addWidget(author_lbl)
        header.addLayout(title_vbox)
        layout.addLayout(header)

        # ── Diagnostic Frame ──
        frame = QFrame()
        frame.setStyleSheet("background-color: #121422; border-radius: 8px; border: 1px solid #1e2030; padding: 6px;")
        f_layout = QVBoxLayout(frame)
        f_layout.setSpacing(8)

        # Detect components
        ffmpeg_bin = resolve_ffmpeg(getattr(self.config, "ffmpeg_path", None) if self.config else None)
        ffmpeg_status = f"✅ Available ({ffmpeg_bin.name})" if ffmpeg_bin else "⚠️ Not found (using internal)"

        items = [
            ("Core Engine", f"yt-dlp v{yt_dlp.version.__version__}"),
            ("GUI Framework", f"PySide6 v{PySide6.__version__} (Qt v{PySide6.QtCore.qVersion()})"),
            ("Python Runtime", f"v{platform.python_version()} ({platform.architecture()[0]})"),
            ("FFmpeg Status", ffmpeg_status),
            ("Operating System", f"{platform.system()} {platform.release()} ({platform.machine()})"),
        ]

        for label, val in items:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #8890a4; font-size: 12px; font-weight: 600; min-width: 120px;")
            v = QLabel(val)
            v.setStyleSheet("color: #e0e0e0; font-size: 12px;")
            row.addWidget(lbl)
            row.addWidget(v, 1)
            f_layout.addLayout(row)

        layout.addWidget(frame)

        # ── Action Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        open_dl_btn = QPushButton("📁 Downloads")
        open_dl_btn.setProperty("cssClass", "secondary")
        open_dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_dl_btn.clicked.connect(self._open_downloads)
        btn_row.addWidget(open_dl_btn)

        open_logs_btn = QPushButton("📝 Logs")
        open_logs_btn.setProperty("cssClass", "secondary")
        open_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_logs_btn.clicked.connect(self._open_logs)
        btn_row.addWidget(open_logs_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(90)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _open_downloads(self) -> None:
        import os
        from pathlib import Path
        dl = getattr(self.config, "download_path", Path("downloads"))
        dl_dir = Path(dl).expanduser().resolve()
        dl_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(dl_dir))

    def _open_logs(self) -> None:
        import os
        from pathlib import Path
        from app.utils.path_helper import get_safe_log_dir
        log_dir = get_safe_log_dir()
        os.startfile(str(log_dir))

