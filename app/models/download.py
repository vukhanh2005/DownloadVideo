from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any


class DownloadType(StrEnum):
    """Target media streams to extract."""

    VIDEO_AUDIO = "video+audio"
    VIDEO_ONLY = "video"
    AUDIO_ONLY = "audio"


class AudioFormat(StrEnum):
    """Supported target audio codecs."""

    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"


class DownloadProgress(BaseModel):
    """A normalized progress event emitted while downloading."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: str
    filename: str | None = None
    downloaded_bytes: int = Field(default=0, ge=0)
    total_bytes: int | None = Field(default=None, ge=0)
    speed: float | None = Field(default=None, ge=0)
    eta: float | None = Field(default=None, ge=0)
    percent: float = Field(default=0, ge=0, le=100)

    @field_validator("downloaded_bytes", mode="before")
    @classmethod
    def _coerce_downloaded_bytes(cls, v: Any) -> int:
        if v is None:
            return 0
        try:
            return max(0, int(round(float(v))))
        except (ValueError, TypeError):
            return 0

    @field_validator("total_bytes", mode="before")
    @classmethod
    def _coerce_total_bytes(cls, v: Any) -> int | None:
        if v is None:
            return None
        try:
            return max(0, int(round(float(v))))
        except (ValueError, TypeError):
            return None

    @field_validator("percent", mode="before")
    @classmethod
    def _coerce_percent(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(val, 100.0))
        except (ValueError, TypeError):
            return 0.0

    @field_validator("speed", "eta", mode="before")
    @classmethod
    def _coerce_float(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            val = float(v)
            return max(0.0, val)
        except (ValueError, TypeError):
            return None


class DownloadResult(BaseModel):
    """Outcome for one downloaded media item."""

    model_config = ConfigDict(frozen=True)

    url: str
    title: str
    path: Path
    success: bool = True


class BatchResult(BaseModel):
    """Summary for a multi-URL download operation."""

    completed: tuple[DownloadResult, ...] = ()
    failures: dict[str, str] = Field(default_factory=dict)

    @property
    def successful_count(self) -> int:
        """Return the number of successfully downloaded items."""
        return len(self.completed)

    @property
    def failed_count(self) -> int:
        """Return the number of failed URLs."""
        return len(self.failures)
