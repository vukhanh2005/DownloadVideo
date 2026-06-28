"""yt-dlp based downloader adapter."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadError

from app.core.exceptions import (
    DownloadFailedError,
    GeoRestrictedError,
    MetadataError,
    NetworkError,
    PrivateVideoError,
    VideoUnavailableError,
)
from app.core.protocols import ProgressCallback
from app.downloaders.base import BaseDownloader
from app.models.download import DownloadProgress, DownloadResult
from app.models.quality import Quality
from app.models.video import VideoFormat, VideoInfo
from app.utils.ffmpeg import resolve_ffmpeg

LOGGER = logging.getLogger(__name__)

COMPATIBLE_VIDEO = "bv*[ext=mp4][vcodec^=avc1]"
COMPATIBLE_AUDIO = "ba[ext=m4a]"

FORMAT_SELECTORS: dict[Quality, str] = {
    Quality.BEST: (
        f"{COMPATIBLE_VIDEO}+{COMPATIBLE_AUDIO}/"
        "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"
    ),
    Quality.P1080: (
        f"{COMPATIBLE_VIDEO}[height<=1080]+{COMPATIBLE_AUDIO}/"
        "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/"
        "b[ext=mp4][height<=1080]/bv*[height<=1080]+ba/b[height<=1080]"
    ),
    Quality.P720: (
        f"{COMPATIBLE_VIDEO}[height<=720]+{COMPATIBLE_AUDIO}/"
        "bv*[ext=mp4][height<=720]+ba[ext=m4a]/"
        "b[ext=mp4][height<=720]/bv*[height<=720]+ba/b[height<=720]"
    ),
    Quality.P480: (
        f"{COMPATIBLE_VIDEO}[height<=480]+{COMPATIBLE_AUDIO}/"
        "bv*[ext=mp4][height<=480]+ba[ext=m4a]/"
        "b[ext=mp4][height<=480]/bv*[height<=480]+ba/b[height<=480]"
    ),
    Quality.AUDIO: "ba/b",
}

VIDEO_ONLY_SELECTORS: dict[Quality, str] = {
    Quality.BEST: (
        f"{COMPATIBLE_VIDEO}/"
        "bv*[ext=mp4]/bv*/b"
    ),
    Quality.P1080: (
        f"{COMPATIBLE_VIDEO}[height<=1080]/"
        "bv*[ext=mp4][height<=1080]/"
        "bv*[height<=1080]/b[height<=1080]"
    ),
    Quality.P720: (
        f"{COMPATIBLE_VIDEO}[height<=720]/"
        "bv*[ext=mp4][height<=720]/"
        "bv*[height<=720]/b[height<=720]"
    ),
    Quality.P480: (
        f"{COMPATIBLE_VIDEO}[height<=480]/"
        "bv*[ext=mp4][height<=480]/"
        "bv*[height<=480]/b[height<=480]"
    ),
    Quality.AUDIO: "ba/b",
}


class _YtDlpLogger:
    """Bridge yt-dlp's logger contract to standard logging."""

    def debug(self, message: str) -> None:
        """Forward diagnostic output at the appropriate log level."""
        if not message.startswith("[debug] "):
            LOGGER.info(message)
        else:
            LOGGER.debug(message)

    def info(self, message: str) -> None:
        """Forward an informational message."""
        LOGGER.info(message)

    def warning(self, message: str) -> None:
        """Forward a warning message."""
        LOGGER.warning(message)

    def error(self, message: str) -> None:
        """Forward an error message."""
        LOGGER.error(message)


