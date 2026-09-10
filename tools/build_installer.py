"""Automated 1-click build script for Video Downloader Desktop App and Setup Installer."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def ensure_icons() -> None:
    """Ensure icon assets are generated."""
    icon_ico = ROOT_DIR / "assets" / "icon.ico"
    icon_png = ROOT_DIR / "assets" / "icon.png"
    if not (icon_ico.exists() and icon_png.exists()):
        print("[1/4] Generating application icons...")
        subprocess.run([sys.executable, str(ROOT_DIR / "tools" / "generate_icon.py")], check=True)
    else:
        print("[1/4] Application icons already exist.")


def build_pyinstaller() -> None:
    """Build the PySide6 onedir application folder using PyInstaller."""
    print("[2/4] Building desktop application bundle with PyInstaller...")
    spec_path = ROOT_DIR / "VideoDownloader.spec"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_path),
    ]
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)

    folder_exe = ROOT_DIR / "dist" / "VideoDownloader_Folder" / "VideoDownloader.exe"
    if not folder_exe.exists():
        raise RuntimeError(f"PyInstaller build failed: {folder_exe} does not exist.")
    print(f"       -> PyInstaller build success: {folder_exe}")


def find_or_install_inno_setup() -> Path:
    """Locate ISCC.exe or install Inno Setup automatically via winget."""
    print("[3/4] Locating Inno Setup Compiler (ISCC.exe)...")

    which_iscc = shutil.which("iscc")
    if which_iscc:
        return Path(which_iscc)

    common_paths = [
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 7" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Inno Setup 7" / "ISCC.exe",
        Path(os.environ.get("LocalAppData", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]

    for cand in common_paths:
        if cand.exists():
            print(f"       -> Found Inno Setup: {cand}")
            return cand

    print("       -> Inno Setup not found. Attempting installation via winget...")
    try:
        subprocess.run(
            [
                "winget",
                "install",
                "JRSoftware.InnoSetup",
                "-e",
                "--silent",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ],
            check=True,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        print(f"Warning: winget install encountered an issue: {exc}")

    # Re-check paths after install
    for cand in common_paths:
        if cand.exists():
            print(f"       -> Installed and found Inno Setup: {cand}")
            return cand

    raise RuntimeError(
        "Could not find or automatically install Inno Setup. "
        "Please install Inno Setup manually from https://jrsoftware.org/isdl.php"
    )


def compile_installer(iscc_path: Path) -> Path:
    """Compile installer.iss using ISCC.exe."""
    print("[4/4] Compiling Windows Setup Installer with Inno Setup...")
    iss_file = ROOT_DIR / "installer.iss"
    cmd = [str(iscc_path), str(iss_file)]
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)

    setup_exe = ROOT_DIR / "dist" / "VideoDownloader_Setup_v1.0.0.exe"
    if not setup_exe.exists():
        raise RuntimeError(f"Installer compilation failed: {setup_exe} not found.")

    size_mb = setup_exe.stat().st_size / (1024 * 1024)
    print("\n========================================================")
    print("SUCCESS: Windows Setup Installer created successfully!")
    print(f"Installer Path : {setup_exe}")
    print(f"Installer Size : {size_mb:.2f} MB")
    print("========================================================")
    return setup_exe


def main() -> None:
    ensure_icons()
    build_pyinstaller()
    iscc_path = find_or_install_inno_setup()
    compile_installer(iscc_path)


if __name__ == "__main__":
    main()
