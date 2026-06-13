"""Windows desktop executable entry point."""

from pathlib import Path

from app.gui import launch_gui

if __name__ == "__main__":
    launch_gui(Path("config.yaml"))
