"""Windows desktop executable entry point."""

from pathlib import Path
import shutil
import sys

from app.gui import launch_gui
from app.utils.path_helper import get_app_data_dir, is_directory_writable


def _resolve_desktop_config() -> Path:
    """Find or initialize a writable config.yaml for the desktop application."""
    # 1. If running locally with writable local config.yaml
    local_cfg = Path("config.yaml")
    if local_cfg.exists() and is_directory_writable(local_cfg.parent):
        return local_cfg

    # 2. Check user AppData config
    app_data_dir = get_app_data_dir()
    app_data_cfg = app_data_dir / "config.yaml"
    if app_data_cfg.exists():
        return app_data_cfg

    # 3. Seed AppData config from bundled template if available
    bundled_candidates = [
        Path(sys.executable).parent / "config.yaml",
        Path(sys.executable).parent / "_internal" / "config.yaml",
        Path(__file__).resolve().parent / "config.yaml",
    ]
    for candidate in bundled_candidates:
        if candidate.exists():
            try:
                shutil.copy2(candidate, app_data_cfg)
                return app_data_cfg
            except OSError:
                pass

    return app_data_cfg


if __name__ == "__main__":
    launch_gui(_resolve_desktop_config())

