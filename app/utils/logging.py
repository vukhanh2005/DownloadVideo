"""Central logging setup."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_path: Path, verbose: bool = False) -> None:
    """Configure rotating file logs and concise console logs."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    if root.handlers:
        return

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if verbose:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root.addHandler(console)
