"""Text rendering utilities: fonts, outlined text, shadow text."""

import functools
import random
from PIL import Image, ImageDraw, ImageFont


@functools.lru_cache(maxsize=64)
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
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
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

    bbox = draw.multiline_textbbox((0, 0), text, font=font, align=align)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (width - tw) // 2
    y = (height - th) // 2

    add_text_with_shadow(draw, (x, y), text, font, fg_color)
    return img


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
