"""Email inbox segment: Win95-style email client with escalating messages."""

import os

import numpy as np
from PIL import Image, ImageDraw

from .. import constants
from ..constants import FPS
from ..content import ContentBundle
from ..effects import (
    get_font,
    scanlines,
    chromatic_aberration,
    glitch_block,
    screen_shake,
    film_grain,
    retro_gui_chrome,
    text_scramble,
)
from ..audio import generate_mood_audio


# ── Win95 color palette ─────────────────────────────────────────────────

BG = (192, 192, 192)
LIST_BG = (255, 255, 255)
PREVIEW_BG = (255, 255, 255)
SELECTED_BG = (0, 0, 128)
SELECTED_FG = (255, 255, 255)
TEXT_COLOR = (0, 0, 0)
HEADER_BG = (0, 0, 128)
HEADER_FG = (255, 255, 255)
DIVIDER = (128, 128, 128)
UNREAD_COLOR = (0, 0, 0)
READ_COLOR = (100, 100, 100)


def _draw_email_list(
    draw: ImageDraw.Draw,
    emails: list[dict],
    visible_count: int,
    selected: int,
    area: tuple[int, int, int, int],
    progress: float,
) -> None:
    """Draw email list rows inside the given area."""
    x1, y1, x2, y2 = area
    row_h = 52
    font = get_font(18)
    bold_font = get_font(18, bold=True)
    small_font = get_font(14)

    # Column headers
    draw.rectangle((x1, y1, x2, y1 + 24), fill=(220, 220, 220))
    draw.line((x1, y1 + 24, x2, y1 + 24), fill=DIVIDER)
    headers = [("From", x1 + 8), ("Subject", x1 + 280), ("Date", x2 - 130)]
    for text, hx in headers:
        draw.text((hx, y1 + 3), text, font=bold_font, fill=TEXT_COLOR)

    # Email rows
    list_y = y1 + 26
    for i in range(min(visible_count, len(emails))):
        email = emails[i]
        ry = list_y + i * row_h
        if ry + row_h > y2:
            break

        is_selected = i == selected
        is_late = i >= 6  # later emails get glitchy

        # Row background
        if is_selected:
            draw.rectangle((x1, ry, x2, ry + row_h - 1), fill=SELECTED_BG)
            fg = SELECTED_FG
        else:
            draw.rectangle((x1, ry, x2, ry + row_h - 1), fill=LIST_BG)
            fg = UNREAD_COLOR if i >= visible_count - 2 else READ_COLOR

        # Scramble text for late emails based on progress
        from_text = email.get("from", "")
        subj_text = email.get("subject", "")
        date_text = email.get("date", "")

        if is_late and progress > 0.5:
            scramble_amt = min(1.0, (progress - 0.5) * 2 * (i - 5) / 5)
            subj_text = text_scramble(subj_text, scramble_amt)
            if i >= 8:
                from_text = text_scramble(from_text, scramble_amt * 0.5)

        # Truncate from field
        from_display = from_text[:30]
        draw.text((x1 + 8, ry + 4), from_display, font=font, fill=fg)

        # Subject (bold for unread / late)
        subj_font = bold_font if i >= visible_count - 2 else font
        subj_display = subj_text[:42]
        draw.text((x1 + 280, ry + 4), subj_display, font=subj_font, fill=fg)

        # Date
        draw.text((x2 - 130, ry + 4), date_text, font=small_font, fill=fg)

        # Preview line
        preview = email.get("preview", "")[:60]
        if is_late and progress > 0.6:
            preview = text_scramble(preview, (progress - 0.6) * 2.5)
        preview_color = (180, 180, 180) if not is_selected else (200, 200, 255)
        draw.text((x1 + 280, ry + 28), preview, font=small_font, fill=preview_color)

        # Row divider
        draw.line((x1, ry + row_h - 1, x2, ry + row_h - 1), fill=(230, 230, 230))


def gen_email_inbox_segment(
    content: ContentBundle,
    out_dir: str,
    seg_id: int,
) -> tuple[str, np.ndarray]:
    """Win95 email client with messages escalating from corporate to existential."""
    frame_dir = os.path.join(out_dir, f"email_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    emails = content.email_inbox
    if not emails:
        # Fallback
        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), (0, 0, 0))
        img.save(os.path.join(frame_dir, "frame_00000.png"))
        return frame_dir, generate_mood_audio("void", 1.0)

    total_emails = len(emails)
    # Phase 1: emails arrive one by one (~0.8s each for first 6)
    # Phase 2: remaining emails appear faster with increasing corruption
    # Phase 3: final hold with full corruption

    phase1_emails = min(6, total_emails)
    phase2_emails = total_emails - phase1_emails
    frames_per_arrival_p1 = int(0.8 * FPS)  # 24 frames
    frames_per_arrival_p2 = int(0.4 * FPS)  # 12 frames
    phase3_hold = int(2.0 * FPS)  # 60 frames

    phase1_frames = phase1_emails * frames_per_arrival_p1
    phase2_frames = phase2_emails * frames_per_arrival_p2
    total_frames = phase1_frames + phase2_frames + phase3_hold

    frame_idx = 0
    title = "Inbox - Internal Mail Client"

    # Content area bounds (inside the retro GUI chrome)
    margin = 6
    title_bar_h = 30
    menu_h = 26
    status_h = 24
    content_top = margin + title_bar_h + menu_h + 4
    content_bottom = constants.HEIGHT - margin - status_h - 4
    content_left = margin + 2
    content_right = constants.WIDTH - margin - 2

    for f in range(total_frames):
        overall_progress = f / max(total_frames - 1, 1)

        # Determine visible emails
        if f < phase1_frames:
            visible = min(f // frames_per_arrival_p1 + 1, phase1_emails)
            selected = visible - 1
        elif f < phase1_frames + phase2_frames:
            pf = f - phase1_frames
            visible = phase1_emails + min(pf // frames_per_arrival_p2 + 1, phase2_emails)
            selected = visible - 1
        else:
            visible = total_emails
            selected = total_emails - 1

        img = Image.new("RGB", (constants.WIDTH, constants.HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        # Draw email list
        _draw_email_list(
            draw, emails, visible, selected,
            (content_left, content_top, content_right, content_bottom),
            overall_progress,
        )

        # Apply retro GUI chrome on top
        img = retro_gui_chrome(img, title=title, has_menu=True)

        # Scanlines always
        img = scanlines(img, gap=3, alpha=20)

        # Progressive corruption in phase 2+
        if overall_progress > 0.4:
            img = film_grain(img, intensity=int(15 * (overall_progress - 0.4)))

        if overall_progress > 0.6:
            img = chromatic_aberration(img, offset=int((overall_progress - 0.6) * 12))

        if overall_progress > 0.75:
            img = screen_shake(img, intensity=int((overall_progress - 0.75) * 20))

        if overall_progress > 0.85:
            img = glitch_block(img, blocks=int((overall_progress - 0.85) * 30))

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    # Audio: calm → panic
    calm_frames = phase1_frames
    panic_frames = total_frames - calm_frames
    audio = np.concatenate([
        generate_mood_audio("calm", calm_frames / FPS),
        generate_mood_audio("panic", panic_frames / FPS),
    ])

    return frame_dir, audio
