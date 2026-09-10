"""Generate application icons (ICO and PNG) using Pillow."""

from pathlib import Path
from PIL import Image, ImageDraw


def create_app_icon(size: int = 512) -> Image.Image:
    """Draw a modern, premium video downloader app icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base rounded rectangle (squircle)
    margin = int(size * 0.05)
    radius = int(size * 0.22)
    box = (margin, margin, size - margin, size - margin)

    # Background: deep dark navy with crimson accent border
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=(24, 26, 42, 255),
        outline=(233, 69, 96, 255),
        width=max(2, int(size * 0.025)),
    )

    # Inner subtle plate
    inner_margin = int(size * 0.08)
    inner_box = (inner_margin, inner_margin, size - inner_margin, size - inner_margin)
    inner_radius = int(size * 0.18)
    draw.rounded_rectangle(inner_box, radius=inner_radius, fill=(15, 17, 26, 255))

    # 2. Downward Download Arrow / Media symbol
    cx = size // 2
    arrow_w = int(size * 0.14)
    arrow_top = int(size * 0.22)
    arrow_bot = int(size * 0.50)
    head_w = int(size * 0.26)
    head_bot = int(size * 0.63)

    # Arrow stem
    draw.rounded_rectangle(
        (cx - arrow_w // 2, arrow_top, cx + arrow_w // 2, arrow_bot),
        radius=int(arrow_w * 0.25),
        fill=(255, 90, 120, 255),
    )

    # Arrow head (triangle)
    draw.polygon(
        [
            (cx - head_w, arrow_bot - int(size * 0.02)),
            (cx + head_w, arrow_bot - int(size * 0.02)),
            (cx, head_bot),
        ],
        fill=(233, 69, 96, 255),
    )

    # 3. Base tray / dish (representing disk / storage)
    tray_y = int(size * 0.70)
    tray_h = int(size * 0.07)
    tray_w = int(size * 0.32)
    tray_thick = int(size * 0.035)

    # Bottom bar
    draw.rounded_rectangle(
        (cx - tray_w, tray_y + tray_h - tray_thick, cx + tray_w, tray_y + tray_h),
        radius=int(tray_thick * 0.5),
        fill=(255, 255, 255, 240),
    )
    # Left lip
    draw.rounded_rectangle(
        (cx - tray_w, tray_y, cx - tray_w + tray_thick, tray_y + tray_h),
        radius=int(tray_thick * 0.5),
        fill=(255, 255, 255, 240),
    )
    # Right lip
    draw.rounded_rectangle(
        (cx + tray_w - tray_thick, tray_y, cx + tray_w, tray_y + tray_h),
        radius=int(tray_thick * 0.5),
        fill=(255, 255, 255, 240),
    )

    return img


def main() -> None:
    output_dir = Path("assets")
    output_dir.mkdir(parents=True, exist_ok=True)

    base_icon = create_app_icon(512)

    # Save PNG
    png_path = output_dir / "icon.png"
    base_icon.save(png_path, format="PNG")
    print(f"Generated {png_path}")

    # Generate multi-resolution ICO
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path = output_dir / "icon.ico"
    base_icon.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"Generated {ico_path} with sizes {ico_sizes}")


if __name__ == "__main__":
    main()
