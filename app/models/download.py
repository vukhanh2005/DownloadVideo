"""Download status and result models."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


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
