"""Tests for formatting and logging utilities."""

import logging
from pathlib import Path

from app.utils.formatting import format_bytes, format_duration
from app.utils.logging import configure_logging


def test_format_bytes() -> None:
    """Byte values use readable binary units."""
    assert format_bytes(None) == "unknown"
    assert format_bytes(512) == "512.0 B"
    assert format_bytes(1024) == "1.0 KiB"
    assert format_bytes(1024**2) == "1.0 MiB"


def test_format_duration() -> None:
    """Duration values use a stable hours-minutes-seconds representation."""
    assert format_duration(None) == "unknown"
    assert format_duration(3661.9) == "01:01:01"


def test_configure_logging_creates_rotating_file(tmp_path: Path) -> None:
    """Logging setup creates its parent and installs handlers once."""
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    for handler in old_handlers:
        root.removeHandler(handler)
    try:
        path = tmp_path / "nested" / "app.log"
        configure_logging(path, verbose=True)
        logging.getLogger("test").info("hello")
        assert path.exists()
        handler_count = len(root.handlers)
        configure_logging(path)
        assert len(root.handlers) == handler_count
    finally:
        for handler in root.handlers[:]:
            handler.close()
            root.removeHandler(handler)
        for handler in old_handlers:
            root.addHandler(handler)
