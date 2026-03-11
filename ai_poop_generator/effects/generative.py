"""Generative effects: procedural visuals, retro GUI, parametric curves."""

import math
import random
import numpy as np
from PIL import Image, ImageDraw

from .text import get_font


def token_probability_bars(
    img: Image.Image,
    tokens_probs: list[tuple[str, float]],
    x: int = 40,
    y: int | None = None,
) -> Image.Image:
    """Horizontal bar chart of token probabilities, green-on-black style."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font = get_font(22)

    bar_height = 28
    gap = 8
    max_bar_w = w - x - 120  # leave room for percentage text
    total_h = len(tokens_probs) * (bar_height + gap)

    if y is None:
        y = (h - total_h) // 2

    for i, (token, prob) in enumerate(tokens_probs):
        cy = y + i * (bar_height + gap)
        # Token label
        label = f"{token:>10s}"
        draw.text((x, cy), label, font=font, fill=(0, 200, 0))
        # Bar
        bar_x = x + 180
        bar_w = max(0, int(prob * max_bar_w))
        green = int(100 + 155 * prob)
        draw.rectangle(
            (bar_x, cy + 2, bar_x + bar_w, cy + bar_height - 2),
            fill=(0, green, 0),
        )
        # Percentage
        pct = f"{prob * 100:.1f}%"
        draw.text((bar_x + bar_w + 8, cy), pct, font=font, fill=(0, 200, 0))

    return img


def rgb_split_text(
    img: Image.Image,
    text: str,
    pos: tuple[int, int],
    font,
    offsets: tuple[int, int] = (3, -2),
) -> Image.Image:
    """Text rendered with RGB channel splitting for glitch aesthetic."""
    w, h = img.size
    dx, dy = offsets

    # Render text in each channel color on separate layers
    red_layer = Image.new("RGB", (w, h), (0, 0, 0))
    green_layer = Image.new("RGB", (w, h), (0, 0, 0))
    blue_layer = Image.new("RGB", (w, h), (0, 0, 0))

    ImageDraw.Draw(red_layer).text(
        (pos[0] - dx, pos[1] - dy), text, font=font, fill=(255, 0, 0)
    )
    ImageDraw.Draw(green_layer).text(
        pos, text, font=font, fill=(0, 255, 0)
    )
    ImageDraw.Draw(blue_layer).text(
        (pos[0] + dx, pos[1] + dy), text, font=font, fill=(0, 0, 255)
    )

    # Combine channels via max blend
    base = np.array(img, dtype=np.uint16)
    base += np.array(red_layer, dtype=np.uint16)
    base += np.array(green_layer, dtype=np.uint16)
    base += np.array(blue_layer, dtype=np.uint16)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def spirograph_curves(
    img: Image.Image,
    params: list[tuple[float, float, float]] | None = None,
    color: tuple[int, int, int] = (0, 255, 100),
) -> Image.Image:
    """Lissajous parametric curves overlaid on image."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size

    if params is None:
        params = [
            (random.uniform(1, 5), random.uniform(1, 5), random.uniform(0, math.pi))
            for _ in range(3)
        ]

    t_values = np.linspace(0, 2 * math.pi, 500)

    for a, b, delta in params:
        xs = (np.sin(a * t_values + delta) * 0.4 + 0.5) * w
        ys = (np.sin(b * t_values) * 0.4 + 0.5) * h
        points = list(zip(xs.astype(int).tolist(), ys.astype(int).tolist()))
        if len(points) > 1:
            draw.line(points, fill=color, width=1)

    return img


