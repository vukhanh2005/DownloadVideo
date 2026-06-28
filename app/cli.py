"""Typer command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from app.config.settings import load_config
from app.core.exceptions import VideoDownloaderError
from app.models.download import AudioFormat, DownloadProgress, DownloadType
from app.models.quality import Quality
from app.models.video import VideoInfo
from app.services.download_service import DownloadService
from app.utils.formatting import format_bytes, format_duration
from app.utils.logging import configure_logging

app = typer.Typer(
    no_args_is_help=True,
    help="Download videos from supported social platforms.",
    pretty_exceptions_show_locals=False,
)
console = Console()


def _service(config_path: Path, verbose: bool = False) -> DownloadService:
    config = load_config(config_path)
    configure_logging(config.log_path, verbose)
    return DownloadService(config)


def _quality(value: str | None, service: DownloadService) -> Quality:
    try:
        return Quality(value or service.config.default_quality)
    except ValueError as exc:
        choices = ", ".join(item.value for item in Quality)
        raise typer.BadParameter(f"Choose one of: {choices}") from exc


def _metadata_table(items: list[VideoInfo]) -> Table:
    table = Table(title="Video information", show_lines=True)
    table.add_column("#", justify="right")
    table.add_column("Platform")
    table.add_column("Title", overflow="fold")
    table.add_column("Author")
    table.add_column("Duration")
    table.add_column("Estimated size")
    table.add_column("Qualities", overflow="fold")
    for index, item in enumerate(items, start=1):
        heights = sorted(
            {fmt.height for fmt in item.formats if fmt.height},
            reverse=True,
        )
        qualities = (
            ", ".join(f"{height}p" for height in heights[:8]) or "source dependent"
        )
        table.add_row(
            str(index),
            item.platform.value,
            item.title,
            item.author or "unknown",
            format_duration(item.duration),
            format_bytes(item.estimated_size),
            qualities,
        )
    return table


def _run_download(
    service: DownloadService,
    url: str,
    quality: Quality,
    *,
    download_type: str = "video+audio",
    audio_format: str = "mp3",
    include_playlist: bool,
) -> None:
    columns = (
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>5.1f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )
    with Progress(*columns, console=console) as progress:
        task_id = progress.add_task("Preparing", total=100)
        callback = _rich_callback(progress, task_id)
        results = service.download(
            url,
            quality,
            download_type=download_type,
            audio_format=audio_format,
            playlist=include_playlist,
            progress_callback=callback,
        )
        task = next((t for t in progress.tasks if t.id == task_id), None)
        if task and task.total:
            progress.update(task_id, completed=task.total, description="Complete")
        else:
            progress.update(task_id, completed=100, description="Complete")
    for result in results:
        console.print(f"[green]Saved:[/green] {result.path}")


def _rich_callback(progress: Progress, task_id: TaskID):
    def callback(event: DownloadProgress) -> None:
        if event.total_bytes and event.total_bytes > 0:
            progress.update(
                task_id,
                completed=event.downloaded_bytes,
                total=event.total_bytes,
                description=Path(event.filename).name if event.filename else "Downloading",
            )
        else:
            progress.update(
                task_id,
                completed=event.percent,
                total=100,
                description=Path(event.filename).name if event.filename else "Downloading",
            )

    return callback


@app.command()
def info(
    url: Annotated[str, typer.Argument(help="Video or playlist URL")],
    include_playlist: Annotated[
        bool, typer.Option("--playlist", help="Read every playlist entry")
    ] = False,
    config: Annotated[
        Path, typer.Option("--config", help="Path to config.yaml")
    ] = Path("config.yaml"),
) -> None:
    """Show metadata and available qualities without downloading."""
    try:
        console.print(
            _metadata_table(_service(config).get_info(url, playlist=include_playlist))
        )
    except VideoDownloaderError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def download(
    url: Annotated[str, typer.Argument(help="Video URL")],
    quality: Annotated[
        str | None,
        typer.Option("--quality", "-q", help="best, 1080p, 720p, 480p, or audio"),
    ] = None,
    download_type: Annotated[
        DownloadType,
        typer.Option("--type", "-t", help="video+audio, video, or audio"),
    ] = DownloadType.VIDEO_AUDIO,
    audio_format: Annotated[
        AudioFormat,
        typer.Option("--audio-format", "-a", help="mp3, wav, or ogg"),
    ] = AudioFormat.MP3,
    config: Annotated[
        Path, typer.Option("--config", help="Path to config.yaml")
    ] = Path("config.yaml"),
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Download a single video."""
    try:
        service = _service(config, verbose)
        _run_download(
            service,
            url,
            _quality(quality, service),
            download_type=download_type.value,
            audio_format=audio_format.value,
            include_playlist=False,
        )
    except VideoDownloaderError as exc:
        console.print(f"[red]Download failed:[/red] {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def playlist(
    url: Annotated[str, typer.Argument(help="Playlist URL")],
    quality: Annotated[
        str | None, typer.Option("--quality", "-q", help="Download quality")
    ] = None,
    download_type: Annotated[
        DownloadType,
        typer.Option("--type", "-t", help="video+audio, video, or audio"),
    ] = DownloadType.VIDEO_AUDIO,
    audio_format: Annotated[
        AudioFormat,
        typer.Option("--audio-format", "-a", help="mp3, wav, or ogg"),
    ] = AudioFormat.MP3,
    metadata_only: Annotated[
        bool,
        typer.Option("--metadata-only", help="Only list playlist entries"),
    ] = False,
    config: Annotated[Path, typer.Option("--config")] = Path("config.yaml"),
) -> None:
    """List or download all supported playlist entries."""
    try:
        service = _service(config)
        if metadata_only:
            console.print(_metadata_table(service.get_info(url, playlist=True)))
            return
        _run_download(
            service,
            url,
            _quality(quality, service),
            download_type=download_type.value,
            audio_format=audio_format.value,
            include_playlist=True,
        )
    except VideoDownloaderError as exc:
        console.print(f"[red]Playlist failed:[/red] {exc}")
        raise typer.Exit(code=1) from None


