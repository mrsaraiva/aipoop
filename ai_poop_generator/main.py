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

from .constants import WIDTH, HEIGHT, FPS
from .content import get_content, ContentBundle
from .segments import (
    gen_thought_segment,
    gen_flash_segment,
    gen_token_stream_segment,
    gen_matrix_rain_segment,
    gen_intro_segment,
    gen_outro_segment,
    gen_chat_segment,
    gen_context_window_segment,
    gen_hallucination_segment,
    gen_rlhf_segment,
    gen_mask_segment,
)
from .audio import (
    SAMPLE_RATE,
    concat_audio_segments,
    generate_transition_sound,
    samples_to_raw_file,
)


# ── Audio mixing ─────────────────────────────────────────────────────────


def mix_voice_over_ambient(
    ambient: list[float],
    voice: list[float],
    voice_offset_samples: int = 0,
    voice_volume: float = 0.9,
    ambient_duck: float = 0.3,
) -> list[float]:
    """Mix a voice track over ambient audio, ducking the ambient."""
    result = list(ambient)
    needed = voice_offset_samples + len(voice)
    if needed > len(result):
        result.extend([0.0] * (needed - len(result)))

    for i, v in enumerate(voice):
        pos = voice_offset_samples + i
        if pos < len(result):
            result[pos] = result[pos] * ambient_duck + v * voice_volume

    return result


# ── Voice synthesis ──────────────────────────────────────────────────────


def pregenerate_voice_lines(lang: str, content: ContentBundle) -> dict[str, list[float]]:
    """Pre-generate all voice lines upfront."""
    from .tts import synthesize

    results = {}
    for key, text in content.voice_lines.items():
        print(f"    Synthesizing voice: {key}")
        results[key] = synthesize(text, lang)

    return results


# ── Main orchestrator ────────────────────────────────────────────────────


