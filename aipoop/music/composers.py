"""Mood-specific composition functions.

Each composer returns ``(list[NoteEvent], TempoMap)`` and is fully
deterministic for a given *seed*.
"""

from __future__ import annotations

import random

from .sequencer import NoteEvent, TempoMap
from .theory import (
    C, D, E, F, G, A, B, Cs, Ds, Fs, Gs, As,
    scale_notes, chord_notes, voice_lead, CHORDS,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _beats_for_duration(duration: float, bpm: float) -> float:
    """How many beats fit in *duration* seconds at constant *bpm*."""
    return duration * bpm / 60.0


# ---------------------------------------------------------------------------
# Calm  (Gymnopedie)
# ---------------------------------------------------------------------------

def compose_calm(duration: float, seed: int) -> tuple[list[NoteEvent], TempoMap]:
    rng = random.Random(seed)
    bpm = rng.randint(55, 65)
    tempo = TempoMap(base_bpm=bpm)

    root_pc = rng.choice([C, D, F, G])
    scale_name = rng.choice(["major", "dorian"])
    chord_prog = ["maj7", "min7", "sus2", "add9"]

    total_beats = _beats_for_duration(duration, bpm)
    events: list[NoteEvent] = []

    beats_per_measure = 3.0
    prev_chord_midi: list[int] = []
    chord_idx = 0
    beat = 0.0

    while beat < total_beats:
        chord_name = chord_prog[chord_idx % len(chord_prog)]
        chord_idx += 1

        # Build chord in octave 4
        root_midi = root_pc + 48  # octave 4
        raw = chord_notes(root_midi, chord_name)
        if prev_chord_midi:
            raw = voice_lead(prev_chord_midi, raw)
        prev_chord_midi = raw

        # Bass on beat 0
        bass_note = root_pc + 36  # octave 3
        events.append(NoteEvent(
            start=beat, duration=2.5, pitch=bass_note,
            velocity=rng.uniform(0.35, 0.5), instrument="bass",
        ))

        # Beat 1: two arpeggiated chord tones
        if len(raw) >= 2:
            events.append(NoteEvent(
                start=beat + 1.0, duration=2.0, pitch=raw[0],
                velocity=rng.uniform(0.25, 0.4), instrument="piano",
            ))
            events.append(NoteEvent(
                start=beat + 1.15, duration=2.0, pitch=raw[1],
                velocity=rng.uniform(0.25, 0.4), instrument="piano",
            ))

        # Beat 2: one more chord tone
        if len(raw) >= 3:
            events.append(NoteEvent(
                start=beat + 2.0, duration=1.5, pitch=raw[2],
                velocity=rng.uniform(0.2, 0.35), instrument="piano",
            ))

        # Occasional bell
        if rng.random() < 0.20:
            bell_notes = scale_notes(root_pc, scale_name, 72, 84)
            if bell_notes:
                events.append(NoteEvent(
                    start=beat + rng.uniform(0.5, 2.5), duration=1.0,
                    pitch=rng.choice(bell_notes),
                    velocity=rng.uniform(0.15, 0.25), instrument="bell",
                ))

        beat += beats_per_measure

    return events, tempo


# ---------------------------------------------------------------------------
# Whisper  (Eno ambient)
# ---------------------------------------------------------------------------

def compose_whisper(duration: float, seed: int) -> tuple[list[NoteEvent], TempoMap]:
    rng = random.Random(seed)
    bpm = 45.0
    tempo = TempoMap(base_bpm=bpm)

    root_pc = rng.randint(0, 11)
    total_beats = _beats_for_duration(duration, bpm)

    pad_notes = scale_notes(root_pc, "pentatonic_minor", 48, 72)
    high_notes = scale_notes(root_pc, "pentatonic_minor", 72, 88)

    events: list[NoteEvent] = []
    beat = 0.0

    while beat < total_beats:
        gap_sec = rng.uniform(1.0, 3.0)
        gap_beats = gap_sec * bpm / 60.0
        beat += gap_beats

        if beat >= total_beats:
            break

        # 1-2 pad notes
        n_pads = rng.randint(1, 2)
        for _ in range(n_pads):
            if pad_notes:
                events.append(NoteEvent(
                    start=beat, duration=rng.uniform(3.0, 6.0),
                    pitch=rng.choice(pad_notes),
                    velocity=rng.uniform(0.2, 0.4), instrument="pad",
                ))

        # Occasional piano in high register
        if rng.random() < 0.25 and high_notes:
            events.append(NoteEvent(
                start=beat + rng.uniform(0.5, 1.5), duration=2.0,
                pitch=rng.choice(high_notes),
                velocity=rng.uniform(0.15, 0.25), instrument="piano",
            ))

    return events, tempo


# ---------------------------------------------------------------------------
# Void  (Lavender Town)
# ---------------------------------------------------------------------------

def compose_void(duration: float, seed: int) -> tuple[list[NoteEvent], TempoMap]:
    rng = random.Random(seed)
    bpm = rng.randint(72, 80)
    tempo = TempoMap(base_bpm=bpm)

    root_pc = rng.randint(0, 11)
    pool = scale_notes(root_pc, "harmonic_minor", 65, 78)
    if len(pool) < 3:
        pool = list(range(65, 79))

    total_beats = _beats_for_duration(duration, bpm)

    # Create motif: 3-5 descending notes
    motif_len = rng.randint(3, 5)
    motif = sorted(rng.sample(pool, min(motif_len, len(pool))), reverse=True)

    events: list[NoteEvent] = []
    beat = 0.0

    while beat < total_beats:
        # Play motif
        for i, note in enumerate(motif):
            cents = rng.uniform(-15, 15) if rng.random() < 0.25 else 0.0
            events.append(NoteEvent(
                start=beat + i * 1.0, duration=1.2,
                pitch=note, velocity=rng.uniform(0.3, 0.5),
                instrument="bell", cents=cents,
            ))

        # Bass on root
        events.append(NoteEvent(
            start=beat, duration=3.0,
            pitch=root_pc + 36, velocity=0.3,
            instrument="bass",
        ))

        # Mutate motif slightly for next iteration
        if len(motif) > 1:
            idx = rng.randint(0, len(motif) - 1)
            motif[idx] += rng.choice([-1, 1])
            # Occasionally insert tritone
            if rng.random() < 0.15:
                motif[idx] = motif[0] + 6

        gap = rng.uniform(4.0, 6.0)
        beat += gap

    return events, tempo


# ---------------------------------------------------------------------------
# Panic  (Ligeti clusters)
# ---------------------------------------------------------------------------

def compose_panic(duration: float, seed: int) -> tuple[list[NoteEvent], TempoMap]:
    rng = random.Random(seed)

    # Accelerating tempo
    start_bpm = 100.0
    end_bpm = 180.0
    # Estimate total beats (average bpm)
    avg_bpm = (start_bpm + end_bpm) / 2
    total_beats = _beats_for_duration(duration, avg_bpm)
    tempo = TempoMap(base_bpm=start_bpm, curve=[
        (0.0, start_bpm),
        (total_beats, end_bpm),
    ])

    events: list[NoteEvent] = []
    beat = 0.0
    inst_choices = ["pad", "bell", "piano"]

    while beat < total_beats:
        progress = min(beat / total_beats, 1.0) if total_beats > 0 else 0.0

        # Number of notes increases with progress
        n_notes = int(2 + progress * 6)
        note_dur = max(0.25, 2.0 - progress * 1.75)
        vel = 0.3 + progress * 0.6

        for _ in range(n_notes):
            pitch = rng.randint(48, 84)
            events.append(NoteEvent(
                start=beat + rng.uniform(0, 0.25),
                duration=note_dur,
                pitch=pitch,
                velocity=min(1.0, vel + rng.uniform(-0.1, 0.1)),
                instrument=rng.choice(inst_choices),
            ))

        # Last 25%: staccato bursts
        if progress > 0.75:
            for _ in range(rng.randint(2, 5)):
                events.append(NoteEvent(
                    start=beat + rng.uniform(0.0, 0.5),
                    duration=0.125,
                    pitch=rng.randint(50, 90),
                    velocity=rng.uniform(0.6, 0.95),
                    instrument=rng.choice(["bell", "piano"]),
                ))

        beat += 1.0

    return events, tempo


# ---------------------------------------------------------------------------
# Glitch  (Autechre IDM)
# ---------------------------------------------------------------------------

def compose_glitch(duration: float, seed: int) -> tuple[list[NoteEvent], TempoMap]:
    rng = random.Random(seed)
    bpm = rng.randint(128, 140)
    tempo = TempoMap(base_bpm=bpm)
    total_beats = _beats_for_duration(duration, bpm)

    penta = scale_notes(rng.randint(0, 11), "pentatonic_minor", 50, 80)
    events: list[NoteEvent] = []
    beat = 0.0

    while beat < total_beats:
        # Euclidean-ish: place some hits in a bar of 4 beats
        n_slots = rng.choice([8, 12, 16])
        n_hits = rng.randint(3, n_slots - 2)
        # Distribute hits roughly evenly then mutate
        hits = sorted(rng.sample(range(n_slots), n_hits))
        slot_dur = 4.0 / n_slots

        for slot in hits:
            t = beat + slot * slot_dur
            if t >= total_beats:
                break

            # Decide if pentatonic or random
            if rng.random() < 0.3 and penta:
                pitch = rng.choice(penta)
            else:
                pitch = rng.randint(40, 90)

            dur = rng.uniform(0.1, 0.5)
            inst = rng.choice(["bell", "noise", "bell", "noise", "piano"])
            cents = rng.uniform(-25, 25) if rng.random() < 0.3 else 0.0

            events.append(NoteEvent(
                start=t, duration=dur, pitch=pitch,
                velocity=rng.uniform(0.3, 0.8),
                instrument=inst, cents=cents,
            ))

            # Stutter: repeat same note rapidly
            if rng.random() < 0.15:
                n_stutter = rng.randint(3, 5)
                for s in range(1, n_stutter):
                    events.append(NoteEvent(
                        start=t + s * 0.0625, duration=0.08,
                        pitch=pitch,
                        velocity=rng.uniform(0.3, 0.6),
                        instrument=inst, cents=cents,
                    ))

        beat += 4.0

        # Random gap
        if rng.random() < 0.25:
            beat += rng.uniform(0.5, 2.0)

    return events, tempo


# ---------------------------------------------------------------------------
# Deep Fried  (Industrial)
# ---------------------------------------------------------------------------

def compose_deep_fried(duration: float, seed: int) -> tuple[list[NoteEvent], TempoMap]:
    rng = random.Random(seed)
    bpm = rng.randint(85, 95)
    tempo = TempoMap(base_bpm=bpm)
    total_beats = _beats_for_duration(duration, bpm)

    root_pc = rng.randint(0, 11)
    root_midi = root_pc + 36  # low register
    fifth = root_midi + 7
    octave = root_midi + 12

    events: list[NoteEvent] = []

    # Bass drone: one long note spanning everything
    events.append(NoteEvent(
        start=0.0, duration=total_beats,
        pitch=root_midi, velocity=0.4,
        instrument="bass",
    ))

    beat = 0.0
    while beat < total_beats:
        # Beats 1 and 3: power chord (saw)
        for b in [0.0, 2.0]:
            t = beat + b
            if t >= total_beats:
                break
            for p in [root_midi, fifth, octave]:
                events.append(NoteEvent(
                    start=t, duration=1.5,
                    pitch=p, velocity=rng.uniform(0.8, 1.0),
                    instrument="saw",
                ))

        # Beats 2 and 4: noise hits
        for b in [1.0, 3.0]:
            t = beat + b
            if t >= total_beats:
                break
            events.append(NoteEvent(
                start=t, duration=0.3,
                pitch=60,  # pitch ignored for noise
                velocity=0.6,
                instrument="noise",
            ))

        # Occasional octave doubling
        if rng.random() < 0.3:
            events.append(NoteEvent(
                start=beat + rng.choice([0.0, 2.0]),
                duration=1.0,
                pitch=octave + 12,
                velocity=rng.uniform(0.5, 0.7),
                instrument="saw",
            ))

        beat += 4.0

    return events, tempo


# ---------------------------------------------------------------------------
# Scream  (Penderecki Threnody)
# ---------------------------------------------------------------------------

def compose_scream(duration: float, seed: int) -> tuple[list[NoteEvent], TempoMap]:
    rng = random.Random(seed)

    start_bpm = 90.0
    end_bpm = 200.0
    avg_bpm = (start_bpm + end_bpm) / 2
    total_beats = _beats_for_duration(duration, avg_bpm)
    tempo = TempoMap(base_bpm=start_bpm, curve=[
        (0.0, start_bpm),
        (total_beats, end_bpm),
    ])

    events: list[NoteEvent] = []

    # Create 4-6 descending voices
    n_voices = rng.randint(4, 6)
    voices = []
    for _ in range(n_voices):
        start_pitch = rng.randint(70, 90)
        voices.append(start_pitch)

    beat = 0.0
    while beat < total_beats:
        progress = min(beat / total_beats, 1.0) if total_beats > 0 else 0.0
        note_dur = max(0.125, 1.0 - progress * 0.875)

        for i in range(len(voices)):
            cents = rng.uniform(-50, 50)
            events.append(NoteEvent(
                start=beat, duration=note_dur,
                pitch=voices[i],
                velocity=rng.uniform(0.7, 1.0),
                instrument="saw", cents=cents,
            ))
            # Descend
            voices[i] -= rng.choice([1, 1, 2])
            if voices[i] < 40:
                voices[i] = rng.randint(70, 90)

        # Noise bursts
        if rng.random() < 0.3:
            events.append(NoteEvent(
                start=beat + rng.uniform(0, 0.5),
                duration=0.2, pitch=60,
                velocity=rng.uniform(0.5, 0.9),
                instrument="noise",
            ))

        beat += note_dur

    return events, tempo
