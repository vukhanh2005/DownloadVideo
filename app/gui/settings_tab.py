"""Settings tab – browse and save all runtime configuration options."""

from __future__ import annotations

from pathlib import Path

import yaml
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import AppConfig, load_config
from app.utils import get_initial_save_dir, set_last_save_dir

# (label shown in UI, yt-dlp browser key)
BROWSER_CHOICES: list[tuple[str, str | None]] = [
    ("Disabled (do not auto-extract)", None),
    ("🌐  Chrome", "chrome"),
    ("🌐  Chromium", "chromium"),
    ("🦊  Firefox", "firefox"),
    ("🔵  Edge", "edge"),
    ("🦁  Brave", "brave"),
    ("🎭  Opera", "opera"),
    ("🌸  Vivaldi", "vivaldi"),
]


class _PathRow(QWidget):
    """A line-edit + browse button row for file/folder paths."""

    changed = Signal(str)

    def __init__(
        self,
        placeholder: str = "",
        *,
        dialog_title: str = "Select file",
        file_filter: str = "All files (*.*)",
        directory: bool = False,
    ) -> None:
        super().__init__()
        self._dir = directory
        self._dialog_title = dialog_title
        self._file_filter = file_filter

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.textChanged.connect(self.changed.emit)
        row.addWidget(self.edit, 1)

        browse = QPushButton("📂")
        browse.setFixedWidth(34)
        browse.setToolTip("Browse…")
        browse.setProperty("cssClass", "secondary")
        browse.clicked.connect(self._browse)
        row.addWidget(browse)

        clear = QPushButton("✕")
        clear.setFixedWidth(28)
        clear.setToolTip("Clear")
        clear.setProperty("cssClass", "secondary")
        clear.clicked.connect(lambda: self.edit.clear())
        row.addWidget(clear)

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, value: str) -> None:  # noqa: N802
        self.edit.setText(value)

    def _browse(self) -> None:
        current = self.edit.text().strip()
        if current and Path(current).exists():
            initial_dir = Path(current) if self._dir else Path(current).parent
        else:
            initial_dir = get_initial_save_dir()

        if self._dir:
            path = QFileDialog.getExistingDirectory(
                self, self._dialog_title, str(initial_dir)
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                self._dialog_title,
                str(initial_dir),
                self._file_filter,
            )
        if path:
            set_last_save_dir(path)
            self.edit.setText(path)


