"""Tkinter desktop interface."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.config.settings import load_config
from app.core.exceptions import VideoDownloaderError
from app.models.download import DownloadProgress
from app.models.quality import Quality
from app.services.download_service import DownloadService
from app.utils.formatting import format_bytes
from app.utils.logging import configure_logging


class DownloaderWindow:
    """Small responsive GUI backed by the application service."""

    def __init__(self, root: tk.Tk, config_path: Path) -> None:
        self.root = root
        self.config = load_config(config_path)
        configure_logging(self.config.log_path)
        self.service = DownloadService(self.config)
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()

        root.title("Multi-platform Video Downloader")
        root.geometry("720x340")
        root.minsize(620, 300)
        root.columnconfigure(1, weight=1)

        self.url = tk.StringVar()
        self.quality = tk.StringVar(value=self.config.default_quality.value)
        self.destination = tk.StringVar(value=str(self.config.download_path))
        self.status = tk.StringVar(value="Ready")
        self.progress_value = tk.DoubleVar(value=0)

        self._build()
        self.root.after(100, self._poll_events)

    def _build(self) -> None:
        padding = {"padx": 12, "pady": 8}
        ttk.Label(self.root, text="Video URL").grid(
            row=0, column=0, sticky="w", **padding
        )
        ttk.Entry(self.root, textvariable=self.url).grid(
            row=0, column=1, columnspan=2, sticky="ew", **padding
        )

        ttk.Label(self.root, text="Quality").grid(
            row=1, column=0, sticky="w", **padding
        )
        ttk.Combobox(
            self.root,
            textvariable=self.quality,
            values=[quality.value for quality in Quality],
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", **padding)

        ttk.Label(self.root, text="Save to").grid(
            row=2, column=0, sticky="w", **padding
        )
        ttk.Entry(self.root, textvariable=self.destination).grid(
            row=2, column=1, sticky="ew", **padding
        )
        ttk.Button(self.root, text="Browse", command=self._choose_directory).grid(
            row=2, column=2, **padding
        )

        self.download_button = ttk.Button(
            self.root, text="Download", command=self._start_download
        )
        self.download_button.grid(row=3, column=1, sticky="ew", **padding)
        ttk.Button(self.root, text="Show info", command=self._start_info).grid(
            row=3, column=2, **padding
        )

        ttk.Progressbar(
            self.root,
            variable=self.progress_value,
            maximum=100,
        ).grid(row=4, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Label(self.root, textvariable=self.status, wraplength=670).grid(
            row=5, column=0, columnspan=3, sticky="w", **padding
        )

    def _choose_directory(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.destination.get())
        if selected:
            self.destination.set(selected)

    def _prepare_service(self) -> DownloadService:
        destination = Path(self.destination.get()).expanduser()
        destination.mkdir(parents=True, exist_ok=True)
        config = self.config.model_copy(update={"download_path": destination})
        return DownloadService(config)

    def _start_download(self) -> None:
        if not self.url.get().strip():
            messagebox.showerror("Invalid URL", "Enter a video URL.")
            return
        self.download_button.configure(state="disabled")
        self.progress_value.set(0)
        self.status.set("Preparing download...")
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self) -> None:
        try:
            results = self._prepare_service().download(
                self.url.get(),
                Quality(self.quality.get()),
                progress_callback=lambda event: self.events.put(("progress", event)),
            )
            self.events.put(("complete", results))
        except (VideoDownloaderError, OSError, ValueError) as exc:
            self.events.put(("error", str(exc)))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            # Keep Tk alive if a third-party extractor raises an unknown error.
            self.events.put(("error", f"Unexpected error: {exc}"))

    def _start_info(self) -> None:
        if not self.url.get().strip():
            messagebox.showerror("Invalid URL", "Enter a video URL.")
            return
        self.status.set("Reading metadata...")
        threading.Thread(target=self._info_worker, daemon=True).start()

    def _info_worker(self) -> None:
        try:
            item = self._prepare_service().get_info(self.url.get())[0]
            text = (
                f"{item.title}\nAuthor: {item.author or 'unknown'}\n"
                f"Estimated size: {format_bytes(item.estimated_size)}"
            )
            self.events.put(("info", text))
        except (VideoDownloaderError, OSError, IndexError) as exc:
            self.events.put(("error", str(exc)))

    def _poll_events(self) -> None:
        try:
            while True:
                event_type, payload = self.events.get_nowait()
                if event_type == "progress":
                    event = payload
                    if isinstance(event, DownloadProgress):
                        self.progress_value.set(event.percent)
                        downloaded = format_bytes(event.downloaded_bytes)
                        speed = format_bytes(event.speed)
                        self.status.set(
                            f"{event.percent:.1f}% | {downloaded} | "
                            f"{speed}/s | ETA {event.eta or 0:.0f}s"
                        )
                elif event_type == "complete":
                    results = payload
                    self.progress_value.set(100)
                    self.status.set("Download complete")
                    self.download_button.configure(state="normal")
                    messagebox.showinfo(
                        "Complete",
                        "\n".join(str(item.path) for item in results),
                    )
                elif event_type == "info":
                    self.status.set(str(payload).replace("\n", " | "))
                    messagebox.showinfo("Video information", str(payload))
                elif event_type == "error":
                    self.status.set(str(payload))
                    self.download_button.configure(state="normal")
                    messagebox.showerror("Operation failed", str(payload))
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)


def launch_gui(config_path: Path = Path("config.yaml")) -> None:
    """Create and run the Tk desktop application."""
    root = tk.Tk()
    DownloaderWindow(root, config_path)
    root.mainloop()