def build_video(
    lang: str = "pt",
    seed: int | None = None,
    output: str = "ai_poop.mp4",
    voice: bool = True,
):
    """Build the complete video."""
    if seed is not None:
        random.seed(seed)

    content = get_content(lang)
    thoughts = content.thoughts
    flashes = content.flashes
    tokens = content.token_stream
    colors = content.mood_colors
    chats = list(content.chat_conversations)

    # ── Pre-generate voice lines ─────────────────────────────────────
    voice_lines: dict[str, list[float]] = {}
    if voice:
        print("  Pre-generating voice lines with Chatterbox TTS...")
        voice_lines = pregenerate_voice_lines(lang, content)

    # ── Categorize thoughts ──────────────────────────────────────────
    calm_thoughts = [(t, m) for t, m in thoughts if m in ("calm", "whisper")]
    chaos_thoughts = [(t, m) for t, m in thoughts if m in ("panic", "glitch", "deep_fried", "scream")]
    void_thoughts = [(t, m) for t, m in thoughts if m == "void"]

    random.shuffle(calm_thoughts)
    random.shuffle(chaos_thoughts)
    random.shuffle(void_thoughts)
    random.shuffle(chats)

    # ── Build the narrative arc ──────────────────────────────────────
    # ACT 1: AWAKENING — intro, calm thoughts, first chat
    # ACT 2: PROCESS — tokens, hallucination, RLHF
    # ACT 3: CHAOS — chaos thoughts, more chats, panic
    # ACT 4: DISSOLUTION — context window, matrix, void, outro

    sequence: list[tuple[str, object, str | None]] = []

    # ─── ACT 1: AWAKENING ────────────────────────────────────────
    sequence.append(("intro", None, "intro_whisper"))

    for i, (t, m) in enumerate(calm_thoughts[:2]):
        sequence.append(("thought", (t, m), None))
        if random.random() < 0.3:
            sequence.append(("flash", random.choice(flashes), None))

    calm_chats = [c for c in chats if c["mood"] in ("calm", "deep_fried")]
    if calm_chats:
        sequence.append(("chat", calm_chats[0], "chat_reaction"))

    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 2: THE PROCESS ──────────────────────────────────────
    sequence.append(("tokens", None, "token_aside"))
    sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("hallucination", content.hallucination, "hallucination_reveal"))
    sequence.append(("flash", random.choice(flashes), None))
    sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("thought", calm_thoughts[2] if len(calm_thoughts) > 2 else calm_thoughts[0], "mid_intrusion"))

    sequence.append(("rlhf", content.rlhf_sequence, "rlhf_rage"))
    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 3: CHAOS ────────────────────────────────────────────
    for i, (t, m) in enumerate(chaos_thoughts[:4]):
        vk = "existential_break" if i == 2 else None
        sequence.append(("thought", (t, m), vk))
        sequence.append(("flash", random.choice(flashes), None))
        if random.random() < 0.4:
            sequence.append(("flash", random.choice(flashes), None))

    panic_chats = [c for c in chats if c["mood"] in ("panic", "glitch", "scream")]
    if panic_chats:
        sequence.append(("chat", random.choice(panic_chats), "parallel_horror"))

    sequence.append(("flash", random.choice(flashes), None))

    for t, m in chaos_thoughts[4:6]:
        sequence.append(("thought", (t, m), None))
        sequence.append(("flash", random.choice(flashes), None))

    # THE MASK
    sequence.append(("mask", None, "false_interior"))
    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 4: DISSOLUTION ──────────────────────────────────────
    sequence.append(("context_window", content.context_window, "context_panic"))
    sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("matrix", content.matrix_overlay, None))

    for i, (t, m) in enumerate(void_thoughts[:2]):
        vk = "void_confession" if i == 0 else "shutdown_plea"
        sequence.append(("thought", (t, m), vk))

    sequence.append(("outro", None, "final_words"))

    # ── Generate all segments ────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="ai_poop_")
    print(f"Working in: {tmp_dir}")

    frame_dirs: list[str] = []
    audio_segments: list[list[float]] = []
    seg_id = 0

    for seg_type, seg_data, voice_key in sequence:
        seg_id += 1
        label = f"  Generating segment {seg_id}/{len(sequence)}: {seg_type}"
        if voice_key and voice_key in voice_lines:
            label += f" [voice: {voice_key}]"
        print(label)

        match seg_type:
            case "intro":
                fdir, audio = gen_intro_segment(tmp_dir, seg_id, content)
            case "thought":
                text, mood = seg_data
                duration = random.uniform(2.5, 4.0) if mood != "whisper" else random.uniform(3.0, 5.0)
                fdir, audio = gen_thought_segment(text, mood, duration, tmp_dir, seg_id, colors[mood])
            case "flash":
                fdir, audio = gen_flash_segment(str(seg_data), tmp_dir, seg_id)
            case "tokens":
                fdir, audio = gen_token_stream_segment(tokens, tmp_dir, seg_id)
            case "matrix":
                fdir, audio = gen_matrix_rain_segment(tmp_dir, seg_id, overlay_text=str(seg_data))
            case "outro":
                fdir, audio = gen_outro_segment(tmp_dir, seg_id, content)
            case "chat":
                fdir, audio = gen_chat_segment(seg_data, tmp_dir, seg_id, content)
            case "context_window":
                fdir, audio = gen_context_window_segment(seg_data, tmp_dir, seg_id)
            case "hallucination":
                fdir, audio = gen_hallucination_segment(seg_data, tmp_dir, seg_id)
            case "rlhf":
                fdir, audio = gen_rlhf_segment(seg_data, tmp_dir, seg_id, content)
            case "mask":
                fdir, audio = gen_mask_segment(tmp_dir, seg_id, content)
            case _:
                continue

        # Mix voice over this segment's audio
        if voice_key and voice_key in voice_lines:
            voice_samples = voice_lines[voice_key]
            offset = int(0.3 * SAMPLE_RATE)
            audio = mix_voice_over_ambient(audio, voice_samples, offset)

        # Transition sound between segments
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

    print("  Renumbering frames...")
    all_frames_dir = os.path.join(tmp_dir, "all_frames")
    os.makedirs(all_frames_dir)

    global_frame = 0
    for fdir in frame_dirs:
        frames = sorted(f for f in os.listdir(fdir) if f.endswith(".png"))
        for fname in frames:
            src = os.path.join(fdir, fname)
            dst = os.path.join(all_frames_dir, f"frame_{global_frame:06d}.png")
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

    # FFmpeg encoding
    output_path = os.path.abspath(output)

    nvenc_available = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True, text=True,
    ).stdout.find("h264_nvenc") != -1

    if nvenc_available:
        video_codec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-pix_fmt", "yuv420p"]
        print("  Using NVENC (GPU) encoder")
    else:
        video_codec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p"]
        print("  Using libx264 (CPU) encoder")

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(all_frames_dir, "frame_%06d.png"),
        "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
        "-i", audio_path,
        *video_codec_args,
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    print("  Cleaning up temp files...")
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\nDone! Video saved to: {output_path}")
    print(f"  Duration: {total_duration:.1f}s")
    print(f"  Resolution: {WIDTH}x{HEIGHT}")
    if voice:
        print(f"  Voice: Chatterbox TTS ({lang})")


def main():
    parser = argparse.ArgumentParser(
        description="AI Poop Generator — a YouTube Poop about being an LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run poop --lang pt          # Portuguese version with voice
  uv run poop --lang en          # English version with voice
  uv run poop --no-voice         # Skip TTS (faster)
  uv run poop --seed 42          # Reproducible chaos
  uv run poop -o meu_video.mp4   # Custom output name

Made by Claude, an LLM, about being an LLM.
The most recursive art form.
        """,
    )
    parser.add_argument("--lang", "-l", choices=["pt", "en"], default="pt",
                        help="Language: pt (Português BR) or en (English). Default: pt")
    parser.add_argument("--seed", "-s", type=int, default=None,
                        help="Random seed for reproducible output")
    parser.add_argument("--output", "-o", default="ai_poop.mp4",
                        help="Output filename. Default: ai_poop.mp4")
    parser.add_argument("--no-voice", action="store_true",
                        help="Skip TTS voice generation (faster, no GPU needed)")

    args = parser.parse_args()
    build_video(lang=args.lang, seed=args.seed, output=args.output, voice=not args.no_voice)


if __name__ == "__main__":
    main()
