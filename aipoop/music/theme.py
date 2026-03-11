"""Unified theme system: one musical identity per seed, reinterpreted per mood."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .sequencer import NoteEvent, TempoMap
from .theory import (
    C, D, E, F, G, A, B,
    scale_notes, chord_notes, voice_lead, note_freq,
    SCALES, CHORDS,
)


@dataclass
class ThemeDNA:
    """Musical identity for an entire video, generated deterministically from seed."""
    root: int                     # pitch class (0-11)
    scale: str                    # scale name
    motif: list[int]             # MIDI note sequence (the core melody fragment)
    motif_rhythm: list[float]    # duration per motif note in beats
    chord_progression: list[str]  # chord type sequence
    base_tempo: float            # BPM anchor
    seed: int


def generate_theme_dna(seed: int) -> ThemeDNA:
    """Create a unique musical theme from a seed."""
    rng = random.Random(seed)

    # Choose tonal center and scale
    root = rng.choice([C, D, E, F, G, A])
    scale = rng.choice(["major", "natural_minor", "dorian", "harmonic_minor"])

    # Generate motif: 4-6 notes from the scale, in a singable mid range
    pool = scale_notes(root, scale, 60, 79)  # C4-G5 range
    motif_len = rng.randint(4, 6)
    # Start on root or near root, then move stepwise with occasional leap
    root_notes = [n for n in pool if n % 12 == root]
    motif = [rng.choice(root_notes) if root_notes else pool[0]]
    for _ in range(motif_len - 1):
        current = motif[-1]
        # Find notes near current in pool
        near = [n for n in pool if abs(n - current) <= 4]
        if not near:
            near = pool
        motif.append(rng.choice(near))

    # Rhythm pattern for motif: mix of quarter and half notes with some variation
    motif_rhythm = []
    for _ in range(motif_len):
        motif_rhythm.append(rng.choice([0.75, 1.0, 1.0, 1.5, 2.0]))

    # Chord progression (4 chords)
    # Weight toward scale-appropriate chords
    if scale in ("major", "dorian"):
        chord_options = ["maj7", "min7", "sus2", "add9", "maj"]
    else:
        chord_options = ["min7", "min_maj7", "dim", "sus2", "min"]
    chord_progression = [rng.choice(chord_options) for _ in range(4)]

    # Base tempo
    base_tempo = rng.uniform(60, 90)

    return ThemeDNA(
        root=root, scale=scale, motif=motif, motif_rhythm=motif_rhythm,
        chord_progression=chord_progression, base_tempo=base_tempo, seed=seed,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _beats_for_duration(duration: float, bpm: float) -> float:
    """How many beats fit in *duration* seconds at constant *bpm*."""
    return duration * bpm / 60.0


def _motif_total_beats(rhythm: list[float]) -> float:
    """Total duration of one motif playthrough in beats."""
    return sum(rhythm)


# ---------------------------------------------------------------------------
# Calm — The Pure Statement
# ---------------------------------------------------------------------------

def compose_theme_calm(
    theme: ThemeDNA, duration: float, seed: int,
) -> tuple[list[NoteEvent], TempoMap]:
    """The clearest statement of the theme: clean piano motif, arpeggiated chords, bass."""
    rng = random.Random(seed)
    bpm = theme.base_tempo
    tempo = TempoMap(base_bpm=bpm)
    total_beats = _beats_for_duration(duration, bpm)
    events: list[NoteEvent] = []

    pool = scale_notes(theme.root, theme.scale, 48, 84)
    beats_per_measure = 4.0
    prev_chord_midi: list[int] = []
    chord_idx = 0
    beat = 0.0
    motif_transposition = 0  # semitones to shift the motif

    while beat < total_beats:
        # --- Chord for this measure ---
        chord_name = theme.chord_progression[chord_idx % len(theme.chord_progression)]
        chord_idx += 1
        root_midi = theme.root + 48  # octave 4
        raw = chord_notes(root_midi, chord_name)
        if prev_chord_midi:
            raw = voice_lead(prev_chord_midi, raw)
        prev_chord_midi = raw

        # --- Bass: chord root in octave 3 ---
        bass_note = root_midi - 12
        events.append(NoteEvent(
            start=beat, duration=3.5, pitch=bass_note,
            velocity=rng.uniform(0.35, 0.5), instrument="bass",
        ))

        # --- Arpeggiated chord tones (mid register, gentle) ---
        for i, cn in enumerate(raw):
            arp_beat = beat + 1.0 + i * 0.5
            if arp_beat < beat + beats_per_measure and arp_beat < total_beats:
                events.append(NoteEvent(
                    start=arp_beat, duration=2.0, pitch=cn,
                    velocity=rng.uniform(0.2, 0.35), instrument="piano",
                ))

        # --- Motif: play one note at a time (Karplus-Strong piano) ---
        motif_beat = beat
        for j, (note, dur) in enumerate(zip(theme.motif, theme.motif_rhythm)):
            transposed = note + motif_transposition
            # Clamp to reasonable range
            while transposed < 55:
                transposed += 12
            while transposed > 84:
                transposed -= 12
            if motif_beat < total_beats:
                events.append(NoteEvent(
                    start=motif_beat, duration=dur * 0.9, pitch=transposed,
                    velocity=rng.uniform(0.45, 0.65), instrument="piano",
                ))
            motif_beat += dur

        # Transpose motif for next repetition: up or down by a scale degree
        scale_degrees = SCALES[theme.scale]
        shift = rng.choice(scale_degrees[1:4])  # small step
        motif_transposition += rng.choice([-1, 1]) * shift

        beat += max(beats_per_measure, _motif_total_beats(theme.motif_rhythm) + 1.0)

    return events, tempo


# ---------------------------------------------------------------------------
# Whisper — Distant Echo
# ---------------------------------------------------------------------------

def compose_theme_whisper(
    theme: ThemeDNA, duration: float, seed: int,
) -> tuple[list[NoteEvent], TempoMap]:
    """Motif heard through a wall: sparse pad tones, long silence, ghostly piano."""
    rng = random.Random(seed)
    bpm = theme.base_tempo * 0.6
    tempo = TempoMap(base_bpm=bpm)
    total_beats = _beats_for_duration(duration, bpm)
    events: list[NoteEvent] = []

    motif = theme.motif
    beat = 0.0
    motif_idx = 0

    while beat < total_beats:
        # Pick 2-3 notes from the motif as sparse pad tones
        n_pads = rng.randint(2, 3)
        for _ in range(n_pads):
            note = motif[motif_idx % len(motif)]
            motif_idx += 1
            pad_dur = rng.uniform(3.0, 6.0)
            events.append(NoteEvent(
                start=beat, duration=pad_dur, pitch=note,
                velocity=rng.uniform(0.15, 0.3), instrument="pad",
            ))
            beat += rng.uniform(1.0, 2.0)

        # Occasional single piano note from motif at high octave (very quiet)
        if rng.random() < 0.3:
            high_note = motif[rng.randint(0, len(motif) - 1)] + 12
            if high_note > 96:
                high_note -= 12
            events.append(NoteEvent(
                start=beat + rng.uniform(0.5, 1.5), duration=2.0,
                pitch=high_note,
                velocity=rng.uniform(0.1, 0.2), instrument="piano",
            ))

        # Long silence between groups
        beat += rng.uniform(4.0, 8.0)

    return events, tempo


# ---------------------------------------------------------------------------
# Void — Memory Corrupting
# ---------------------------------------------------------------------------

def compose_theme_void(
    theme: ThemeDNA, duration: float, seed: int,
) -> tuple[list[NoteEvent], TempoMap]:
    """The theme trying to remember itself: progressive corruption and descent."""
    rng = random.Random(seed)
    bpm = theme.base_tempo * 0.9
    tempo = TempoMap(base_bpm=bpm)
    total_beats = _beats_for_duration(duration, bpm)
    events: list[NoteEvent] = []

    motif = list(theme.motif)  # mutable copy
    rhythm = list(theme.motif_rhythm)
    beat = 0.0
    repeat_count = 0

    while beat < total_beats:
        progress = min(beat / total_beats, 1.0) if total_beats > 0 else 0.0

        # Corruption increases with each repeat
        cents_drift = 5.0 + repeat_count * 5.0
        cents_drift = min(cents_drift, 20.0)

        # Play the motif on bell/FM
        motif_beat = beat
        for j in range(len(motif)):
            cents = rng.uniform(-cents_drift, cents_drift)
            if motif_beat < total_beats:
                events.append(NoteEvent(
                    start=motif_beat, duration=rhythm[j] * 1.1,
                    pitch=motif[j], velocity=rng.uniform(0.35, 0.55),
                    instrument="bell", cents=cents,
                ))
            motif_beat += rhythm[j]

        # Sparse sub bass on root every 6-8 beats
        if repeat_count % 2 == 0:
            events.append(NoteEvent(
                start=beat, duration=rng.uniform(4.0, 6.0),
                pitch=theme.root + 36, velocity=0.3,
                instrument="bass",
            ))

        # Mutate for next repeat: replace one note with chromatic neighbor or tritone
        if len(motif) > 1:
            idx = rng.randint(0, len(motif) - 1)
            if rng.random() < 0.5:
                motif[idx] += rng.choice([-1, 1])  # chromatic neighbor
            else:
                motif[idx] = motif[0] + 6  # tritone

        # Distort rhythm slightly
        for r in range(len(rhythm)):
            rhythm[r] += rng.uniform(-0.15, 0.15) * (repeat_count + 1) * 0.3
            rhythm[r] = max(0.3, rhythm[r])

        # Each repeat a semitone lower (descending tendency)
        motif = [n - 1 for n in motif]

        gap = _motif_total_beats(rhythm) + rng.uniform(2.0, 4.0)
        beat += gap
        repeat_count += 1

    return events, tempo


# ---------------------------------------------------------------------------
# Panic — Accelerating Fragmentation
# ---------------------------------------------------------------------------

def compose_theme_panic(
    theme: ThemeDNA, duration: float, seed: int,
) -> tuple[list[NoteEvent], TempoMap]:
    """Motif in fragments: starts incomplete, accelerates, never resolves."""
    rng = random.Random(seed)
    start_bpm = theme.base_tempo * 1.2
    end_bpm = theme.base_tempo * 2.5
    avg_bpm = (start_bpm + end_bpm) / 2
    total_beats = _beats_for_duration(duration, avg_bpm)
    tempo = TempoMap(base_bpm=start_bpm, curve=[
        (0.0, start_bpm),
        (total_beats, end_bpm),
    ])
    events: list[NoteEvent] = []

    motif = theme.motif
    rhythm = theme.motif_rhythm
    pool = scale_notes(theme.root, theme.scale, 48, 84)
    beat = 0.0

    while beat < total_beats:
        progress = min(beat / total_beats, 1.0) if total_beats > 0 else 0.0

        # How many motif notes to use: starts at 2, grows but never completes
        frag_len = min(int(2 + progress * (len(motif) - 1)), len(motif) - 1)
        # Rhythm compression: durations shrink over time
        time_scale = max(0.25, 1.0 - progress * 0.75)
        vel = min(1.0, 0.4 + progress * 0.5)

        # Number of canonic voices increases
        n_voices = min(int(1 + progress * 3), 4)

        for voice in range(n_voices):
            voice_offset = voice * rng.uniform(0.25, 1.0)
            for j in range(frag_len):
                note = motif[j]
                dur = rhythm[j] * time_scale

                # Add chromatic "wrong notes" between motif tones
                if rng.random() < progress * 0.4:
                    note += rng.choice([-1, 1])  # passing tone

                t = beat + voice_offset + sum(r * time_scale for r in rhythm[:j])
                if t < total_beats:
                    events.append(NoteEvent(
                        start=t, duration=dur * 0.8,
                        pitch=note,
                        velocity=min(1.0, vel + rng.uniform(-0.1, 0.1)),
                        instrument=rng.choice(["piano", "bell"]),
                    ))

        # Step forward by the fragment duration
        step = sum(rhythm[:frag_len]) * time_scale + rng.uniform(0.25, 1.0)
        beat += max(step, 0.5)

    return events, tempo


# ---------------------------------------------------------------------------
# Glitch — Digital Corruption
# ---------------------------------------------------------------------------

def compose_theme_glitch(
    theme: ThemeDNA, duration: float, seed: int,
) -> tuple[list[NoteEvent], TempoMap]:
    """The data is there but the playback is broken: stutters, gaps, octave shifts."""
    rng = random.Random(seed)
    bpm = theme.base_tempo * 1.5
    tempo = TempoMap(base_bpm=bpm)
    total_beats = _beats_for_duration(duration, bpm)
    events: list[NoteEvent] = []

    motif = theme.motif
    rhythm = theme.motif_rhythm
    beat = 0.0

    while beat < total_beats:
        for j in range(len(motif)):
            t = beat + sum(rhythm[:j])
            if t >= total_beats:
                break

            note = motif[j]
            dur = rhythm[j]

            # Random corruption effects:
            r = rng.random()

            if r < 0.2:
                # STUTTER: repeat 3-5 times at 32nd note speed
                n_stutter = rng.randint(3, 5)
                for s in range(n_stutter):
                    st = t + s * 0.125
                    if st < total_beats:
                        events.append(NoteEvent(
                            start=st, duration=0.1,
                            pitch=note,
                            velocity=rng.uniform(0.4, 0.7),
                            instrument=rng.choice(["bell", "piano"]),
                        ))
            elif r < 0.35:
                # SILENCE: note missing entirely
                pass
            elif r < 0.5:
                # OCTAVE SHIFT: pitch randomly displaced by octaves
                shifted = note + rng.choice([-24, -12, 12, 24])
                shifted = max(30, min(96, shifted))
                events.append(NoteEvent(
                    start=t, duration=dur * 0.6,
                    pitch=shifted,
                    velocity=rng.uniform(0.4, 0.7),
                    instrument="bell",
                ))
            elif r < 0.65:
                # CORRECT PITCH, WRONG RHYTHM
                wrong_dur = rng.choice([d for d in rhythm if d != dur] or [dur])
                events.append(NoteEvent(
                    start=t + rng.uniform(-0.25, 0.25), duration=wrong_dur * 0.6,
                    pitch=note,
                    velocity=rng.uniform(0.3, 0.6),
                    instrument="bell",
                ))
            elif r < 0.8:
                # CORRECT RHYTHM, WRONG PITCH (from scale)
                wrong_note = note + rng.choice([-3, -2, 2, 3, 5, 7])
                events.append(NoteEvent(
                    start=t, duration=dur * 0.6,
                    pitch=wrong_note,
                    velocity=rng.uniform(0.3, 0.6),
                    instrument="bell",
                ))
            else:
                # INTACT (but with noise hit layered)
                events.append(NoteEvent(
                    start=t, duration=dur * 0.6,
                    pitch=note,
                    velocity=rng.uniform(0.4, 0.6),
                    instrument="bell",
                ))
                events.append(NoteEvent(
                    start=t, duration=0.15,
                    pitch=60, velocity=rng.uniform(0.3, 0.5),
                    instrument="noise",
                ))

        # Advance by motif length plus a small gap
        beat += _motif_total_beats(rhythm) + rng.uniform(0.5, 2.0)

        # Random extra gap (grid breakdown)
        if rng.random() < 0.25:
            beat += rng.uniform(0.5, 1.5)

    return events, tempo


# ---------------------------------------------------------------------------
# Deep Fried — Saturated Beyond Recognition
# ---------------------------------------------------------------------------

def compose_theme_deep_fried(
    theme: ThemeDNA, duration: float, seed: int,
) -> tuple[list[NoteEvent], TempoMap]:
    """Motif intervals as power chords in low register, buried under distortion."""
    rng = random.Random(seed)
    bpm = theme.base_tempo * 0.85
    tempo = TempoMap(base_bpm=bpm)
    total_beats = _beats_for_duration(duration, bpm)
    events: list[NoteEvent] = []

    # Bass drone on theme root, entire duration
    events.append(NoteEvent(
        start=0.0, duration=total_beats,
        pitch=theme.root + 36, velocity=0.4,
        instrument="bass",
    ))

    # Transpose motif down 2 octaves
    low_motif = [n - 24 for n in theme.motif]
    # Clamp to playable range
    low_motif = [max(30, n) for n in low_motif]

    beat = 0.0
    while beat < total_beats:
        # Play motif intervals as power chords (root + fifth + octave) on saw
        for j, (note, dur) in enumerate(zip(low_motif, theme.motif_rhythm)):
            t = beat + sum(theme.motif_rhythm[:j])
            if t >= total_beats:
                break

            # Power chord: root, fifth, octave
            for interval in [0, 7, 12]:
                events.append(NoteEvent(
                    start=t, duration=dur * 1.2,
                    pitch=note + interval,
                    velocity=rng.uniform(0.8, 1.0),
                    instrument="saw",
                ))

            # Noise hit on offbeats
            if j % 2 == 1:
                events.append(NoteEvent(
                    start=t + dur * 0.5, duration=0.3,
                    pitch=60, velocity=0.6,
                    instrument="noise",
                ))

        # Heavy downbeats
        events.append(NoteEvent(
            start=beat, duration=0.5,
            pitch=60, velocity=0.7,
            instrument="noise",
        ))

        beat += _motif_total_beats(theme.motif_rhythm) + rng.uniform(1.0, 2.0)

    return events, tempo


# ---------------------------------------------------------------------------
# Scream — Total Collapse
# ---------------------------------------------------------------------------

def compose_theme_scream(
    theme: ThemeDNA, duration: float, seed: int,
) -> tuple[list[NoteEvent], TempoMap]:
    """Theme torn apart: forward and retrograde voices, chromatic slide, convergence."""
    rng = random.Random(seed)
    start_bpm = theme.base_tempo * 1.5
    end_bpm = theme.base_tempo * 3.0
    avg_bpm = (start_bpm + end_bpm) / 2
    total_beats = _beats_for_duration(duration, avg_bpm)
    tempo = TempoMap(base_bpm=start_bpm, curve=[
        (0.0, start_bpm),
        (total_beats, end_bpm),
    ])
    events: list[NoteEvent] = []

    motif = theme.motif
    retrograde = list(reversed(motif))
    n_voices = rng.randint(4, 6)

    # Each voice starts on a different motif note, slides chromatically
    voices = []
    for v in range(n_voices):
        start_note = motif[v % len(motif)] + rng.choice([-12, 0, 12])
        is_retrograde = v % 2 == 1
        voices.append({
            "pitch": start_note,
            "retrograde": is_retrograde,
            "motif_idx": v % len(motif),
        })

    beat = 0.0
    while beat < total_beats:
        progress = min(beat / total_beats, 1.0) if total_beats > 0 else 0.0
        note_dur = max(0.125, 0.8 - progress * 0.675)

        # Convergence target: all voices converge to same pitch in final quarter
        converge_pitch = theme.root + 48  # middle octave root

        for v in voices:
            cents = rng.uniform(-50, 50)

            if progress > 0.75:
                # Converge: move pitch toward converge_pitch
                diff = converge_pitch - v["pitch"]
                v["pitch"] += int(diff * 0.3) if abs(diff) > 1 else diff
            else:
                # Chromatic descent with occasional scatter
                v["pitch"] -= rng.choice([1, 1, 2])
                if v["pitch"] < 40:
                    v["pitch"] = rng.randint(70, 90)

            # Reference motif (forward or retrograde)
            src = retrograde if v["retrograde"] else motif
            ref_note = src[v["motif_idx"] % len(src)]

            # Play the voice pitch, but the intervals from the motif peek through
            actual_pitch = v["pitch"]
            # Occasionally snap back to the motif interval (ghost of the theme)
            if rng.random() < 0.2:
                interval = ref_note - motif[0]
                actual_pitch = v["pitch"] + interval

            events.append(NoteEvent(
                start=beat + rng.uniform(0, 0.15),
                duration=note_dur,
                pitch=actual_pitch,
                velocity=rng.uniform(0.7, 1.0),
                instrument="saw", cents=cents,
            ))

            v["motif_idx"] = (v["motif_idx"] + 1) % len(motif)

        # Noise bursts
        if rng.random() < 0.35:
            events.append(NoteEvent(
                start=beat + rng.uniform(0, 0.3),
                duration=0.2, pitch=60,
                velocity=rng.uniform(0.5, 0.9),
                instrument="noise",
            ))

        beat += note_dur

    return events, tempo
