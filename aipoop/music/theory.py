"""Musical theory primitives for procedural composition.

Pure-Python module providing MIDI/frequency conversion, scale and chord
definitions, voice leading, and helper utilities.  No external dependencies
beyond the standard library.
"""

from __future__ import annotations

import random

# ---------------------------------------------------------------------------
# Pitch-class constants (C = 0 … B = 11)
# ---------------------------------------------------------------------------

C, Cs, D, Ds, E, F, Fs, G, Gs, A, As, B = range(12)

# ---------------------------------------------------------------------------
# MIDI ↔ frequency conversion
# ---------------------------------------------------------------------------


def note_freq(midi_note: int, cents: float = 0.0) -> float:
    """Convert a MIDI note number to frequency in Hz.

    Uses the standard A4 = 440 Hz tuning (MIDI note 69).  An optional
    *cents* offset allows microtonal adjustments (100 cents = 1 semitone).

    >>> round(note_freq(69), 2)
    440.0
    >>> round(note_freq(60), 2)   # Middle C
    261.63
    """
    return 440.0 * 2.0 ** ((midi_note - 69 + cents / 100.0) / 12.0)


# ---------------------------------------------------------------------------
# Scale definitions — semitone intervals from root
# ---------------------------------------------------------------------------

SCALES: dict[str, list[int]] = {
    "major":           [0, 2, 4, 5, 7, 9, 11],
    "natural_minor":   [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor":  [0, 2, 3, 5, 7, 8, 11],
    "dorian":          [0, 2, 3, 5, 7, 9, 10],
    "chromatic":       list(range(12)),
    "octatonic":       [0, 1, 3, 4, 6, 7, 9, 10],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "whole_tone":      [0, 2, 4, 6, 8, 10],
}

# ---------------------------------------------------------------------------
# Chord definitions — semitone intervals from root
# ---------------------------------------------------------------------------

CHORDS: dict[str, list[int]] = {
    "maj":      [0, 4, 7],
    "min":      [0, 3, 7],
    "maj7":     [0, 4, 7, 11],
    "min7":     [0, 3, 7, 10],
    "add9":     [0, 4, 7, 14],
    "sus2":     [0, 2, 7],
    "dim":      [0, 3, 6],
    "aug":      [0, 4, 8],
    "min_maj7": [0, 3, 7, 11],
    "cluster":  [0, 1, 2, 3],
    "power":    [0, 7, 12],
}

# ---------------------------------------------------------------------------
# Scale / chord generation
# ---------------------------------------------------------------------------


def scale_notes(root: int, scale_name: str, low: int, high: int) -> list[int]:
    """Return every MIDI note belonging to a scale within *[low, high]*.

    *root* is a pitch class 0-11 (0 = C).  The function iterates over all
    octaves and collects notes whose pitch class matches the scale pattern.

    >>> scale_notes(C, "major", 60, 72)
    [60, 62, 64, 65, 67, 69, 71, 72]
    """
    intervals = SCALES[scale_name]
    pitch_classes = {(root + iv) % 12 for iv in intervals}
    return [n for n in range(low, high + 1) if n % 12 in pitch_classes]


def chord_notes(root_midi: int, chord_name: str) -> list[int]:
    """Return the MIDI notes of a chord built on *root_midi*.

    >>> chord_notes(60, "maj")
    [60, 64, 67]
    """
    intervals = CHORDS[chord_name]
    return [root_midi + iv for iv in intervals]


# ---------------------------------------------------------------------------
# Voice leading
# ---------------------------------------------------------------------------


def voice_lead(
    prev_chord: list[int],
    next_pitches: list[int],
    max_leap: int = 7,
) -> list[int]:
    """Revoice *next_pitches* to minimise movement from *prev_chord*.

    For each pitch in *next_pitches* the algorithm finds the octave
    transposition closest to the corresponding voice in *prev_chord* (or the
    nearest voice when the chords have different lengths).  Movement is
    clamped to *max_leap* semitones where possible.

    Returns a new list of MIDI note numbers (same length as *next_pitches*).
    """
    if not prev_chord or not next_pitches:
        return list(next_pitches)

    result: list[int] = []
    for i, pitch in enumerate(next_pitches):
        # Pick the reference voice: corresponding index, or nearest note.
        if i < len(prev_chord):
            ref = prev_chord[i]
        else:
            ref = min(prev_chord, key=lambda p, pc=pitch % 12: abs(p - pc))

        # Find the octave placement of *pitch* closest to *ref*.
        pc = pitch % 12
        # Candidate octave base notes around ref
        base = (ref // 12) * 12
        candidates = [base + pc - 12, base + pc, base + pc + 12]
        best = min(candidates, key=lambda c: abs(c - ref))

        # Clamp leap if possible (but still keep the pitch class).
        if abs(best - ref) > max_leap:
            # Try the next-closest candidate
            candidates.sort(key=lambda c: abs(c - ref))
            for cand in candidates:
                if abs(cand - ref) <= max_leap:
                    best = cand
                    break
            # If no candidate fits within max_leap, keep the closest one.

        result.append(best)

    return result


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def random_root(
    rng: random.Random,
    options: list[int] | None = None,
) -> int:
    """Pick a random pitch class (0-11).

    If *options* is given, the choice is restricted to that list; otherwise
    all 12 pitch classes are available.

    >>> r = random.Random(0)
    >>> random_root(r, [C, E, G]) in (C, E, G)
    True
    """
    if options is None:
        options = list(range(12))
    return rng.choice(options)