class SettingsTab(QWidget):
    """UI panel for editing and saving config.yaml settings."""

    # Emitted when the user saves so other tabs can reload their service
    config_saved = Signal(object)  # AppConfig

    def __init__(self, config: AppConfig, config_path: Path = Path("config.yaml")) -> None:
        super().__init__()
        self.config = config
        self.config_path = config_path
        self._build()
        self._populate()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable area so small windows don't clip content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(self._auth_group())
        layout.addWidget(self._paths_group())
        layout.addWidget(self._network_group())
        layout.addWidget(self._output_group())
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # ── Bottom save bar ──
        bar = QWidget()
        bar.setStyleSheet(
            "QWidget { background: #0d0f18; border-top: 1px solid #1e2030; }"
        )
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 8, 16, 8)
        bar_layout.setSpacing(10)

        self._status = QLabel("")
        self._status.setProperty("cssClass", "status")
        bar_layout.addWidget(self._status, 1)

        reset_btn = QPushButton("↺  Reset")
        reset_btn.setProperty("cssClass", "secondary")
        reset_btn.setFixedWidth(90)
        reset_btn.setToolTip("Reload values from config.yaml")
        reset_btn.clicked.connect(self._populate)
        bar_layout.addWidget(reset_btn)

        save_btn = QPushButton("💾  Save")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._save)
        bar_layout.addWidget(save_btn)

        outer.addWidget(bar)

    # ── Group builders ─────────────────────────────────────────────────────

    def _auth_group(self) -> QGroupBox:
        box = QGroupBox("🔐  Authentication")
        form = QFormLayout(box)
        form.setSpacing(10)
        form.setContentsMargins(12, 16, 12, 12)

        # ── Auto-extract from browser ──────────────────────────────────────
        self.browser_combo = QComboBox()
        for label, _ in BROWSER_CHOICES:
            self.browser_combo.addItem(label)
        self.browser_combo.setToolTip(
            "Let yt-dlp read cookies directly from your installed browser.\n"
            "The browser must be closed or its cookie DB unlocked."
        )
        self.browser_combo.currentIndexChanged.connect(self._on_browser_changed)
        form.addRow("Auto-extract from", self.browser_combo)

        self._browser_status = QLabel("")
        self._browser_status.setStyleSheet("QLabel { color: #6a7090; font-size: 11px; }")
        self._browser_status.setWordWrap(True)
        form.addRow("", self._browser_status)

        # ── Manual cookies file ────────────────────────────────────────────
        self.cookies_row = _PathRow(
            placeholder="Leave empty to skip (not required for public videos)",
            dialog_title="Select Netscape cookies file",
            file_filter="Cookies files (*.txt);;All files (*.*)",
        )
        self.cookies_row.edit.setEnabled(True)
        form.addRow("Manual cookies file", self.cookies_row)

        hint = QLabel(
            "Manual file is used only when <b>Auto-extract</b> is <i>Disabled</i>.<br>"
            "Export with the <b>\"Get cookies.txt LOCALLY\"</b> extension (Chrome / Firefox)."
        )
        hint.setStyleSheet("QLabel { color: #6a7090; font-size: 11px; }")
        hint.setWordWrap(True)
        form.addRow("", hint)

        how_btn = QPushButton("❓  How to get cookies")
        how_btn.setProperty("cssClass", "secondary")
        how_btn.setFixedWidth(160)
        how_btn.clicked.connect(self._open_cookie_guide)
        form.addRow("", how_btn)

        return box

    def _on_browser_changed(self, index: int) -> None:
        """Update status hint when browser selection changes."""
        _, key = BROWSER_CHOICES[index]
        if key is None:
            self._browser_status.setText("")
            self.cookies_row.setEnabled(True)
        else:
            self._browser_status.setText(
                f"yt-dlp will read cookies from <b>{key.title()}</b> automatically.\n"
                "Close the browser before downloading for best results."
            )
            self.cookies_row.setEnabled(False)

    def _paths_group(self) -> QGroupBox:
        box = QGroupBox("📁  Paths")
        form = QFormLayout(box)
        form.setSpacing(10)
        form.setContentsMargins(12, 16, 12, 12)

        self.download_path_row = _PathRow(
            placeholder="downloads",
            dialog_title="Select download folder",
            directory=True,
        )
        form.addRow("Download folder", self.download_path_row)

        self.ffmpeg_row = _PathRow(
            placeholder="Auto-detect (recommended)",
            dialog_title="Select ffmpeg executable",
            file_filter="ffmpeg (ffmpeg.exe);;All executables (*.exe);;All files (*.*)",
        )
        form.addRow("FFmpeg path", self.ffmpeg_row)

        return box

    def _network_group(self) -> QGroupBox:
        box = QGroupBox("🌐  Network")
        form = QFormLayout(box)
        form.setSpacing(10)
        form.setContentsMargins(12, 16, 12, 12)

        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 100)
        self.retries_spin.setSuffix(" retries")
        form.addRow("Retries", self.retries_spin)

        self.fragment_retries_spin = QSpinBox()
        self.fragment_retries_spin.setRange(0, 100)
        self.fragment_retries_spin.setSuffix(" retries")
        form.addRow("Fragment retries", self.fragment_retries_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 300)
        self.timeout_spin.setSuffix(" s")
        form.addRow("Socket timeout", self.timeout_spin)

        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 16)
        self.concurrent_spin.setSuffix(" fragments")
        form.addRow("Concurrent fragments", self.concurrent_spin)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        self.threads_spin.setSuffix(" threads")
        form.addRow("Max threads", self.threads_spin)

        return box

    def _output_group(self) -> QGroupBox:
        box = QGroupBox("🎬  Output")
        form = QFormLayout(box)
        form.setSpacing(10)
        form.setContentsMargins(12, 16, 12, 12)

        self.template_edit = QLineEdit()
        self.template_edit.setPlaceholderText("%(title).60B [%(id)s].%(ext)s")
        form.addRow("Output template", self.template_edit)

        hint = QLabel(
            "yt-dlp output template. "
            "<a href='https://github.com/yt-dlp/yt-dlp#output-template' "
            "style='color:#e94560;'>Template reference ↗</a>"
        )
        hint.setStyleSheet("QLabel { color: #6a7090; font-size: 11px; }")
        hint.setOpenExternalLinks(True)
        hint.setWordWrap(True)
        form.addRow("", hint)

        return box

    # ── Data binding ──────────────────────────────────────────────────────

    def _populate(self) -> None:
        """Load current config values into the form widgets."""
        cfg = self.config

        # Browser combo
        browser_key = cfg.cookies_from_browser
        idx = next(
            (i for i, (_, k) in enumerate(BROWSER_CHOICES) if k == browser_key), 0
        )
        self.browser_combo.setCurrentIndex(idx)
        self._on_browser_changed(idx)  # refresh status + enabled state

        self.cookies_row.setText(str(cfg.cookies_file) if cfg.cookies_file else "")
        self.download_path_row.setText(str(cfg.download_path))
        self.ffmpeg_row.setText(str(cfg.ffmpeg_path) if cfg.ffmpeg_path else "")
        self.retries_spin.setValue(cfg.retries)
        self.fragment_retries_spin.setValue(cfg.fragment_retries)
        self.timeout_spin.setValue(cfg.socket_timeout)
        self.concurrent_spin.setValue(cfg.concurrent_fragments)
        self.threads_spin.setValue(cfg.max_threads)
        self.template_edit.setText(cfg.output_template)
        self._status.setText("")

    @Slot()
    def _save(self) -> None:
        """Validate, write config.yaml, and emit the new AppConfig."""
        _, browser_key = BROWSER_CHOICES[self.browser_combo.currentIndex()]

        cookies_raw = self.cookies_row.text()
        if cookies_raw and browser_key is None:  # validate only when manual mode
            cookies_path = Path(cookies_raw)
            if not cookies_path.exists():
                QMessageBox.warning(
                    self,
                    "Cookies file not found",
                    f"The file does not exist:\n{cookies_raw}\n\n"
                    "Please select a valid cookies file or clear the field.",
                )
                return

        data: dict = {
            "download_path": self.download_path_row.text() or "downloads",
            "max_threads": self.threads_spin.value(),
            "default_quality": self.config.default_quality.value,
            "retries": self.retries_spin.value(),
            "fragment_retries": self.fragment_retries_spin.value(),
            "socket_timeout": self.timeout_spin.value(),
            "concurrent_fragments": self.concurrent_spin.value(),
            "output_template": self.template_edit.text().strip()
                or "%(title).60B [%(id)s].%(ext)s",
            "cookies_from_browser": browser_key,
            "cookies_file": (cookies_raw if browser_key is None else None) or None,
            "ffmpeg_path": self.ffmpeg_row.text() or None,
            "log_path": str(self.config.log_path),
            "browser_log_path": str(self.config.browser_log_path),
        }

        try:
            self.config_path.write_text(
                yaml.dump(data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            new_config = load_config(self.config_path)
            self.config = new_config
            self._status.setText("✅  Saved successfully")
            self.config_saved.emit(new_config)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))
            self._status.setText("❌  Save failed")

    @staticmethod
    def _open_cookie_guide() -> None:
        """Open Chrome Web Store page for the cookies extension."""
        import webbrowser
        webbrowser.open(
            "https://chromewebstore.google.com/detail/get-cookiestxt-locally/"
            "cclelndahbckbenkjhflpdbgdldlbecc"
        )
