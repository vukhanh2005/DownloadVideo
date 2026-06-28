"""Download history tab with persistent JSON storage."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

HISTORY_FILE = Path("downloads/history.json")


class HistoryTab(QWidget):
    """Display download history from a persistent JSON file."""

    def __init__(self) -> None:
        super().__init__()
        self._entries: list[dict[str, str]] = []
        self._build()
        self._load()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # ── Header ──
        header = QHBoxLayout()
        heading = QLabel("📋  Download History")
        heading.setProperty("cssClass", "heading")
        header.addWidget(heading)
        header.addStretch()

        self.count_label = QLabel("")
        self.count_label.setProperty("cssClass", "status")
        header.addWidget(self.count_label)

        clear_button = QPushButton("🗑  Clear")
        clear_button.setProperty("cssClass", "secondary")
        clear_button.setFixedWidth(80)
        clear_button.clicked.connect(self._clear)
        header.addWidget(clear_button)
        layout.addLayout(header)

        # ── Table: 3 columns — compact for small screens ──
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Video", "Time", ""])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        # Column 0: Video title — stretch to fill
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        # Column 1: Time — fixed compact width
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(1, 130)
        # Column 2: Actions — fixed compact width
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(2, 70)

        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(True)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(
            "QTableWidget { border: 1px solid #1e2030; border-radius: 6px; }"
            "QTableWidget::item { padding: 6px 8px; border-bottom: 1px solid #1a1c2e; }"
        )
        layout.addWidget(self.table, 1)

        # ── Empty state ──
        self.empty_label = QLabel(
            "📭  No downloads yet\nYour history will appear here after saving a video."
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            "QLabel { color: #5a6080; font-size: 13px; padding: 30px; }"
        )
        layout.addWidget(self.empty_label)

    def _load(self) -> None:
        """Load history from JSON file."""
        if HISTORY_FILE.exists():
            try:
                data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._entries = data
            except (json.JSONDecodeError, OSError):
                self._entries = []
        self._refresh_table()

    def _save(self) -> None:
        """Persist history to JSON file."""
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _refresh_table(self) -> None:
        """Rebuild table rows from entries (newest first)."""
        self.table.setRowCount(0)
        has_data = len(self._entries) > 0
        self.table.setVisible(has_data)
        self.empty_label.setVisible(not has_data)
        self.count_label.setText(f"{len(self._entries)} videos" if has_data else "")

        for entry in reversed(self._entries):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Column 0: Title + path below it
            title = entry.get("title", "Unknown")
            path_str = entry.get("path", "")
            filename = Path(path_str).name if path_str else ""

            title_item = QTableWidgetItem(f"{title}\n📁 {filename}")
            title_item.setToolTip(f"Full path: {path_str}")
            title_item.setForeground(QColor("#d0d4e0"))
            self.table.setItem(row, 0, title_item)

            # Column 1: Time (compact)
            time_str = entry.get("time", "")
            # Show just date + time without seconds if possible
            short_time = time_str[:16] if len(time_str) > 16 else time_str
            time_item = QTableWidgetItem(short_time)
            time_item.setForeground(QColor("#6a7090"))
            time_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            self.table.setItem(row, 1, time_item)

            # Column 2: Open folder button
            btn = QPushButton("Open")
            btn.setToolTip(f"Open folder: {Path(path_str).parent}" if path_str else "")
            btn.setStyleSheet(
                "QPushButton { "
                "  background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #2ecc71, stop:1 #27ae60); "
                "  color: #fff; border: none; border-radius: 4px; "
                "  font-weight: 600; font-size: 11px; padding: 4px 8px; "
                "}"
                "QPushButton:hover { "
                "  background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #3ddb80, stop:1 #2ecc71); "
                "}"
            )
            btn.setFixedSize(52, 28)
            folder = str(Path(path_str).parent) if path_str else ""
            btn.clicked.connect(
                lambda _checked=False, f=folder: self._open_folder(f)
            )
            self.table.setCellWidget(row, 2, btn)

    @Slot(str, str, str)
    def add_entry(self, title: str, path: str, timestamp: str) -> None:
        """Add a new history entry and persist."""
        self._entries.append({"time": timestamp, "title": title, "path": path})
        self._save()
        self._refresh_table()

    def _clear(self) -> None:
        """Clear all history after confirmation."""
        if not self._entries:
            return
        reply = QMessageBox.question(
            self,
            "Clear History",
            f"Delete all {len(self._entries)} history entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._entries.clear()
            self._save()
            self._refresh_table()

    @staticmethod
    def _open_folder(folder: str) -> None:
        """Open folder in Windows File Explorer."""
        if folder:
            subprocess.Popen(["explorer", folder])  # noqa: S603
