"""Base class for platform downloaders."""

from abc import ABC

from app.config.settings import AppConfig
from app.models.platform import Platform


class BaseDownloader(ABC):
    """Common state for concrete downloader adapters."""

    platform: Platform

    def __init__(self, config: AppConfig) -> None:
        self.config = config
