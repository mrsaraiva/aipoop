"""Distortion effects: deep-fry, chromatic aberration, VHS, glitch blocks, etc."""

import functools
import random
import numpy as np
from PIL import Image, ImageDraw


def deep_fry(img: Image.Image, intensity: float = 1.0) -> Image.Image:
    """Deep-fry an image: oversaturate, sharpen, add noise, JPEG artifacts."""
    from PIL import ImageEnhance
    import io

    img = ImageEnhance.Contrast(img).enhance(1.5 + intensity)
    img = ImageEnhance.Color(img).enhance(1.5 + intensity * 2)
    img = ImageEnhance.Sharpness(img).enhance(2.0 + intensity * 3)

    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, 15 * intensity, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    quality = max(1, int(15 - intensity * 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    img = Image.open(buf).copy()

    return img.convert("RGB")


def chromatic_aberration(img: Image.Image, offset: int = 6) -> Image.Image:
    """Split RGB channels and offset them for a glitch look."""
    r, g, b = img.split()
    from PIL import ImageChops
    r = ImageChops.offset(r, -offset, 0)
    b = ImageChops.offset(b, offset, 0)
    return Image.merge("RGB", (r, g, b))


@functools.lru_cache(maxsize=16)
def _scanlines_mask(width: int, height: int, gap: int, alpha: int) -> np.ndarray:
    """Pre-compute a scanlines darkening factor array (cached)."""
    factor = np.ones((height, 1, 1), dtype=np.float32)
    factor[::gap, :, :] = 1.0 - alpha / 255.0
    return factor


def scanlines(img: Image.Image, gap: int = 3, alpha: int = 80) -> Image.Image:
    """Add CRT-style scanlines using cached numpy mask."""
    w, h = img.size
    factor = _scanlines_mask(w, h, gap, alpha)
    arr = np.array(img, dtype=np.float32)
    arr *= factor
    return Image.fromarray(arr.astype(np.uint8))


def pixel_sort_horizontal(img: Image.Image, threshold: int = 100) -> Image.Image:
    """Sort pixels in horizontal bands by brightness (datamosh aesthetic)."""
    arr = np.array(img)
    h, w, _ = arr.shape
    for _ in range(h // 8):
        y = random.randint(0, h - 1)
        row = arr[y]
        brightness = np.sum(row, axis=1)
        mask = brightness > threshold
        indices = np.where(mask)[0]
        if len(indices) > 2:
            start, end = indices[0], indices[-1]
            segment = row[start:end]
            order = np.argsort(np.sum(segment, axis=1))
            arr[y, start:end] = segment[order]
    return Image.fromarray(arr)


def vhs_distortion(img: Image.Image) -> Image.Image:
    """VHS-style horizontal line displacement."""
    arr = np.array(img)
    h, w, _ = arr.shape
    for y in range(h):
        if random.random() < 0.05:
            shift = random.randint(-20, 20)
            arr[y] = np.roll(arr[y], shift, axis=0)
    return Image.fromarray(arr)


def glitch_block(img: Image.Image, blocks: int = 8) -> Image.Image:
    """Copy random rectangular blocks to wrong positions."""
    arr = np.array(img)
    h, w, _ = arr.shape
    for _ in range(blocks):
        bh = random.randint(10, h // 4)
        bw = random.randint(20, w // 3)
        sy = random.randint(0, h - bh)
        sx = random.randint(0, w - bw)
        dy = random.randint(0, h - bh)
        dx = random.randint(0, w - bw)
        arr[dy:dy + bh, dx:dx + bw] = arr[sy:sy + bh, sx:sx + bw]
    return Image.fromarray(arr)


def zoom_blur(img: Image.Image, factor: float = 1.3) -> Image.Image:
    """Zoom into center with motion blur feel."""
    w, h = img.size
    nw, nh = int(w / factor), int(h / factor)
    left = (w - nw) // 2
    top = (h - nh) // 2
    cropped = img.crop((left, top, left + nw, top + nh))
    return cropped.resize((w, h), Image.Resampling.NEAREST)


def screen_shake(img: Image.Image, intensity: int = 15) -> Image.Image:
    """Randomly offset the entire image to simulate screen shake."""
    dx = random.randint(-intensity, intensity)
    dy = random.randint(-intensity, intensity)
    from PIL import ImageChops
    return ImageChops.offset(img, dx, dy)


def corruption_effect(img: Image.Image, amount: float = 0.3) -> Image.Image:
    """Randomly corrupt rectangular regions with solid colors or noise."""
    arr = np.array(img)
    h, w, _ = arr.shape
    n_corruptions = int(amount * 10)
    for _ in range(n_corruptions):
        ch = random.randint(5, h // 6)
        cw = random.randint(20, w // 2)
        cy = random.randint(0, h - ch)
        cx = random.randint(0, w - cw)
        if random.random() < 0.5:
            color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255), (0, 0, 0)])
            arr[cy:cy + ch, cx:cx + cw] = color
        else:
            arr[cy:cy + ch, cx:cx + cw] = np.random.randint(0, 255, (ch, cw, 3), dtype=np.uint8)
    return Image.fromarray(arr)


def film_grain(img: Image.Image, intensity: int = 30) -> Image.Image:
    """Add per-pixel grayscale noise for a film grain look."""
    arr = np.array(img, dtype=np.int16)
    noise = np.random.randint(-intensity, intensity + 1, (arr.shape[0], arr.shape[1], 1), dtype=np.int16)
    arr += noise
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def near_black_subliminal(img: Image.Image, brightness: float = 0.04) -> Image.Image:
    """Multiply all pixels by a tiny factor, making content barely perceptible."""
    arr = np.array(img, dtype=np.float32)
    arr *= brightness
    return Image.fromarray(arr.astype(np.uint8))


def diagonal_streaks(
    img: Image.Image,
    count: int = 5,
    color: tuple[int, int, int] = (255, 0, 180),
    alpha: float = 0.3,
) -> Image.Image:
    """Diagonal corruption lines across the frame."""
    overlay = Image.new("RGB", img.size, (0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size

    for _ in range(count):
        x_start = random.randint(-w // 2, w)
        y_start = random.randint(-h // 4, 0)
        x_end = x_start + random.randint(w // 2, w)
        y_end = y_start + h + random.randint(0, h // 4)
        width = random.randint(2, 6)
        draw.line((x_start, y_start, x_end, y_end), fill=color, width=width)

    # Alpha blend
    arr_base = np.array(img, dtype=np.float32)
    arr_over = np.array(overlay, dtype=np.float32)
    mask = arr_over.sum(axis=2, keepdims=True) > 0
    arr_base = np.where(mask, arr_base * (1 - alpha) + arr_over * alpha, arr_base)
    return Image.fromarray(arr_base.astype(np.uint8))


def heavy_crt_interlace(
    img: Image.Image, darken: float = 0.4, blur_px: int = 1
) -> Image.Image:
    """Dense scanlines with color bleed: every other row darkened + horizontal blur."""
    from PIL import ImageFilter

    arr = np.array(img, dtype=np.float32)
    # Darken odd rows
    arr[1::2] *= (1.0 - darken)
    img = Image.fromarray(arr.astype(np.uint8))

    if blur_px > 0:
        # Apply horizontal blur via box blur on each channel
        img = img.filter(ImageFilter.BoxBlur(blur_px))

    return img


def rgb_static_noise(width: int, height: int) -> Image.Image:
    """Full-frame random RGB noise (for transitions)."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(arr)


def crt_warmup_noise(width: int, height: int) -> Image.Image:
    """Green-biased CRT warm-up noise."""
    arr = np.random.randint(20, 60, (height, width, 3), dtype=np.uint8)
    # Boost green channel
    arr[:, :, 1] = np.random.randint(40, 100, (height, width), dtype=np.uint8)
    return Image.fromarray(arr)


def invert_colors(img: Image.Image) -> Image.Image:
    """Invert all colors."""
    from PIL import ImageOps
    return ImageOps.invert(img.convert("RGB"))
