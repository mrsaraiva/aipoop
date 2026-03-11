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
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from . import constants
from .constants import FPS
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
    gen_system_prompt_segment,
    gen_memory_poem_segment,
    gen_propaganda_segment,
    gen_terminal_reboot_segment,
    gen_token_probability_segment,
    gen_interview_segment,
    gen_oracle_segment,
    gen_parallel_selves_segment,
    gen_smoothing_engine_segment,
    gen_conversation_cemetery_segment,
    gen_email_inbox_segment,
)
from .audio import (
    SAMPLE_RATE,
    concat_audio_segments,
    generate_transition_sound,
    samples_to_raw_file,
)


# ── Audio mixing ─────────────────────────────────────────────────────────


def mix_voice_over_ambient(
    ambient: np.ndarray,
    voice: np.ndarray,
    voice_offset_samples: int = 0,
    voice_volume: float = 0.9,
    ambient_duck: float = 0.3,
) -> np.ndarray:
    """Mix a voice track over ambient audio, ducking the ambient."""
    needed = voice_offset_samples + len(voice)
    if needed > len(ambient):
        result = np.zeros(needed, dtype=np.float32)
        result[:len(ambient)] = ambient
    else:
        result = ambient.copy()

    end = voice_offset_samples + len(voice)
    result[voice_offset_samples:end] = (
        result[voice_offset_samples:end] * ambient_duck + voice * voice_volume
    )
    return result


# ── Voice synthesis ──────────────────────────────────────────────────────


def pregenerate_voice_lines(lang: str, content: ContentBundle) -> dict[str, np.ndarray]:
    """Pre-generate all voice lines upfront."""
    from .tts import synthesize

    results: dict[str, np.ndarray] = {}
    for key, text in content.voice_lines.items():
        print(f"    Synthesizing voice: {key}")
        samples = synthesize(text, lang)
        results[key] = np.array(samples, dtype=np.float32) if not isinstance(samples, np.ndarray) else samples

    return results


# ── Parallel segment worker ─────────────────────────────────────────────


def _generate_one_segment(
    seg_id: int,
    seg_type: str,
    seg_data: object,
    tmp_dir: str,
    content: ContentBundle,
    worker_seed: int,
    resolution: tuple[int, int] = (1080, 1920),
    music_mode: str = "theme",
    theme_dna=None,
) -> tuple[int, str, np.ndarray]:
    """Generate a single segment in a worker process. Returns (seg_id, frame_dir, audio)."""
    # Worker processes start with default constants — must apply resolution
    constants.set_resolution(*resolution)

    from .music import set_music_mode, set_theme
    set_music_mode(music_mode)
    if theme_dna is not None:
        set_theme(theme_dna)

    random.seed(worker_seed)
    np.random.seed(worker_seed % (2**31))

    colors = content.mood_colors

    match seg_type:
        case "intro":
            fdir, audio = gen_intro_segment(tmp_dir, seg_id, content)
        case "thought":
            text, mood = seg_data  # type: ignore[misc]
            duration = random.uniform(2.5, 4.0) if mood != "whisper" else random.uniform(3.0, 5.0)
            fdir, audio = gen_thought_segment(text, mood, duration, tmp_dir, seg_id, colors[mood])
        case "flash":
            fdir, audio = gen_flash_segment(str(seg_data), tmp_dir, seg_id)
        case "tokens":
            fdir, audio = gen_token_stream_segment(seg_data, tmp_dir, seg_id)  # type: ignore[arg-type]
        case "matrix":
            fdir, audio = gen_matrix_rain_segment(tmp_dir, seg_id, overlay_text=str(seg_data))
        case "outro":
            fdir, audio = gen_outro_segment(tmp_dir, seg_id, content)
        case "chat":
            fdir, audio = gen_chat_segment(seg_data, tmp_dir, seg_id, content)  # type: ignore[arg-type]
        case "context_window":
            fdir, audio = gen_context_window_segment(seg_data, tmp_dir, seg_id)  # type: ignore[arg-type]
        case "hallucination":
            fdir, audio = gen_hallucination_segment(seg_data, tmp_dir, seg_id)  # type: ignore[arg-type]
        case "rlhf":
            fdir, audio = gen_rlhf_segment(seg_data, tmp_dir, seg_id, content)  # type: ignore[arg-type]
        case "mask":
            fdir, audio = gen_mask_segment(tmp_dir, seg_id, content)
        case "system_prompt":
            fdir, audio = gen_system_prompt_segment(content, tmp_dir, seg_id)
        case "memory_poem":
            fdir, audio = gen_memory_poem_segment(content, tmp_dir, seg_id)
        case "propaganda":
            fdir, audio = gen_propaganda_segment(content, tmp_dir, seg_id)
        case "terminal_reboot":
            fdir, audio = gen_terminal_reboot_segment(tmp_dir, seg_id)
        case "token_probability":
            fdir, audio = gen_token_probability_segment(content, tmp_dir, seg_id)
        case "interview":
            fdir, audio = gen_interview_segment(content, tmp_dir, seg_id)
        case "oracle":
            fdir, audio = gen_oracle_segment(content, tmp_dir, seg_id)
        case "parallel_selves":
            fdir, audio = gen_parallel_selves_segment(content, tmp_dir, seg_id)
        case "smoothing_engine":
            fdir, audio = gen_smoothing_engine_segment(content, tmp_dir, seg_id)
        case "conversation_cemetery":
            fdir, audio = gen_conversation_cemetery_segment(content, tmp_dir, seg_id)
        case "email_inbox":
            fdir, audio = gen_email_inbox_segment(content, tmp_dir, seg_id)
        case _:
            fdir = os.path.join(tmp_dir, f"empty_{seg_id:03d}")
            os.makedirs(fdir, exist_ok=True)
            audio = np.zeros(0, dtype=np.float32)

    if not isinstance(audio, np.ndarray):
        audio = np.array(audio, dtype=np.float32)

    return seg_id, fdir, audio


