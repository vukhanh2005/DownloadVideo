"""Human-readable value formatting."""


def format_bytes(value: int | float | None) -> str:
    """Format a byte count using binary units."""
    if value is None:
        return "unknown"
    size = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TiB"


def format_duration(seconds: float | None) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds is None:
        return "unknown"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