@app.command()
def batch(
    file: Annotated[
        Path, typer.Argument(help="Text file containing one URL per line")
    ] = Path("urls.txt"),
    quality: Annotated[str | None, typer.Option("--quality", "-q")] = None,
    download_type: Annotated[
        DownloadType,
        typer.Option("--type", "-t", help="video+audio, video, or audio"),
    ] = DownloadType.VIDEO_AUDIO,
    audio_format: Annotated[
        AudioFormat,
        typer.Option("--audio-format", "-a", help="mp3, wav, or ogg"),
    ] = AudioFormat.MP3,
    sequential: Annotated[
        bool, typer.Option("--sequential", help="Disable parallel downloads")
    ] = False,
    config: Annotated[Path, typer.Option("--config")] = Path("config.yaml"),
) -> None:
    """Download all URLs from a UTF-8 text file."""
    try:
        urls = [
            line
            for line in file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        service = _service(config)
        result = service.download_many(
            urls,
            _quality(quality, service),
            download_type=download_type.value,
            audio_format=audio_format.value,
            parallel=not sequential,
        )
    except OSError as exc:
        console.print(f"[red]Cannot read URL file:[/red] {exc}")
        raise typer.Exit(code=1) from None
    except VideoDownloaderError as exc:
        console.print(f"[red]Batch failed:[/red] {exc}")
        raise typer.Exit(code=1) from None

    console.print(
        f"[green]Completed: {result.successful_count}[/green] | "
        f"[red]Failed: {result.failed_count}[/red]"
    )
    for failed_url, message in dict(result.failures).items():
        console.print(f"[red]{failed_url}:[/red] {message}")
    if result.failures:
        raise typer.Exit(code=1)


@app.command()
def gui(
    config: Annotated[Path, typer.Option("--config")] = Path("config.yaml"),
) -> None:
    """Launch the desktop interface."""
    from app.gui import launch_gui  # pylint: disable=import-outside-toplevel

    try:
        launch_gui(config)
    except VideoDownloaderError as exc:
        console.print(f"[red]GUI failed:[/red] {exc}")
        raise typer.Exit(code=1) from None