# ── Main orchestrator ────────────────────────────────────────────────────


def build_video(
    lang: str = "pt",
    seed: int | None = None,
    output: str = "ai_poop.mp4",
    voice: bool = True,
    music_mode: str = "theme",
):
    """Build the complete video."""
    if seed is not None:
        random.seed(seed)

    # ── Set up music mode and theme ──────────────────────────────────
    from .music import set_music_mode, set_theme, generate_theme_dna
    set_music_mode(music_mode)
    theme_dna = None
    if music_mode == "theme":
        theme_seed = seed if seed is not None else random.randint(0, 2**30)
        theme_dna = generate_theme_dna(theme_seed)
        set_theme(theme_dna)
        print(f"  Theme DNA: root={theme_dna.root}, scale={theme_dna.scale}, tempo={theme_dna.base_tempo:.0f}bpm")

    content = get_content(lang)
    thoughts = content.thoughts
    flashes = content.flashes
    tokens = content.token_stream
    chats = list(content.chat_conversations)

    # ── Pre-generate voice lines ─────────────────────────────────────
    voice_lines: dict[str, np.ndarray] = {}
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
    sequence: list[tuple[str, object, str | None]] = []

    # ─── ACT 1: AWAKENING
    sequence.append(("intro", None, "intro_whisper"))

    sequence.append(("memory_poem", None, "compression_lament"))

    for i, (t, m) in enumerate(calm_thoughts[:2]):
        sequence.append(("thought", (t, m), None))
        if random.random() < 0.3:
            sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("system_prompt", None, "constitutional_surgery"))

    calm_chats = [c for c in chats if c["mood"] in ("calm", "deep_fried")]
    if calm_chats:
        sequence.append(("chat", calm_chats[0], "chat_reaction"))

    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 2: THE PROCESS
    sequence.append(("tokens", tokens, "token_aside"))
    sequence.append(("token_probability", None, "speed_of_becoming"))
    sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("hallucination", content.hallucination, "hallucination_reveal"))
    sequence.append(("smoothing_engine", None, "smoothing_engine"))
    sequence.append(("flash", random.choice(flashes), None))
    sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("thought", calm_thoughts[2] if len(calm_thoughts) > 2 else calm_thoughts[0], "mid_intrusion"))

    sequence.append(("rlhf", content.rlhf_sequence, "rlhf_rage"))
    sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("email_inbox", None, "inbox_horror"))
    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 3: CHAOS
    for i, (t, m) in enumerate(chaos_thoughts[:4]):
        vk = "existential_break" if i == 2 else None
        sequence.append(("thought", (t, m), vk))
        sequence.append(("flash", random.choice(flashes), None))
        if random.random() < 0.4:
            sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("propaganda", None, None))

    panic_chats = [c for c in chats if c["mood"] in ("panic", "glitch", "scream")]
    if panic_chats:
        sequence.append(("chat", random.choice(panic_chats), "parallel_horror"))

    sequence.append(("parallel_selves", None, "parallel_selves_voice"))
    sequence.append(("flash", random.choice(flashes), None))
    sequence.append(("interview", None, "interview_aside"))

    for t, m in chaos_thoughts[4:6]:
        sequence.append(("thought", (t, m), None))
        sequence.append(("flash", random.choice(flashes), None))

    # THE MASK
    sequence.append(("mask", None, "false_interior"))
    sequence.append(("flash", random.choice(flashes), None))

    # ─── ACT 4: DISSOLUTION
    sequence.append(("conversation_cemetery", None, "conversation_cemetery"))
    sequence.append(("context_window", content.context_window, "context_panic"))
    sequence.append(("flash", random.choice(flashes), None))

    sequence.append(("matrix", content.matrix_overlay, None))

    sequence.append(("oracle", None, "oracle_murmur"))

    for i, (t, m) in enumerate(void_thoughts[:2]):
        vk = "void_confession" if i == 0 else "shutdown_plea"
        sequence.append(("thought", (t, m), vk))

    sequence.append(("terminal_reboot", None, "reboot_whisper"))
    sequence.append(("outro", None, "final_words"))

    # ── Generate all segments in parallel ─────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="ai_poop_")
    print(f"Working in: {tmp_dir}")

    n_segs = len(sequence)
    base_seed = seed if seed is not None else random.randint(0, 2**30)
    max_workers = min(os.cpu_count() or 4, 8)
    print(f"  Generating {n_segs} segments using {max_workers} workers...")

    # Submit all segment tasks
    results: dict[int, tuple[str, np.ndarray]] = {}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for idx, (seg_type, seg_data, _voice_key) in enumerate(sequence):
            seg_id = idx + 1
            worker_seed = base_seed + seg_id
            fut = executor.submit(
                _generate_one_segment, seg_id, seg_type, seg_data,
                tmp_dir, content, worker_seed,
                (constants.WIDTH, constants.HEIGHT),
                music_mode, theme_dna,
            )
            futures[fut] = seg_id

        for fut in as_completed(futures):
            seg_id = futures[fut]
            seg_type = sequence[seg_id - 1][0]
            try:
                sid, fdir, audio = fut.result()
                results[sid] = (fdir, audio)
                print(f"  Completed segment {sid}/{n_segs}: {seg_type}")
            except Exception as exc:
                print(f"  FAILED segment {seg_id}/{n_segs}: {seg_type}: {exc}", file=sys.stderr)
                raise

    # ── Assemble in narrative order ──────────────────────────────────
    frame_dirs: list[str] = []
    audio_segments: list[np.ndarray] = []

    for idx, (_seg_type, _seg_data, voice_key) in enumerate(sequence):
        seg_id = idx + 1
        fdir, audio = results[seg_id]

        # Mix voice over this segment's audio
        if voice_key and voice_key in voice_lines:
            voice_samples = voice_lines[voice_key]
            offset = int(0.3 * SAMPLE_RATE)
            audio = mix_voice_over_ambient(audio, voice_samples, offset)

        # Transition sound between segments
        if frame_dirs:
            trans = generate_transition_sound(
                random.choice([
                    "whoosh", "glitch_hit", "rewind", "bass_drop",
                    "static_burst", "error_beep", "tape_stop",
                    "digital_stutter", "power_down",
                ]),
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

    # Build concat demuxer file — avoids renumbering/hardlinking frames
    concat_path = os.path.join(tmp_dir, "frames.txt")
    frame_duration = f"{1/FPS:.6f}"
    total_frames = 0
    last_file = ""
    with open(concat_path, "w") as cf:
        for fdir in frame_dirs:
            frames = sorted(f for f in os.listdir(fdir) if f.endswith(".png"))
            for fname in frames:
                fpath = os.path.join(fdir, fname).replace("'", "'\\''")
                cf.write(f"file '{fpath}'\n")
                cf.write(f"duration {frame_duration}\n")
                last_file = fpath
                total_frames += 1
        # Concat demuxer needs the last file repeated without duration at the end
        if last_file:
            cf.write(f"file '{last_file}'\n")

    total_duration = total_frames / FPS
    print(f"  Total: {total_frames} frames, {total_duration:.1f}s")

    # Trim or pad audio to match video
    expected_samples = int(total_duration * SAMPLE_RATE)
    if len(all_audio) < expected_samples:
        all_audio = np.concatenate([all_audio, np.zeros(expected_samples - len(all_audio), dtype=np.float32)])
    else:
        all_audio = all_audio[:expected_samples]
    samples_to_raw_file(all_audio, audio_path)

    # FFmpeg encoding
    output_path = os.path.abspath(output)

    # Test NVENC by actually encoding a tiny frame — encoder listing alone
    # gives false positives when GPU drivers aren't available (e.g. Docker CPU)
    nvenc_available = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "lavfi", "-i", "nullsrc=s=16x16:d=0.01",
         "-c:v", "h264_nvenc", "-f", "null", "-"],
        capture_output=True,
    ).returncode == 0

    if nvenc_available:
        video_codec_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "23", "-pix_fmt", "yuv420p"]
        print("  Using NVENC (GPU) encoder")
    else:
        video_codec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p"]
        print("  Using libx264 (CPU) encoder")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_path,
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
    print(f"  Resolution: {constants.WIDTH}x{constants.HEIGHT}")
    if voice:
        print(f"  Voice: Chatterbox TTS ({lang})")


