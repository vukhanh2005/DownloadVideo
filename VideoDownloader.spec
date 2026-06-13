"""PyInstaller specification for the Windows desktop application."""

from PyInstaller.utils.hooks import collect_all

yt_dlp_data, yt_dlp_binaries, yt_dlp_hiddenimports = collect_all("yt_dlp")
ffmpeg_data, ffmpeg_binaries, ffmpeg_hiddenimports = collect_all("imageio_ffmpeg")

analysis = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=yt_dlp_binaries + ffmpeg_binaries,
    datas=yt_dlp_data + ffmpeg_data + [("config.yaml", ".")],
    hiddenimports=yt_dlp_hiddenimports + ffmpeg_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pylint", "black"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="VideoDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