def retro_gui_chrome(
    img: Image.Image,
    title: str = "UNTITLED",
    has_menu: bool = True,
) -> Image.Image:
    """Win95/98 window frame chrome drawn around the image content."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font = get_font(16, bold=True)
    small_font = get_font(14)

    # Colors (Win95 palette)
    border_light = (223, 223, 223)
    border_dark = (128, 128, 128)
    bg = (192, 192, 192)
    title_bg = (0, 0, 128)
    title_fg = (255, 255, 255)
    btn_face = (192, 192, 192)

    m = 4  # border margin
    title_h = 28
    menu_h = 24 if has_menu else 0

    # Outer border (3D bevel)
    draw.rectangle((0, 0, w - 1, h - 1), outline=border_light)
    draw.rectangle((1, 1, w - 2, h - 2), outline=border_light)
    draw.rectangle((0, 0, w - 1, h - 1), outline=border_dark)
    # Light edges (top/left)
    draw.line((0, 0, w - 1, 0), fill=border_light, width=2)
    draw.line((0, 0, 0, h - 1), fill=border_light, width=2)
    # Dark edges (bottom/right)
    draw.line((0, h - 1, w - 1, h - 1), fill=border_dark, width=2)
    draw.line((w - 1, 0, w - 1, h - 1), fill=border_dark, width=2)

    # Title bar
    draw.rectangle((m, m, w - m - 1, m + title_h), fill=title_bg)
    draw.text((m + 6, m + 4), title, font=font, fill=title_fg)

    # Window buttons (close, maximize, minimize)
    btn_w = 20
    for i, label in enumerate(["_", "□", "×"]):
        bx = w - m - (3 - i) * (btn_w + 2)
        by = m + 3
        draw.rectangle((bx, by, bx + btn_w, by + btn_w), fill=btn_face, outline=border_dark)
        draw.text((bx + 5, by + 1), label, font=small_font, fill=(0, 0, 0))

    # Menu bar
    if has_menu:
        my = m + title_h + 2
        draw.rectangle((m, my, w - m - 1, my + menu_h), fill=bg)
        menu_items = ["File", "Edit", "View", "Help"]
        mx = m + 6
        for item in menu_items:
            draw.text((mx, my + 3), item, font=small_font, fill=(0, 0, 0))
            mx += len(item) * 10 + 16

    # Status bar at bottom
    sb_h = 22
    draw.rectangle((m, h - m - sb_h, w - m - 1, h - m - 1), fill=bg, outline=border_dark)
    draw.text((m + 8, h - m - sb_h + 3), "Ready", font=small_font, fill=(0, 0, 0))

    return img


def procedural_landscape(
    img: Image.Image,
    seed: int | None = None,
    color: tuple[int, int, int] = (20, 40, 80),
) -> Image.Image:
    """Mountain silhouette + starfield overlaid on image."""
    w, h = img.size
    rng = np.random.default_rng(seed)

    arr = np.array(img, dtype=np.uint8)

    # Starfield in upper portion
    n_stars = 200
    star_x = rng.integers(0, w, n_stars)
    star_y = rng.integers(0, h * 2 // 3, n_stars)
    brightness = rng.integers(150, 256, n_stars)
    for sx, sy, b in zip(star_x, star_y, brightness):
        arr[sy, sx] = (b, b, b)

    # Mountain silhouette using cumulative random walk
    horizon = h * 2 // 3
    heights = np.zeros(w, dtype=np.float64)
    heights[0] = horizon
    steps = rng.normal(0, 3, w - 1)
    heights[1:] = heights[0] + np.cumsum(steps)
    # Smooth
    kernel_size = 30
    kernel = np.ones(kernel_size) / kernel_size
    heights = np.convolve(heights, kernel, mode="same")
    # Add peaks
    for _ in range(rng.integers(2, 6)):
        px = rng.integers(0, w)
        pw = rng.integers(40, 150)
        ph = rng.integers(50, 200)
        peak = ph * np.exp(-0.5 * ((np.arange(w) - px) / pw) ** 2)
        heights -= peak

    heights = np.clip(heights, h // 4, h - 1).astype(int)

    # Fill below mountain line with silhouette color
    for x in range(w):
        arr[heights[x]:, x] = color

    return Image.fromarray(arr)