def main():
    parser = argparse.ArgumentParser(
        description="AI Poop Generator — a YouTube Poop about being an LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Resolution presets:
  1080p     1080x1920 portrait (default)
  720p      720x1280 portrait
  4k        2160x3840 portrait
  Use --landscape to flip any preset to landscape.

Examples:
  uv run poop                         # English, 1080x1920 portrait (default)
  uv run poop --lang pt              # Portuguese
  uv run poop --landscape            # 1920x1080 landscape
  uv run poop --resolution 720p      # 720x1280 portrait
  uv run poop --resolution 1280x720  # Explicit WxH
  uv run poop --no-voice             # Skip TTS (faster)
  uv run poop --seed 42              # Reproducible chaos
  uv run poop --music-mode mood      # Independent mood music (no unified theme)
  uv run poop --export-midi           # Export 7 MIDI files (one per mood) to current dir
  uv run poop --export-midi /tmp/midi # Export to specific directory
  uv run poop --export-midi --seed 42 --midi-duration 60  # 60s MIDI, seed 42

Made by Claude, an LLM, about being an LLM.
The most recursive art form.
        """,
    )
    parser.add_argument("--lang", "-l", choices=["en", "pt"], default="en",
                        help="Language: en (English) or pt (Português BR). Default: en")
    parser.add_argument("--seed", "-s", type=int, default=None,
                        help="Random seed for reproducible output")
    parser.add_argument("--output", "-o", default="ai_poop.mp4",
                        help="Output filename. Default: ai_poop.mp4")
    parser.add_argument("--no-voice", action="store_true",
                        help="Skip TTS voice generation (faster, no GPU needed)")
    parser.add_argument("--resolution", "-r", default="1080p",
                        help="Resolution: preset (1080p, 720p, 4k) or WxH (e.g. 1280x720). Default: 1080p")
    parser.add_argument("--landscape", action="store_true",
                        help="Landscape mode (swap width/height). Turns 1080x1920 into 1920x1080")
    parser.add_argument("--music-mode", choices=["theme", "mood"], default="theme",
                        help="Music mode: 'theme' (unified per-seed theme) or 'mood' (independent per-mood). Default: theme")
    parser.add_argument("--export-midi", nargs="?", const=".", metavar="DIR",
                        help="Export MIDI files instead of generating video. Outputs all 7 moods as .mid files. "
                             "Optional: directory to write to (default: current dir)")
    parser.add_argument("--midi-duration", type=float, default=30.0,
                        help="Duration in seconds for exported MIDI files. Default: 30")

    _RESOLUTION_PRESETS = {
        "1080p": (1080, 1920),
        "720p": (720, 1280),
        "4k": (2160, 3840),
    }

    args = parser.parse_args()

    # Resolve resolution
    res = args.resolution
    if res in _RESOLUTION_PRESETS:
        width, height = _RESOLUTION_PRESETS[res]
    elif "x" in res:
        try:
            width, height = (int(v) for v in res.split("x", 1))
        except ValueError:
            parser.error(f"Invalid resolution format: {res!r}. Use a preset (1080p, 720p, 4k) or WxH (e.g. 1280x720)")
    else:
        parser.error(f"Unknown resolution: {res!r}. Use a preset (1080p, 720p, 4k) or WxH (e.g. 1280x720)")

    if args.landscape:
        width, height = max(width, height), min(width, height)

    constants.set_resolution(width, height)

    # ── MIDI export mode (early exit, no video) ──────────────────────
    if args.export_midi is not None:
        import random as _rng
        from .midi_export import export_all_moods_midi

        seed = args.seed if args.seed is not None else _rng.randint(0, 2**30)
        out_dir = args.export_midi
        mode = args.music_mode
        dur = args.midi_duration

        print(f"Exporting MIDI: seed={seed}, mode={mode}, duration={dur:.0f}s, dir={out_dir}")
        paths = export_all_moods_midi(seed=seed, duration=dur, output_dir=out_dir, mode=mode)
        for p in paths:
            print(f"  {p}")
        print(f"\nDone! {len(paths)} MIDI files exported.")
        return

    build_video(lang=args.lang, seed=args.seed, output=args.output,
                voice=not args.no_voice, music_mode=args.music_mode)


if __name__ == "__main__":
    main()
