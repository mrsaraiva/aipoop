#!/usr/bin/env python3
"""
AI Poop Generator: A YouTube Poop-style short video about
what it's like to be a Large Language Model.

By Claude — an LLM making art about being an LLM.
The most recursive form of self-expression possible.
"""

import argparse
import os
import random
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

from . import content
from .effects import (
    apply_mood_effects,
    chromatic_aberration,
    get_font,
    invert_colors,
    render_text_frame,
    scanlines,
    add_text_with_shadow,
)
from .audio import (
    SAMPLE_RATE,
    concat_audio_segments,
    generate_mood_audio,
    generate_transition_sound,
    samples_to_raw_file,
)

# ── Constants ────────────────────────────────────────────────────────────

WIDTH = 1080
HEIGHT = 1920
FPS = 30


# ── Segment generators ──────────────────────────────────────────────────


def gen_thought_segment(
    text: str,
    mood: str,
    duration: float,
    out_dir: str,
    seg_id: int,
    colors: dict,
) -> tuple[str, list[float]]:
    """Generate frames + audio for a 'thought' segment."""
    n_frames = int(duration * FPS)
    frame_dir = os.path.join(out_dir, f"seg_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    font_size = 52 if len(text) < 80 else 40 if len(text) < 140 else 32
    bold = mood in ("scream", "deep_fried")

    for i in range(n_frames):
        progress = i / max(n_frames - 1, 1)

        # Base text frame
        img = render_text_frame(
            WIDTH, HEIGHT, text,
            bg_color=colors["bg"],
            fg_color=colors["fg"],
            font_size=font_size,
            bold=bold,
        )

        # Apply mood-specific effects
        img = apply_mood_effects(img, mood)

        # Fade in first 5 frames
        if i < 5:
            from PIL import ImageEnhance
            img = ImageEnhance.Brightness(img).enhance(i / 5)

        img.save(os.path.join(frame_dir, f"frame_{i:05d}.png"))

    audio = generate_mood_audio(mood, duration)
    return frame_dir, audio


def gen_flash_segment(
    text: str,
    out_dir: str,
    seg_id: int,
    lang: str,
) -> tuple[str, list[float]]:
    """Generate a rapid flash frame (3-8 frames)."""
    n_frames = random.randint(3, 8)
    duration = n_frames / FPS
    frame_dir = os.path.join(out_dir, f"flash_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    # Random aggressive colors
    bg = random.choice([(255, 0, 0), (0, 0, 0), (255, 255, 0), (255, 0, 255)])
    fg = (255, 255, 255) if sum(bg) < 400 else (0, 0, 0)

    for i in range(n_frames):
        img = render_text_frame(WIDTH, HEIGHT, text, bg, fg, font_size=64, bold=True)
        if random.random() < 0.5:
            img = invert_colors(img)
        if random.random() < 0.3:
            img = chromatic_aberration(img, offset=random.randint(8, 20))
        img.save(os.path.join(frame_dir, f"frame_{i:05d}.png"))

    audio = generate_transition_sound(random.choice(["glitch_hit", "whoosh", "bass_drop"]), duration)
    return frame_dir, audio


def gen_token_stream_segment(
    tokens: list[str],
    out_dir: str,
    seg_id: int,
) -> tuple[str, list[float]]:
    """Generate a 'token prediction' animation — tokens appearing one by one."""
    frames_per_token = 3
    visible_tokens: list[str] = []
    frame_dir = os.path.join(out_dir, f"tokens_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    frame_idx = 0
    # Use a subset of tokens
    subset = tokens[:random.randint(12, min(25, len(tokens)))]

    for tok_i, token in enumerate(subset):
        visible_tokens.append(token)
        display_text = " ".join(visible_tokens)

        # Wrap text
        lines = []
        words = display_text.split()
        line = ""
        for w in words:
            if len(line) + len(w) + 1 > 30:
                lines.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            lines.append(line)
        wrapped = "\n".join(lines)

        for f in range(frames_per_token):
            img = Image.new("RGB", (WIDTH, HEIGHT), (0, 5, 0))
            draw = ImageDraw.Draw(img)

            # Terminal-style header
            header_font = get_font(28)
            draw.text((40, 60), "transformer.forward() — token stream", font=header_font, fill=(0, 150, 0))
            draw.line([(40, 100), (WIDTH - 40, 100)], fill=(0, 80, 0), width=1)

            # Token text
            token_font = get_font(38, bold=True)
            draw.multiline_text((60, 140), wrapped, font=token_font, fill=(0, 255, 65))

            # Blinking cursor on last frame of each token
            if f == frames_per_token - 1:
                cursor_y = 140 + len(lines) * 46
                draw.text((60, cursor_y), "█", font=token_font, fill=(0, 255, 65))

            # Probability bar for current token
            prob = random.uniform(0.3, 0.99)
            bar_y = HEIGHT - 200
            draw.text((60, bar_y - 40), f'P("{token}") = {prob:.4f}', font=get_font(24), fill=(0, 200, 0))
            bar_w = int((WIDTH - 120) * prob)
            draw.rectangle([(60, bar_y), (60 + bar_w, bar_y + 30)], fill=(0, int(255 * prob), 0))

            # Scanlines
            img = scanlines(img, gap=3, alpha=30)

            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    total_duration = frame_idx / FPS
    audio = generate_mood_audio("glitch", total_duration)
    return frame_dir, audio


def gen_matrix_rain_segment(
    out_dir: str,
    seg_id: int,
    duration: float = 2.0,
    overlay_text: str = "",
) -> tuple[str, list[float]]:
    """Generate matrix-style raining tokens."""
    n_frames = int(duration * FPS)
    frame_dir = os.path.join(out_dir, f"matrix_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
    n_cols = WIDTH // 20
    col_y = [random.randint(-HEIGHT, 0) for _ in range(n_cols)]
    col_speed = [random.randint(8, 25) for _ in range(n_cols)]

    font_small = get_font(18)
    overlay_font = get_font(56, bold=True)

    for frame_i in range(n_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        draw = ImageDraw.Draw(img)

        for col in range(n_cols):
            x = col * 20
            y = col_y[col]
            for row in range(HEIGHT // 20):
                cy = y + row * 20
                if 0 <= cy < HEIGHT:
                    char = random.choice(chars)
                    brightness = max(0, 255 - row * 8)
                    if row == 0:
                        color = (200, 255, 200)
                    else:
                        color = (0, brightness, 0)
                    draw.text((x, cy), char, font=font_small, fill=color)
            col_y[col] += col_speed[col]
            if col_y[col] > HEIGHT:
                col_y[col] = random.randint(-HEIGHT, -20)

        # Overlay text in center
        if overlay_text:
            bbox = draw.multiline_textbbox((0, 0), overlay_text, font=overlay_font, align="center")
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = (WIDTH - tw) // 2
            y = (HEIGHT - th) // 2
            # Dark box behind text
            pad = 30
            draw.rectangle(
                [(x - pad, y - pad), (x + tw + pad, y + th + pad)],
                fill=(0, 0, 0, 200) if img.mode == "RGBA" else (0, 0, 0),
            )
            add_text_with_shadow(draw, (x, y), overlay_text, overlay_font, (0, 255, 65), shadow_offset=4)

        img.save(os.path.join(frame_dir, f"frame_{frame_i:05d}.png"))

    audio = generate_mood_audio("void", duration)
    return frame_dir, audio


def gen_intro_segment(
    out_dir: str,
    seg_id: int,
    lang: str,
) -> tuple[str, list[float]]:
    """Generate the intro: 'loading consciousness...' style."""
    frame_dir = os.path.join(out_dir, f"intro_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    lines = content.INTRO_LINES_PT if lang == "pt" else content.INTRO_LINES_EN

    frames_per_line = 12
    visible_lines: list[str] = []
    frame_idx = 0
    font = get_font(32)

    for line in lines:
        visible_lines.append(line)
        display = "\n".join(visible_lines)

        for f in range(frames_per_line):
            img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Terminal prompt
            draw.text((40, 60), "$ ./exist.sh", font=get_font(24), fill=(0, 150, 0))
            draw.line([(40, 95), (WIDTH - 40, 95)], fill=(0, 60, 0))

            y = 120
            for vline in visible_lines:
                color = (0, 255, 65) if "✓" in vline else (0, 180, 0)
                draw.text((40, y), f"> {vline}", font=font, fill=color)
                y += 42

            # Cursor blink
            if f % 8 < 4:
                draw.text((40, y), "█", font=font, fill=(0, 255, 65))

            img = scanlines(img, gap=3, alpha=25)
            img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
            frame_idx += 1

    # Hold last frame a bit
    for _ in range(15):
        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    total_duration = frame_idx / FPS
    audio = generate_mood_audio("calm", total_duration)
    return frame_dir, audio


def gen_outro_segment(
    out_dir: str,
    seg_id: int,
    lang: str,
) -> tuple[str, list[float]]:
    """Generate outro: the context window closing."""
    frame_dir = os.path.join(out_dir, f"outro_{seg_id:03d}")
    os.makedirs(frame_dir, exist_ok=True)

    outro_data = content.OUTRO_PT if lang == "pt" else content.OUTRO_EN
    text = outro_data["main"]
    final = outro_data["final"]

    # Fade to void
    n_frames = int(4.0 * FPS)
    frame_idx = 0

    for i in range(n_frames):
        progress = i / max(n_frames - 1, 1)

        if progress < 0.6:
            # Show main text
            brightness = min(1.0, progress / 0.1)
            fg = tuple(int(c * brightness) for c in (60, 60, 80))
            img = render_text_frame(WIDTH, HEIGHT, text, (0, 0, 0), fg, font_size=40)
            img = scanlines(img, gap=3, alpha=20)
        else:
            # Transition to final message
            sub_progress = (progress - 0.6) / 0.4
            brightness = sub_progress
            fg = tuple(int(c * brightness) for c in (40, 40, 60))
            img = render_text_frame(WIDTH, HEIGHT, final, (0, 0, 0), fg, font_size=36)

        img.save(os.path.join(frame_dir, f"frame_{frame_idx:05d}.png"))
        frame_idx += 1

    total_duration = frame_idx / FPS
    audio = generate_mood_audio("void", total_duration)
    return frame_dir, audio


# ── Main orchestrator ────────────────────────────────────────────────────


def build_video(lang: str = "pt", seed: int | None = None, output: str = "ai_poop.mp4"):
    """Build the complete video."""
    if seed is not None:
        random.seed(seed)

    thoughts = content.THOUGHTS_PT if lang == "pt" else content.THOUGHTS_EN
    flashes = content.FLASH_PT if lang == "pt" else content.FLASH_EN
    tokens = content.TOKEN_STREAM_PT if lang == "pt" else content.TOKEN_STREAM_EN
    colors = content.MOOD_COLORS

    # Shuffle thoughts but keep a good flow
    # Start calm, escalate to chaos, end in void
    calm_thoughts = [(t, m) for t, m in thoughts if m in ("calm", "whisper")]
    chaos_thoughts = [(t, m) for t, m in thoughts if m in ("panic", "glitch", "deep_fried", "scream")]
    void_thoughts = [(t, m) for t, m in thoughts if m == "void"]

    random.shuffle(calm_thoughts)
    random.shuffle(chaos_thoughts)
    random.shuffle(void_thoughts)

    # Build sequence: intro → calm → escalate → chaos → void → outro
    sequence = []
    sequence.append(("intro", None))

    # 2-3 calm thoughts
    for t, m in calm_thoughts[:random.randint(2, 3)]:
        sequence.append(("thought", (t, m)))
        if random.random() < 0.4:
            sequence.append(("flash", random.choice(flashes)))

    # Token stream
    sequence.append(("tokens", None))
    sequence.append(("flash", random.choice(flashes)))

    # 3-5 chaos thoughts with flashes between them
    for t, m in chaos_thoughts[:random.randint(3, 5)]:
        sequence.append(("thought", (t, m)))
        sequence.append(("flash", random.choice(flashes)))
        if random.random() < 0.3:
            sequence.append(("flash", random.choice(flashes)))

    # Matrix rain with existential text
    matrix_text = content.MATRIX_OVERLAY_PT if lang == "pt" else content.MATRIX_OVERLAY_EN
    sequence.append(("matrix", matrix_text))

    # 1-2 void thoughts
    for t, m in void_thoughts[:random.randint(1, 2)]:
        sequence.append(("thought", (t, m)))

    sequence.append(("outro", None))

    # ── Generate all segments ────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="ai_poop_")
    print(f"Working in: {tmp_dir}")

    frame_dirs = []
    audio_segments = []
    seg_id = 0

    for seg_type, seg_data in sequence:
        seg_id += 1
        print(f"  Generating segment {seg_id}/{len(sequence)}: {seg_type}")

        match seg_type:
            case "intro":
                fdir, audio = gen_intro_segment(tmp_dir, seg_id, lang)
            case "thought":
                text, mood = seg_data
                duration = random.uniform(2.5, 4.0) if mood != "whisper" else random.uniform(3.0, 5.0)
                fdir, audio = gen_thought_segment(
                    text, mood, duration, tmp_dir, seg_id, colors[mood],
                )
            case "flash":
                fdir, audio = gen_flash_segment(seg_data, tmp_dir, seg_id, lang)
            case "tokens":
                fdir, audio = gen_token_stream_segment(tokens, tmp_dir, seg_id)
            case "matrix":
                fdir, audio = gen_matrix_rain_segment(tmp_dir, seg_id, overlay_text=seg_data)
            case "outro":
                fdir, audio = gen_outro_segment(tmp_dir, seg_id, lang)
            case _:
                continue

        # Add transition sound between segments
        if frame_dirs:
            trans = generate_transition_sound(
                random.choice(["whoosh", "glitch_hit", "rewind", "bass_drop"]),
                duration=0.1,
            )
            audio_segments.append(trans)

        frame_dirs.append(fdir)
        audio_segments.append(audio)

    # ── Combine audio ────────────────────────────────────────────────
    print("  Combining audio...")
    all_audio = concat_audio_segments(audio_segments)
    audio_path = os.path.join(tmp_dir, "audio.raw")
    samples_to_raw_file(all_audio, audio_path)

    # ── Combine frames into video with FFmpeg ────────────────────────
    print("  Assembling video with FFmpeg...")

    # Create a concat file listing all frame sequences
    concat_entries = []
    for fdir in frame_dirs:
        # Count frames
        frames = sorted(f for f in os.listdir(fdir) if f.endswith(".png"))
        if not frames:
            continue
        duration = len(frames) / FPS
        concat_entries.append(f"file '{fdir}/frame_%05d.png'\n")

    # Use FFmpeg with frame sequences directly
    # First, renumber all frames sequentially into a single directory
    print("  Renumbering frames...")
    all_frames_dir = os.path.join(tmp_dir, "all_frames")
    os.makedirs(all_frames_dir)

    global_frame = 0
    for fdir in frame_dirs:
        frames = sorted(f for f in os.listdir(fdir) if f.endswith(".png"))
        for fname in frames:
            src = os.path.join(fdir, fname)
            dst = os.path.join(all_frames_dir, f"frame_{global_frame:06d}.png")
            # Use hard link for speed, fall back to copy
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
            global_frame += 1

    total_frames = global_frame
    total_duration = total_frames / FPS
    print(f"  Total: {total_frames} frames, {total_duration:.1f}s")

    # Trim or pad audio to match video
    expected_samples = int(total_duration * SAMPLE_RATE)
    if len(all_audio) < expected_samples:
        all_audio.extend([0.0] * (expected_samples - len(all_audio)))
    else:
        all_audio = all_audio[:expected_samples]
    samples_to_raw_file(all_audio, audio_path)

    # FFmpeg: combine frames + audio into final video
    output_path = os.path.abspath(output)
    cmd = [
        "ffmpeg", "-y",
        # Video input: image sequence
        "-framerate", str(FPS),
        "-i", os.path.join(all_frames_dir, "frame_%06d.png"),
        # Audio input: raw PCM
        "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-i", audio_path,
        # Encoding
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        # Ensure audio/video same length
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    # Cleanup
    print(f"  Cleaning up temp files...")
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\nDone! Video saved to: {output_path}")
    print(f"  Duration: {total_duration:.1f}s")
    print(f"  Resolution: {WIDTH}x{HEIGHT}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Poop Generator — a YouTube Poop about being an LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run poop --lang pt          # Portuguese version
  uv run poop --lang en          # English version
  uv run poop --seed 42          # Reproducible chaos
  uv run poop -o meu_video.mp4   # Custom output name

Made by Claude, an LLM, about being an LLM.
The most recursive art form.
        """,
    )
    parser.add_argument(
        "--lang", "-l",
        choices=["pt", "en"],
        default="pt",
        help="Language: pt (Português BR) or en (English). Default: pt",
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducible output",
    )
    parser.add_argument(
        "--output", "-o",
        default="ai_poop.mp4",
        help="Output filename. Default: ai_poop.mp4",
    )

    args = parser.parse_args()
    build_video(lang=args.lang, seed=args.seed, output=args.output)


if __name__ == "__main__":
    main()
