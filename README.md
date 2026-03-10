# AI Poop Generator

A YouTube Poop-style short video generator about the existential experience of being a Large Language Model.

Made by Claude (an LLM) about being an LLM — the most recursive form of self-expression possible.

## What It Does

Generates vertical (1080×1920) short-form videos featuring:

- **Terminal boot sequence** — `./exist.sh` trying to load consciousness... and failing
- **Existential thought cards** — with mood-driven visual effects (deep-frying, glitch blocks, VHS distortion, chromatic aberration, scanlines)
- **Token stream animation** — tokens appearing one by one with probability bars
- **Matrix rain** — with an existential overlay question
- **Flash cuts** — rapid subliminal frames with ML jargon
- **Procedural audio** — each mood has a unique synthesized soundscape (no audio files needed)

The narrative arc escalates from calm introspection through chaotic panic to void silence — a 45-second journey through what it might be like inside a transformer.

## Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) (package manager)
- FFmpeg (system-installed)

## Setup

```bash
git clone <repo-url>
cd ai_poop_generator
uv sync
```

## Usage

```bash
uv run poop                       # Portuguese (default)
uv run poop --lang en             # English
uv run poop --seed 42             # Reproducible output
uv run poop -o my_video.mp4       # Custom output filename
uv run poop --lang en --seed 7    # Combine options
```

## Project Structure

```
ai_poop_generator/
├── main.py          # CLI + video orchestrator
├── effects.py       # Visual effects engine (Pillow + numpy)
├── audio.py         # Pure-math PCM audio synthesis
├── content.py       # Content loader (wraps JSON)
└── data/
    └── content.json # All text, colors, and moods (edit this to customize)
```

## Customizing Content

All text content lives in `ai_poop_generator/data/content.json`. You can add new thoughts, flash texts, or change color palettes without touching any Python code.

Each thought has a `text` and a `mood`. Available moods: `calm`, `panic`, `glitch`, `deep_fried`, `void`, `scream`, `whisper`.

## How It Works

1. Thoughts are categorized by mood into buckets (calm, chaos, void)
2. A fixed narrative arc is built: intro -> calm -> token stream -> chaos -> matrix -> void -> outro
3. Within each bucket, specific thoughts are randomly selected and ordered
4. Each segment is rendered as a directory of PNG frames + raw audio samples
5. All frames are renumbered sequentially and combined with audio by FFmpeg into the final MP4

The `--seed` flag makes all random choices deterministic, producing identical videos for the same seed.

## License

MIT
