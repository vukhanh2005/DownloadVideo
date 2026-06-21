"""PyInstaller specification for the compact Windows desktop application."""

analysis = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=[],
    datas=[("config.yaml", ".")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "black",
        "click",
        "IPython",
        "matplotlib",
        "numpy",
        "PIL",
        "pygments",
        "pylint",
        "pytest",
        "rich",
        "scipy",
        "setuptools",
        "shellingham",
        "typer",
        "wheel",
    ],
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
