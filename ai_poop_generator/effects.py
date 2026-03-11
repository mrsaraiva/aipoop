"""
Visual effects engine: deep-frying, glitching, and existential dread
rendered as pixel manipulation.
"""

import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try to load a monospace font, fall back to default."""
    candidates = [
        "/usr/share/fonts/google-noto/NotoSansMono-Bold.ttf" if bold
        else "/usr/share/fonts/google-noto/NotoSansMono-Regular.ttf",
        "/usr/share/fonts/liberation-mono/LiberationMono-Bold.ttf" if bold
        else "/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf",
        "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono-Bold.ttf" if bold
        else "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default(size)


def deep_fry(img: Image.Image, intensity: float = 1.0) -> Image.Image:
    """Deep-fry an image: oversaturate, sharpen, add noise, JPEG artifacts."""
    from PIL import ImageEnhance
    import io

    # Boost contrast and saturation
    img = ImageEnhance.Contrast(img).enhance(1.5 + intensity)
    img = ImageEnhance.Color(img).enhance(1.5 + intensity * 2)
    img = ImageEnhance.Sharpness(img).enhance(2.0 + intensity * 3)

    # Add noise
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, 15 * intensity, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # JPEG compression artifacts
    quality = max(1, int(15 - intensity * 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    img = Image.open(buf).copy()

    return img.convert("RGB")


def chromatic_aberration(img: Image.Image, offset: int = 6) -> Image.Image:
    """Split RGB channels and offset them for a glitch look."""
    r, g, b = img.split()
    # Shift red left, blue right
    from PIL import ImageChops
    r = ImageChops.offset(r, -offset, 0)
    b = ImageChops.offset(b, offset, 0)
    return Image.merge("RGB", (r, g, b))


def scanlines(img: Image.Image, gap: int = 3, alpha: int = 80) -> Image.Image:
    """Add CRT-style scanlines."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, img.size[1], gap):
        draw.line([(0, y), (img.size[0], y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def pixel_sort_horizontal(img: Image.Image, threshold: int = 100) -> Image.Image:
    """Sort pixels in horizontal bands by brightness (datamosh aesthetic)."""
    arr = np.array(img)
    h, w, _ = arr.shape
    # Pick random bands to sort
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
    return cropped.resize((w, h), Image.NEAREST)


def invert_colors(img: Image.Image) -> Image.Image:
    """Invert all colors."""
    from PIL import ImageOps
    return ImageOps.invert(img.convert("RGB"))


def add_text_with_shadow(
    draw: ImageDraw.Draw,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    shadow_color: tuple[int, int, int] = (0, 0, 0),
    shadow_offset: int = 3,
):
    """Draw text with a drop shadow for readability."""
    x, y = pos
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def render_text_frame(
    width: int,
    height: int,
    text: str,
    bg_color: tuple[int, int, int],
    fg_color: tuple[int, int, int],
    font_size: int = 48,
    bold: bool = False,
    align: str = "center",
) -> Image.Image:
    """Render a text frame with proper centering."""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    font = get_font(font_size, bold)

    # Calculate text bounding box
    bbox = draw.multiline_textbbox((0, 0), text, font=font, align=align)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (width - tw) // 2
    y = (height - th) // 2

    add_text_with_shadow(draw, (x, y), text, font, fg_color)
    return img


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
            # Solid color block
            color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255), (0, 0, 0)])
            arr[cy:cy + ch, cx:cx + cw] = color
        else:
            # Noise block
            arr[cy:cy + ch, cx:cx + cw] = np.random.randint(0, 255, (ch, cw, 3), dtype=np.uint8)
    return Image.fromarray(arr)


def text_scramble(text: str, amount: float = 0.3) -> str:
    """Randomly replace characters with glitch unicode."""
    glitch_chars = "̷̶̸̵̴̡̨̢̧̛̱̯̮̭̬̫̪̩̦̥̤̣̠̟̞̝̜̙̘̗̖̕̚▓░▒█▄▀■□◆◇○●"
    result = []
    for c in text:
        if c in (' ', '\n'):
            result.append(c)
        elif random.random() < amount:
            result.append(random.choice(glitch_chars))
        else:
            result.append(c)
    return "".join(result)


def apply_mood_effects(img: Image.Image, mood: str) -> Image.Image:
    """Apply visual effects based on mood."""
    match mood:
        case "calm":
            img = scanlines(img, gap=4, alpha=40)
        case "panic":
            img = chromatic_aberration(img, offset=random.randint(4, 12))
            img = vhs_distortion(img)
            if random.random() < 0.3:
                img = zoom_blur(img, 1.1)
        case "glitch":
            img = glitch_block(img, blocks=random.randint(5, 15))
            img = chromatic_aberration(img, offset=random.randint(3, 8))
            img = scanlines(img)
        case "deep_fried":
            img = deep_fry(img, intensity=random.uniform(0.8, 1.5))
        case "void":
            img = scanlines(img, gap=2, alpha=30)
            # Fade to near-black periodically
        case "scream":
            img = deep_fry(img, intensity=0.5)
            img = chromatic_aberration(img, offset=random.randint(6, 15))
            img = zoom_blur(img, random.uniform(1.05, 1.2))
        case "whisper":
            img = scanlines(img, gap=3, alpha=20)
            img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    return img
