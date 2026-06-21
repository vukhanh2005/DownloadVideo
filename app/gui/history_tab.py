"""Download history tab with persistent JSON storage."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Header ──
        header = QHBoxLayout()
        heading = QLabel("📋  Download History")
        heading.setProperty("cssClass", "heading")
        header.addWidget(heading)
        header.addStretch()

        clear_button = QPushButton("🗑  Clear History")
        clear_button.setProperty("cssClass", "secondary")
        clear_button.clicked.connect(self._clear)
        header.addWidget(clear_button)
        layout.addLayout(header)

        # ── Table ──
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Title", "Saved Path", "Action"]
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        # ── Empty state ──
        self.empty_label = QLabel("No downloads yet. Your history will appear here.")
        self.empty_label.setProperty("cssClass", "status")
        self.empty_label.setStyleSheet(
            "QLabel { color: #5a6080; font-size: 13px; padding: 40px; }"
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
        visible = len(self._entries) > 0
        self.table.setVisible(visible)
        self.empty_label.setVisible(not visible)

        for entry in reversed(self._entries):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(entry.get("time", "")))
            self.table.setItem(row, 1, QTableWidgetItem(entry.get("title", "")))

            path_str = entry.get("path", "")
            path_item = QTableWidgetItem(path_str)
            path_item.setToolTip(path_str)
            self.table.setItem(row, 2, path_item)

            btn = QPushButton("📂 Open")
            btn.setProperty("cssClass", "secondary")
            btn.setToolTip("Open containing folder")
            folder = str(Path(path_str).parent) if path_str else ""
            btn.clicked.connect(
                lambda _checked=False, f=folder: self._open_folder(f)
            )
            self.table.setCellWidget(row, 3, btn)

    @Slot(str, str, str)
    def add_entry(self, title: str, path: str, timestamp: str) -> None:
        """Add a new history entry and persist."""
        self._entries.append({"time": timestamp, "title": title, "path": path})
        self._save()
        self._refresh_table()

    def _clear(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._save()
        self._refresh_table()

    @staticmethod
    def _open_folder(folder: str) -> None:
        """Open folder in Windows File Explorer."""
        if folder:
            subprocess.Popen(["explorer", folder])  # noqa: S603
