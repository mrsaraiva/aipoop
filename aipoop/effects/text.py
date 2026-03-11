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


def redacted_blocks(
    img: Image.Image,
    text: str,
    positions: list[int],
    font: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Draw black rectangles over selected word indices in rendered text."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    words = text.split()
    # Measure cumulative word positions
    x_cursor = 0
    space_w = draw.textlength(" ", font=font)
    word_boxes: list[tuple[int, int, int, int]] = []
    for word in words:
        bbox = font.getbbox(word)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        word_boxes.append((x_cursor, 0, x_cursor + w, h))
        x_cursor += w + int(space_w)
    for idx in positions:
        if 0 <= idx < len(word_boxes):
            bx0, by0, bx1, by1 = word_boxes[idx]
            draw.rectangle(
                (bx0 - 2, by0 - 2, bx1 + 2, by1 + 4),
                fill=(0, 0, 0),
            )
    return img


def text_stutter(
    img: Image.Image,
    text: str,
    pos: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    offset: tuple[int, int] = (2, 1),
    colors: tuple[tuple[int, int, int], tuple[int, int, int]] = (
        (255, 0, 0),
        (0, 255, 0),
    ),
) -> Image.Image:
    """Double-print text with slight offset and contrasting colors."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    x, y = pos
    dx, dy = offset
    draw.text((x, y), text, font=font, fill=colors[0])
    draw.text((x + dx, y + dy), text, font=font, fill=colors[1])
    return img


def progressive_text_reveal(
    lines: list[str],
    progress: float,
    font: ImageFont.FreeTypeFont,
    img: Image.Image,
    corrupt_last: bool = True,
) -> Image.Image:
    """Reveal text line-by-line based on progress (0.0-1.0), optionally corrupting the last visible line."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    n_visible = int(len(lines) * progress)
    visible = lines[:n_visible]

    y = 40
    line_h = font.size + 12
    for i, line in enumerate(visible):
        display = line
        if corrupt_last and i == n_visible - 1 and progress < 1.0:
            display = text_scramble(line, amount=0.4)
        draw.text((40, y), display, font=font, fill=(0, 200, 0))
        y += line_h

    return img


def typing_cursor_reveal(
    text: str,
    char_index: int,
    img: Image.Image,
    pos: tuple[int, int],
    font: ImageFont.FreeTypeFont,
    cursor_color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Typewriter effect: show text up to char_index with blinking block cursor."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    visible = text[:char_index]
    x, y = pos

    draw.text((x, y), visible, font=font, fill=(0, 255, 0))

    # Cursor position
    if visible:
        cursor_x = x + int(draw.textlength(visible, font=font))
    else:
        cursor_x = x
    bbox = font.getbbox("█")
    cursor_h = bbox[3] - bbox[1]
    cursor_w = bbox[2] - bbox[0]

    # Blink based on char_index parity (alternates per frame)
    if char_index % 2 == 0:
        draw.rectangle(
            (cursor_x, y, cursor_x + cursor_w, y + cursor_h),
            fill=cursor_color,
        )

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
