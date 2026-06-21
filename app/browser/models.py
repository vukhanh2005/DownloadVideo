"""Domain models used by Browser Downloader."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class BrowserMediaType(StrEnum):
    """Media types detectable from browser network traffic."""

    VIDEO = "video"
    AUDIO = "audio"
    HLS = "hls"


class DownloadState(StrEnum):
    """Lifecycle states for a browser media download."""

    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BrowserMedia(BaseModel):
    """A normalized media resource discovered by the embedded browser."""

    model_config = ConfigDict(frozen=True)

    url: str
    media_type: BrowserMediaType
    name: str
    mime_type: str | None = None
    size: int | None = Field(default=None, ge=0)
    quality: str | None = None
    source_page: str | None = None
    referer: str | None = None
    user_agent: str | None = None
    cookies: str | None = None
    is_live: bool = False


class HlsVariant(BaseModel):
    """One selectable stream in an HLS master playlist."""

    model_config = ConfigDict(frozen=True)

    url: str
    quality: str
    bandwidth: int | None = Field(default=None, ge=0)
    codecs: str | None = None


class BrowserDownloadSnapshot(BaseModel):
    """Thread-safe value object describing a download task."""

    model_config = ConfigDict(frozen=True)

    task_id: str
    media: BrowserMedia
    destination: Path
    state: DownloadState
    percent: float = Field(default=0, ge=0, le=100)
    downloaded_bytes: int = Field(default=0, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    speed: float | None = Field(default=None, ge=0)
    eta: float | None = Field(default=None, ge=0)
    output_path: Path | None = None
    error: str | None = None
