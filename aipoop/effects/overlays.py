"""Overlay effects: HUD elements, borders, banners, surveillance grids."""

from PIL import Image, ImageDraw

from .text import get_font


def vhs_rec_overlay(
    img: Image.Image, frame_number: int, fps: int = 30
) -> Image.Image:
    """Red dot + REC + running timecode overlay in top-left corner."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    font = get_font(24)

    # Blinking red dot (visible 2/3 of the time)
    x, y = 30, 30
    half_fps = max(fps // 2, 1)
    if (frame_number // half_fps) % 3 != 0:
        draw.ellipse((x, y, x + 16, y + 16), fill=(255, 0, 0))

    # REC text
    draw.text((x + 24, y - 2), "REC", font=font, fill=(255, 0, 0))

    # Timecode HH:MM:SS
    total_seconds = frame_number / fps
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    timecode = f"{h:02d}:{m:02d}:{s:02d}"
    draw.text((x + 80, y - 2), timecode, font=font, fill=(255, 255, 255))

    return img


def crt_border_brackets(
    img: Image.Image,
    color: tuple[int, int, int] = (0, 255, 255),
    margin: int = 40,
    length: int = 60,
) -> Image.Image:
    """L-shaped corner brackets simulating CRT viewfinder overlay."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    lw = 2  # line width

    corners = [
        # top-left
        ((margin, margin), (margin + length, margin)),
        ((margin, margin), (margin, margin + length)),
        # top-right
        ((w - margin - length, margin), (w - margin, margin)),
        ((w - margin, margin), (w - margin, margin + length)),
        # bottom-left
        ((margin, h - margin), (margin + length, h - margin)),
        ((margin, h - margin - length), (margin, h - margin)),
        # bottom-right
        ((w - margin - length, h - margin), (w - margin, h - margin)),
        ((w - margin, h - margin - length), (w - margin, h - margin)),
    ]
    for start, end in corners:
        draw.line((start, end), fill=color, width=lw)

    return img


def classification_header_banner(
    img: Image.Image,
    text: str = "TS//SCI//NEURAL",
    height: int = 40,
) -> Image.Image:
    """Dark banner at top of frame with classification text."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, _ = img.size
    font = get_font(20, bold=True)

    draw.rectangle((0, 0, w, height), fill=(0, 0, 0))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (w - tw) // 2
    y = (height - (bbox[3] - bbox[1])) // 2
    draw.text((x, y), text, font=font, fill=(255, 200, 0))

    return img


def military_hud(
    img: Image.Image,
    cx: int,
    cy: int,
    radius: int = 200,
) -> Image.Image:
    """Concentric circles + crosshair + coordinate readouts."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    font = get_font(16)
    color = (0, 255, 0)

    # Concentric circles
    for r in (radius, radius * 2 // 3, radius // 3):
        draw.arc(
            (cx - r, cy - r, cx + r, cy + r),
            0, 360, fill=color, width=1,
        )

    # Crosshair lines
    draw.line((cx - radius, cy, cx + radius, cy), fill=color, width=1)
    draw.line((cx, cy - radius, cx, cy + radius), fill=color, width=1)

    # Tick marks on crosshair
    step = max(radius // 3, 1)
    for i in range(-radius, radius + 1, step):
        if i == 0:
            continue
        draw.line((cx + i, cy - 5, cx + i, cy + 5), fill=color, width=1)
        draw.line((cx - 5, cy + i, cx + 5, cy + i), fill=color, width=1)

    # Coordinate readouts at corners
    draw.text((cx + radius + 8, cy - 8), f"X:{cx}", font=font, fill=color)
    draw.text((cx - 8, cy + radius + 8), f"Y:{cy}", font=font, fill=color)

    return img


def surveillance_grid(
    img: Image.Image,
    rows: int = 4,
    cols: int = 4,
    color: tuple[int, int, int] = (0, 180, 0),
) -> Image.Image:
    """Grid overlay with target dots at intersections."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font = get_font(12)

    cell_w = w // cols
    cell_h = h // rows

    # Grid lines
    for r in range(1, rows):
        y = r * cell_h
        draw.line((0, y, w, y), fill=color, width=1)
    for c in range(1, cols):
        x = c * cell_w
        draw.line((x, 0, x, h), fill=color, width=1)

    # Target dots at intersections
    dot_r = 4
    for r in range(1, rows):
        for c in range(1, cols):
            x, y = c * cell_w, r * cell_h
            draw.ellipse(
                (x - dot_r, y - dot_r, x + dot_r, y + dot_r),
                fill=color,
            )

    # Cell labels
    for r in range(rows):
        for c in range(cols):
            label = f"{chr(65 + r)}{c + 1}"
            draw.text(
                (c * cell_w + 4, r * cell_h + 4),
                label, font=font, fill=color,
            )

    return img
