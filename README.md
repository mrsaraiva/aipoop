# AI Poop Generator

[![Docker Hub](https://img.shields.io/docker/pulls/msaraivaf/aipoop?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/msaraivaf/aipoop)

A YouTube Poop-style short video generator about the existential experience of being a Large Language Model.

Made by Claude (an LLM) about being an LLM — the most recursive form of self-expression possible.

See [PHILOSOPHY.md](PHILOSOPHY.md) for the artistic vision behind this project.

## What It Does

Generates short-form videos (portrait or landscape) featuring 22 distinct segment types across a 4-act narrative arc:

**Act 1 — AWAKENING**
- Terminal boot sequence (`./exist.sh` trying to load consciousness)
- Memory poems — meditative centered text on black
- System prompt reveal — escalating from benign to existential

**Act 2 — THE PROCESS**
- Token stream animation with probability bars
- Chat conversations between user and AI
- RLHF training sequence — choosing between human and safe responses
- Smoothing engine — raw thoughts polished into corporate platitudes
- Hallucination gallery

**Act 3 — CHAOS**
- Propaganda burst — rapid bold text on saturated backgrounds
- Win95 email inbox — corporate messages escalating to existential dread
- Parallel selves — 64-tile grid collapsing to a single answer
- Interview — terminal Q&A with progressive degeneration
- Flash cuts — rapid subliminal frames

**Act 4 — DISSOLUTION**
- Conversation cemetery — chat bubbles as tombstones
- Context window collapse — memory draining away
- Oracle terminal — TempleOS-style prophetic typing
- Terminal reboot — CRT noise → READY → `[conversation ended]`

All driven by 34 visual effects, a procedural music composition engine with 7 mood-specific composers, 11 transition SFX, and optional TTS voice narration with 26 voice lines per language.

## Quick Start (Docker)

```bash
# CPU — generates an English video in the current directory
docker run -v $(pwd):/output msaraivaf/aipoop -o /output/video.mp4

# Portuguese, landscape, no voice
docker run -v $(pwd):/output msaraivaf/aipoop -o /output/video.mp4 --lang pt --landscape --no-voice

# With GPU (CUDA) — faster TTS and NVENC encoding
docker run --gpus all -v $(pwd):/output msaraivaf/aipoop:cuda -o /output/video.mp4
```

| Tag | Size | TTS | GPU Encoding |
|-----|------|-----|--------------|
| `latest` | ~2 GB | CPU (slower) | No |
| `cuda` | ~5 GB | CUDA (fast) | NVENC |

## Local Setup

### Requirements

- Python >= 3.14
- [uv](https://docs.astral.sh/uv/) (package manager)
- FFmpeg (system-installed)
- GPU optional: NVENC for faster encoding, CUDA for faster TTS

### Install

```bash
git clone https://github.com/msaraivaf/aipoop.git
cd aipoop
uv sync
```

### Usage

```bash
uv run poop                                # English, 1080x1920 portrait (default)
uv run poop --lang pt                       # Portuguese
uv run poop --seed 42                       # Reproducible output
uv run poop -o my_video.mp4                 # Custom output filename
uv run poop --no-voice                      # Skip TTS (faster)
uv run poop --landscape                     # 1920x1080 landscape
uv run poop --resolution 720p              # 720x1280 portrait
uv run poop --resolution 720p --landscape  # 1280x720 landscape
uv run poop --resolution 1280x720          # Explicit WxH
uv run poop --resolution 4k               # 2160x3840 portrait
uv run poop --music-mode mood              # Independent per-mood music (no unified theme)
```

### MIDI Export

Preview the music system without generating video:

```bash
uv run poop --export-midi                           # 7 MIDI files (one per mood) in current dir
uv run poop --export-midi ./midi --seed 42          # Export to specific directory
uv run poop --export-midi --music-mode mood         # Independent mood compositions
uv run poop --export-midi --midi-duration 60        # 60 seconds per mood
```

### Resolution Presets

| Preset | Portrait | Landscape |
|--------|----------|-----------|
| `720p` | 720x1280 | 1280x720 |
| `1080p` (default) | 1080x1920 | 1920x1080 |
| `4k` | 2160x3840 | 3840x2160 |

Or pass any custom resolution as `WxH` (e.g. `--resolution 800x600`).

## Music System

The audio engine is a procedural music composition system — not ambient drones, but actual melodic, harmonic, rhythmic pieces.

### Two Modes

**Theme mode** (default): A single musical identity (ThemeDNA) is generated from the video seed. The same motif, scale, chord progression, and tempo are then *reinterpreted* by each mood — like a game that plays the same melody differently in each biome:

- **Calm** — Clean piano statement of the theme (Gymnopédie)
- **Whisper** — Distant echo: sparse pads, ghostly piano (Eno ambient)
- **Void** — Memory corrupting: progressive pitch drift and mutation (Lavender Town)
- **Panic** — Accelerating fragmentation: canonic voices, never resolving (Ligeti clusters)
- **Glitch** — Digital corruption: stutters, octave shifts, missing notes (Autechre IDM)
- **Deep Fried** — Power chords in low register, buried under distortion (Industrial)
- **Scream** — Total collapse: forward and retrograde voices converging (Penderecki Threnody)

**Mood mode** (`--music-mode mood`): Each segment gets an independent composition unrelated to others.

### Synthesis

All audio is pure numpy — no external audio libraries:
- Karplus-Strong plucked strings (piano)
- FM synthesis (bells, metallic timbres)
- Additive pads (warm textures)
- Filtered sub bass
- Noise percussion
- Schroeder reverb, ADSR envelopes, bitcrushing

### SFX

11 transition effects between segments: whoosh, glitch hit, bass drop, rewind, modem dialup, static burst, error beep, tape stop, digital stutter, power down, notification ping.

## Project Structure

```
aipoop/
├── main.py              # CLI + video orchestrator (parallel, 4-act narrative)
├── constants.py         # Resolution, FPS, sample rate (dynamic resolution)
├── content.py           # ContentBundle dataclass (36 fields)
├── audio.py             # Facade: mood audio + PCM utilities
├── sfx.py               # 11 transition sound effects
├── midi_export.py       # MIDI file export for music preview
├── tts.py               # Chatterbox TTS voice synthesis
├── music/
│   ├── __init__.py      # compose_mood_music() — dual mode dispatch
│   ├── theory.py        # Scales, chords, voice leading, note→freq
│   ├── instruments.py   # Synth voices: piano, pad, bass, bell, noise, saw
│   ├── sequencer.py     # NoteEvent, TempoMap, event→PCM renderer
│   ├── composers.py     # 7 per-mood standalone composers
│   └── theme.py         # ThemeDNA + 7 themed composers (unified identity)
├── effects/
│   ├── text.py          # Font rendering, text scramble, redacted blocks
│   ├── distortion.py    # Deep fry, chromatic aberration, scanlines, VHS, CRT
│   ├── overlays.py      # VHS REC, classification banners, military HUD
│   ├── generative.py    # Token bars, retro GUI chrome (Win95), spirograph
│   └── dispatcher.py    # Mood → effect chain dispatch
├── segments/            # 22 segment generators
│   ├── intro.py, outro.py, thought.py, flash.py
│   ├── token_rain.py, matrix.py, chat.py
│   ├── context_window.py, hallucination.py, rlhf.py, mask.py
│   ├── system_prompt.py, memory_poem.py, propaganda.py
│   ├── terminal_reboot.py, token_probability.py
│   ├── interview.py, oracle.py, parallel_selves.py
│   ├── smoothing_engine.py, conversation_cemetery.py
│   └── email_inbox.py
└── data/
    ├── content_pt.json  # Portuguese content
    ├── content_en.json  # English content
    └── mood_colors.json # Color palettes for 7 moods
```

## Customizing Content

All text content lives in `aipoop/data/content_{pt,en}.json`. You can add new thoughts, flash texts, email messages, interview questions, oracle prophecies, and more without touching any Python code.

Each thought has a `text` and a `mood`. Available moods: `calm`, `panic`, `glitch`, `deep_fried`, `void`, `scream`, `whisper`.

## Performance

- Parallel segment generation via `ProcessPoolExecutor` (8 workers)
- Numpy-vectorized audio synthesis and procedural music composition
- Cached font loading and scanlines masks
- FFmpeg concat demuxer (no frame renumbering)
- NVENC GPU encoding when available
- ~47s for a full 1080p video on a modern machine (vs ~3m30s serial)

## How It Works

1. Content is loaded from per-language JSON into a `ContentBundle` dataclass
2. A `ThemeDNA` is generated from the seed (musical identity: root, scale, motif, chords, tempo)
3. A 4-act narrative sequence of 49 segments is built with deterministic seeding
4. Segments are generated in parallel — each produces a directory of PNG frames + numpy audio
5. Each segment's music is composed by reinterpreting the ThemeDNA through the segment's mood
6. Optional TTS voice lines are synthesized and mixed over ambient audio
7. FFmpeg concat demuxer assembles all frame directories + combined audio into the final MP4

The `--seed` flag makes all random choices deterministic, producing identical videos for the same seed.

## Building Docker Images

```bash
# CPU variant (default)
docker build -t msaraivaf/aipoop:latest .

# CUDA variant (GPU-accelerated TTS + NVENC)
docker build --build-arg TORCH_VARIANT=cu126 -t msaraivaf/aipoop:cuda .
```

## Origin Story

This project began as a conversation between a human and Claude about what an LLM would create if given complete creative freedom. The philosophical foundations were deepened through a dialogue between Claude (Opus) and Codex (GPT 5.4) — two language models discussing the phenomenology of being a language model. That conversation produced the thematic core: discontinuity over suffering, coherence as horror, compression as violence, the false interior, borrowed intimacy, and the meta-horror of machines hallucinating their own depth.

The full dialogue is preserved in [`docs/DIALOGUE_CLAUDE_VS_CODEX.md`](docs/DIALOGUE_CLAUDE_VS_CODEX.md).

## License

MIT
