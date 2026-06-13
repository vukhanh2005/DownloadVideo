"""Locate an FFmpeg executable for yt-dlp post-processing."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import imageio_ffmpeg

from app.core.exceptions import ConfigurationError


def resolve_ffmpeg(configured_path: Path | None = None) -> Path | None:
    """Return a usable FFmpeg binary from config, PATH, or the bundled wheel."""
    if configured_path is not None:
        candidate = configured_path.expanduser()
        if candidate.is_dir():
            executable = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
            candidate = candidate / executable
        if not candidate.is_file():
            raise ConfigurationError(f"Configured FFmpeg was not found: {candidate}")
        return candidate.resolve()

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return Path(system_ffmpeg).resolve()

    try:
        bundled = Path(imageio_ffmpeg.get_ffmpeg_exe())
    except RuntimeError:
        return None
    if bundled.is_file():
        return bundled.resolve()
    return None
