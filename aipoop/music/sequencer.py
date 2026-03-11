"""Event-based sequencer and PCM renderer for procedural music."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..constants import SAMPLE_RATE
from .theory import note_freq
from . import instruments


@dataclass
class NoteEvent:
    start: float       # in beats
    duration: float    # in beats
    pitch: int         # MIDI note number
    velocity: float    # 0.0-1.0
    instrument: str    # "piano", "pad", "bass", "bell", "noise", "saw"
    cents: float = 0.0 # microtonal offset


@dataclass
class TempoMap:
    base_bpm: float = 120.0
    curve: list[tuple[float, float]] = field(default_factory=list)
    # curve is (beat, bpm) keyframes for tempo changes


def beats_to_seconds(beat: float, tempo_map: TempoMap) -> float:
    """Convert a beat position to seconds using the tempo map.

    If the curve is empty, uses base_bpm uniformly.
    If keyframes exist, integrates piecewise-linear tempo.
    """
    if not tempo_map.curve:
        return beat * 60.0 / tempo_map.base_bpm

    # Sort keyframes by beat
    kf = sorted(tempo_map.curve, key=lambda k: k[0])

    # Prepend beat-0 if missing (use first keyframe's bpm)
    if kf[0][0] > 0:
        kf = [(0.0, kf[0][1])] + kf

    seconds = 0.0
    prev_beat, prev_bpm = kf[0]

    for kb, kbpm in kf[1:]:
        if beat <= prev_beat:
            break
        seg_end = min(beat, kb)
        seg_len = seg_end - prev_beat
        if seg_len <= 0:
            prev_beat, prev_bpm = kb, kbpm
            continue
        # Linearly interpolate BPM over this segment; integrate dt = db / bpm * 60
        # If BPMs are nearly equal, treat as constant for numerical stability
        if abs(kbpm - prev_bpm) < 0.01:
            seconds += seg_len * 60.0 / prev_bpm
        else:
            # Integral of 60/bpm(b) db where bpm(b) = prev_bpm + (kbpm-prev_bpm)*(b-prev_beat)/(kb-prev_beat)
            ratio = (seg_end - prev_beat) / (kb - prev_beat)
            bpm_at_end = prev_bpm + (kbpm - prev_bpm) * ratio
            # integral of 60/(a + m*x) dx = 60/m * ln((a + m*x)) evaluated
            m = (kbpm - prev_bpm) / (kb - prev_beat)
            seconds += 60.0 / m * np.log(bpm_at_end / prev_bpm)
        if beat <= kb:
            break
        prev_beat, prev_bpm = kb, kbpm
    else:
        # beat is beyond last keyframe — use last bpm as constant
        if beat > prev_beat:
            seconds += (beat - prev_beat) * 60.0 / prev_bpm

    return float(seconds)


# Instrument dispatch table
_INSTRUMENT_MAP = {
    "piano": lambda freq, dur, sr: instruments.karplus_strong(freq, dur, sr),
    "pad": lambda freq, dur, sr: instruments.pad_voice(freq, dur, sr),
    "bass": lambda freq, dur, sr: instruments.sub_bass(freq, dur, sr),
    "bell": lambda freq, dur, sr: instruments.fm_bell(freq, dur, sr),
    "noise": lambda freq, dur, sr: instruments.noise_hit(dur, sr),
    "saw": lambda freq, dur, sr: instruments.sawtooth_voice(freq, dur, sr),
}


def render_events(
    events: list[NoteEvent],
    tempo_map: TempoMap,
    duration_seconds: float,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    """Render note events to a float32 PCM buffer."""
    n_samples = int(duration_seconds * sr)
    output = np.zeros(n_samples, dtype=np.float64)

    for ev in events:
        start_sec = beats_to_seconds(ev.start, tempo_map)
        dur_sec = beats_to_seconds(ev.start + ev.duration, tempo_map) - start_sec
        if dur_sec <= 0.01:
            dur_sec = 0.01

        freq = note_freq(ev.pitch, ev.cents)

        synth = _INSTRUMENT_MAP.get(ev.instrument)
        if synth is None:
            continue

        samples = synth(freq, dur_sec, sr)
        if len(samples) == 0:
            continue

        samples = samples.astype(np.float64) * ev.velocity

        offset = int(start_sec * sr)
        if offset < 0:
            offset = 0
        end = offset + len(samples)
        if offset >= n_samples:
            continue
        if end > n_samples:
            samples = samples[: n_samples - offset]
            end = n_samples

        output[offset:end] += samples

    # Apply light reverb
    output_f32 = output.astype(np.float32)
    output_f32 = instruments.simple_reverb(output_f32, sr=sr, wet=0.15)

    # Normalize
    peak = np.max(np.abs(output_f32))
    if peak > 1.0:
        output_f32 *= 0.95 / peak

    return output_f32
