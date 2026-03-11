"""Export the procedural music system to MIDI files for preview."""

from __future__ import annotations

from midiutil import MIDIFile

from .music import generate_theme_dna
from .music.sequencer import NoteEvent, TempoMap
from .music.theme import (
    compose_theme_calm,
    compose_theme_whisper,
    compose_theme_void,
    compose_theme_panic,
    compose_theme_glitch,
    compose_theme_deep_fried,
    compose_theme_scream,
)
from .music.composers import (
    compose_calm,
    compose_whisper,
    compose_void,
    compose_panic,
    compose_glitch,
    compose_deep_fried,
    compose_scream,
)


# Map instruments to MIDI channels/programs
_INSTRUMENT_PROGRAMS = {
    "piano": 0,      # Acoustic Grand Piano
    "bass": 32,      # Acoustic Bass
    "pad": 89,       # Pad 2 (warm)
    "bell": 14,      # Tubular Bells
    "saw": 81,       # Lead 2 (sawtooth)
    "noise": 127,    # Gunshot (percussion-ish, channel 9)
}

_INSTRUMENT_CHANNEL = {
    "piano": 0,
    "bass": 1,
    "pad": 2,
    "bell": 3,
    "saw": 4,
    "noise": 9,  # GM percussion channel
}

_THEME_COMPOSERS = {
    "calm": compose_theme_calm,
    "whisper": compose_theme_whisper,
    "void": compose_theme_void,
    "panic": compose_theme_panic,
    "glitch": compose_theme_glitch,
    "deep_fried": compose_theme_deep_fried,
    "scream": compose_theme_scream,
}

_MOOD_COMPOSERS = {
    "calm": compose_calm,
    "whisper": compose_whisper,
    "void": compose_void,
    "panic": compose_panic,
    "glitch": compose_glitch,
    "deep_fried": compose_deep_fried,
    "scream": compose_scream,
}


def events_to_midi(
    events: list[NoteEvent],
    tempo: TempoMap,
    output_path: str,
    title: str = "aipoop",
) -> None:
    """Convert NoteEvents to a MIDI file."""
    n_tracks = 6  # one per instrument family
    midi = MIDIFile(n_tracks, deinterleave=False)

    bpm = tempo.base_bpm
    midi.addTempo(0, 0, bpm)

    # Set up programs on each channel
    assigned_tracks: dict[str, int] = {}
    track_idx = 0
    for inst, program in _INSTRUMENT_PROGRAMS.items():
        ch = _INSTRUMENT_CHANNEL[inst]
        t = track_idx if ch != 9 else min(track_idx, n_tracks - 1)
        if ch != 9:
            midi.addProgramChange(t, ch, 0, program)
        assigned_tracks[inst] = t
        track_idx = min(track_idx + 1, n_tracks - 1)

    # Add tempo curve if present
    if tempo.curve and len(tempo.curve) > 1:
        for beat, bpm_val in tempo.curve:
            midi.addTempo(0, max(0, beat), bpm_val)

    for ev in events:
        inst = ev.instrument
        ch = _INSTRUMENT_CHANNEL.get(inst, 0)
        track = assigned_tracks.get(inst, 0)
        pitch = max(0, min(127, ev.pitch))
        vel = max(1, min(127, int(ev.velocity * 127)))
        start = max(0.0, ev.start)
        dur = max(0.01, ev.duration)
        midi.addNote(track, ch, pitch, start, dur, vel)

    with open(output_path, "wb") as f:
        midi.writeFile(f)


def export_theme_midi(
    seed: int,
    mood: str,
    duration: float,
    output_path: str,
    mode: str = "theme",
) -> None:
    """Generate and export a single mood as MIDI."""
    theme = generate_theme_dna(seed)

    if mode == "theme":
        composer = _THEME_COMPOSERS.get(mood)
        if composer is None:
            raise ValueError(f"Unknown mood: {mood}")
        events, tempo = composer(theme, duration, seed)
    else:
        composer = _MOOD_COMPOSERS.get(mood)
        if composer is None:
            raise ValueError(f"Unknown mood: {mood}")
        events, tempo = composer(duration, seed)

    title = f"aipoop seed={seed} {mode}/{mood}"
    events_to_midi(events, tempo, output_path, title)


def export_all_moods_midi(
    seed: int,
    duration: float,
    output_dir: str,
    mode: str = "theme",
) -> list[str]:
    """Export all 7 moods as separate MIDI files. Returns list of paths."""
    import os
    os.makedirs(output_dir, exist_ok=True)

    paths = []
    moods = ["calm", "whisper", "void", "panic", "glitch", "deep_fried", "scream"]
    for mood in moods:
        path = os.path.join(output_dir, f"{mode}_{mood}_seed{seed}.mid")
        export_theme_midi(seed, mood, duration, path, mode)
        paths.append(path)

    return paths