class YtDlpDownloader(BaseDownloader):
    """Download and normalize media through yt-dlp."""

    def get_info(self, url: str, *, playlist: bool = False) -> list[VideoInfo]:
        """Extract normalized metadata without downloading media."""
        options = self._base_options(playlist=playlist)
        options.update({"skip_download": True, "quiet": True})
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                raw = ydl.extract_info(url, download=False)
        except DownloadError as exc:
            raise self._map_error(exc, metadata=True) from exc
        except OSError as exc:
            raise MetadataError(f"Cannot retrieve metadata: {exc}") from exc
        return [self._to_video_info(item, url) for item in self._entries(raw)]

    def download(
        self,
        url: str,
        quality: str,
        *,
        download_type: str = "video+audio",
        audio_format: str = "mp3",
        playlist: bool = False,
        progress_callback: ProgressCallback | None = None,
    ) -> list[DownloadResult]:
        """Download media with retries, progress callbacks, and resume support."""
        try:
            preset = Quality(quality)
        except ValueError as exc:
            raise DownloadFailedError(f"Unsupported quality: {quality}") from exc

        is_audio = download_type == "audio" or preset is Quality.AUDIO
        is_video_only = download_type == "video"

        if is_audio:
            format_spec = "ba/b"
        elif is_video_only:
            format_spec = VIDEO_ONLY_SELECTORS.get(preset, FORMAT_SELECTORS[preset])
        else:
            format_spec = FORMAT_SELECTORS[preset]

        options = self._base_options(playlist=playlist)
        options.update(
            {
                "format": format_spec,
                "continuedl": True,
                "nopart": False,
                "overwrites": False,
                "progress_hooks": [self._progress_hook(progress_callback)],
            }
        )
        if is_audio:
            codec = "vorbis" if audio_format == "ogg" else audio_format
            options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": codec,
                    "preferredquality": "192",
                }
            ]

        LOGGER.info(
            "download start | platform=%s | url=%s | quality=%s",
            self.platform,
            url,
            preset,
        )
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                raw = ydl.extract_info(url, download=True)
                results = [
                    self._to_download_result(item, url, ydl)
                    for item in self._entries(raw)
                ]
        except DownloadError as exc:
            LOGGER.exception("download failed | url=%s", url)
            raise self._map_error(exc, metadata=False) from exc
        except OSError as exc:
            LOGGER.exception("download failed | url=%s", url)
            raise DownloadFailedError(f"Cannot write downloaded media: {exc}") from exc
        LOGGER.info("download complete | url=%s | items=%d", url, len(results))
        return results

    def _base_options(self, *, playlist: bool) -> dict[str, Any]:
        output = str(self.config.download_path / self.config.output_template)
        options: dict[str, Any] = {
            "logger": _YtDlpLogger(),
            "outtmpl": {"default": output},
            "noplaylist": not playlist,
            "ignoreerrors": False,
            "retries": self.config.retries,
            "fragment_retries": self.config.fragment_retries,
            "socket_timeout": self.config.socket_timeout,
            "concurrent_fragment_downloads": self.config.concurrent_fragments,
            "windowsfilenames": True,
            "restrictfilenames": False,
            "merge_output_format": "mp4",
            "js_runtimes": {"node": {}, "deno": {}, "quickjs": {}, "bun": {}},
            "remote_components": {"ejs:github"},
        }
        ffmpeg_path = resolve_ffmpeg(self.config.ffmpeg_path)
        if ffmpeg_path:
            options["ffmpeg_location"] = str(ffmpeg_path)
        # Browser cookies take priority (always fresh); fall back to manual file.
        if self.config.cookies_from_browser:
            options["cookiesfrombrowser"] = (self.config.cookies_from_browser,)
        elif self.config.cookies_file:
            options["cookiefile"] = str(self.config.cookies_file)
        return options

    @staticmethod
    def _entries(raw: dict[str, Any] | None) -> Iterable[dict[str, Any]]:
        if not raw:
            return ()
        entries = raw.get("entries")
        if entries is None:
            return (raw,)
        return (entry for entry in entries if entry)

    def _to_video_info(self, raw: dict[str, Any], fallback_url: str) -> VideoInfo:
        formats = tuple(
            VideoFormat(
                format_id=str(item.get("format_id", "")),
                extension=item.get("ext"),
                resolution=item.get("resolution"),
                height=item.get("height"),
                audio_only=item.get("vcodec") == "none",
                filesize=item.get("filesize") or item.get("filesize_approx"),
                note=item.get("format_note"),
            )
            for item in raw.get("formats", ())
            if item.get("format_id")
        )
        estimated_size = max(
            (item.filesize for item in formats if item.filesize is not None),
            default=None,
        )
        return VideoInfo(
            id=str(raw.get("id", "")),
            url=raw.get("webpage_url") or raw.get("original_url") or fallback_url,
            platform=self.platform,
            title=raw.get("title") or "Untitled video",
            duration=raw.get("duration"),
            thumbnail=raw.get("thumbnail"),
            author=raw.get("uploader") or raw.get("channel") or raw.get("creator"),
            estimated_size=estimated_size,
            formats=formats,
            playlist_title=raw.get("playlist_title") or raw.get("playlist"),
            playlist_index=raw.get("playlist_index"),
        )

    @staticmethod
    def _to_download_result(
        raw: dict[str, Any], fallback_url: str, ydl: yt_dlp.YoutubeDL
    ) -> DownloadResult:
        path = YtDlpDownloader._downloaded_path(raw, ydl)
        return DownloadResult(
            url=raw.get("webpage_url") or fallback_url,
            title=raw.get("title") or path.stem,
            path=path,
        )

    @staticmethod
    def _downloaded_path(raw: dict[str, Any], ydl: yt_dlp.YoutubeDL) -> Path:
        requested = raw.get("requested_downloads") or ()
        candidates = [
            item.get("filepath") or item.get("_filename") for item in requested if item
        ]
        candidates.extend([raw.get("filepath"), raw.get("_filename")])
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return Path(candidate)
        return Path(ydl.prepare_filename(raw))

    @staticmethod
    def _progress_hook(
        callback: ProgressCallback | None,
    ) -> Any:
        def hook(data: dict[str, Any]) -> None:
            if callback is None:
                return
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = int(data.get("downloaded_bytes") or 0)
            percent = min((downloaded / total * 100) if total else 0, 100)
            if data.get("status") == "finished":
                percent = 100
            callback(
                DownloadProgress(
                    status=data.get("status", "downloading"),
                    filename=data.get("filename"),
                    downloaded_bytes=downloaded,
                    total_bytes=total,
                    speed=data.get("speed"),
                    eta=data.get("eta"),
                    percent=percent,
                )
            )

        return hook

    @staticmethod
    def _map_error(error: Exception, *, metadata: bool) -> Exception:
        message = str(error)
        lowered = message.lower()
        if any(
            token in lowered for token in ("private video", "login required", "sign in")
        ):
            return PrivateVideoError(
                "This video requires authentication. Configure cookies_file with a "
                "Netscape-format cookies file."
            )
        if any(
            token in lowered
            for token in ("geo", "not available in your country", "region")
        ):
            return GeoRestrictedError("This video is restricted in your region.")
        if any(
            token in lowered
            for token in (
                "video unavailable",
                "has been removed",
                "deleted",
                "does not exist",
            )
        ):
            return VideoUnavailableError("The video was removed or is unavailable.")
        if any(
            token in lowered
            for token in ("timed out", "unable to download", "connection", "network")
        ):
            return NetworkError(
                "A network error occurred. The next run will resume partial downloads."
            )
        if "ffmpeg is not installed" in lowered or "ffmpeg not found" in lowered:
            return DownloadFailedError(
                "FFmpeg is required to merge this quality. Reinstall the application "
                "or configure ffmpeg_path in config.yaml."
            )
        exception_type = MetadataError if metadata else DownloadFailedError
        return exception_type(message)
