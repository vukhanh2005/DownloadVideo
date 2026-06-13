"""Video metadata models."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.platform import Platform


class VideoFormat(BaseModel):
    """A selectable media format reported by the extractor."""

    model_config = ConfigDict(frozen=True)

    format_id: str
    extension: str | None = None
    resolution: str | None = None
    height: int | None = None
    audio_only: bool = False
    filesize: int | None = Field(default=None, ge=0)
    note: str | None = None


class VideoInfo(BaseModel):
    """Normalized metadata independent from a source platform."""

    model_config = ConfigDict(frozen=True)

    id: str
    url: str
    platform: Platform
    title: str
    duration: float | None = Field(default=None, ge=0)
    thumbnail: str | None = None
    author: str | None = None
    estimated_size: int | None = Field(default=None, ge=0)
    formats: tuple[VideoFormat, ...] = ()
    playlist_title: str | None = None
    playlist_index: int | None = None
