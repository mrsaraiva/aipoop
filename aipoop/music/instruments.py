"""Synthesizer voices for procedural music composition.

Pure numpy implementations — zero external audio dependencies.
All functions accept and return np.float32 arrays.
"""

from __future__ import annotations

import numpy as np

from ..constants import SAMPLE_RATE


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------

def adsr_envelope(
    n_samples: int,
    attack: float = 0.01,
    decay: float = 0.1,
    sustain_level: float = 0.7,
    release: float = 0.1,
) -> np.ndarray:
    """Generate a standard ADSR envelope.

    Parameters
    ----------
    n_samples : int
        Total length of the envelope in samples.
    attack : float
        Attack time in seconds.
    decay : float
        Decay time in seconds.
    sustain_level : float
        Sustain amplitude (0–1).
    release : float
        Release time in seconds.

    Returns
    -------
    np.ndarray
        Float32 array of shape ``(n_samples,)`` with values in [0, 1].
    """
    if n_samples <= 0:
        return np.array([], dtype=np.float32)

    a_samples = int(attack * SAMPLE_RATE)
    d_samples = int(decay * SAMPLE_RATE)
    r_samples = int(release * SAMPLE_RATE)

    # Clamp so we never exceed n_samples
    total_adr = a_samples + d_samples + r_samples
    if total_adr > n_samples:
        scale = n_samples / total_adr
        a_samples = int(a_samples * scale)
        d_samples = int(d_samples * scale)
        r_samples = n_samples - a_samples - d_samples

    s_samples = max(0, n_samples - a_samples - d_samples - r_samples)

    parts: list[np.ndarray] = []

    # Attack: 0 → 1
    if a_samples > 0:
        parts.append(np.linspace(0.0, 1.0, a_samples, endpoint=False, dtype=np.float32))

    # Decay: 1 → sustain_level
    if d_samples > 0:
        parts.append(np.linspace(1.0, sustain_level, d_samples, endpoint=False, dtype=np.float32))

    # Sustain
    if s_samples > 0:
        parts.append(np.full(s_samples, sustain_level, dtype=np.float32))

    # Release: sustain_level → 0
    if r_samples > 0:
        parts.append(np.linspace(sustain_level, 0.0, r_samples, dtype=np.float32))

    env = np.concatenate(parts) if parts else np.array([], dtype=np.float32)

    # Ensure exact length (rounding can shift by ±1)
    if len(env) < n_samples:
        env = np.pad(env, (0, n_samples - len(env)), constant_values=0.0).astype(np.float32)
    elif len(env) > n_samples:
        env = env[:n_samples]

    return env


# ---------------------------------------------------------------------------
# Karplus–Strong plucked string
# ---------------------------------------------------------------------------

def karplus_strong(
    freq: float,
    duration: float,
    sr: int = SAMPLE_RATE,
    brightness: float = 0.5,
    detune: float = 0.0,
) -> np.ndarray:
    """Plucked string / piano-like synthesis via Karplus–Strong algorithm.

    Parameters
    ----------
    freq : float
        Fundamental frequency in Hz.
    duration : float
        Duration in seconds.
    sr : int
        Sample rate.
    brightness : float
        0–1.  Higher values keep more high-frequency content.
    detune : float
        If non-zero, a second string is layered at ``freq * (1 + detune)``.

    Returns
    -------
    np.ndarray
        Float32 array normalised to [-1, 1].
    """
    n_samples = int(duration * sr)
    if n_samples <= 0 or freq <= 0:
        return np.zeros(max(n_samples, 0), dtype=np.float32)

    def _single_string(f: float) -> np.ndarray:
        N = max(1, round(sr / f))
        buf = np.random.uniform(-1.0, 1.0, N).astype(np.float64)
        out = np.empty(n_samples, dtype=np.float64)
        out[:N] = buf

        for i in range(N, n_samples):
            prev = out[i - N]
            prev1 = out[i - N - 1] if (i - N - 1) >= 0 else out[i - N]
            avg = (prev + prev1) / 2.0
            out[i] = brightness * avg + (1.0 - brightness) * prev

        return out

    signal = _single_string(freq)

    if detune != 0.0:
        signal2 = _single_string(freq * (1.0 + detune))
        signal = (signal + signal2) * 0.5

    # Apply gentle ADSR
    env = adsr_envelope(n_samples, attack=0.005, decay=0.05, sustain_level=0.8, release=0.15)
    signal *= env.astype(np.float64)

    # Normalise
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak

    return signal.astype(np.float32)


# ---------------------------------------------------------------------------
# Additive pad
# ---------------------------------------------------------------------------

def pad_voice(
    freq: float,
    duration: float,
    sr: int = SAMPLE_RATE,
    n_harmonics: int = 8,
    warmth: float = 0.5,
) -> np.ndarray:
    """Additive synthesis pad with slow attack and per-harmonic micro-detune.

    Parameters
    ----------
    freq : float
        Fundamental frequency in Hz.
    duration : float
        Duration in seconds.
    sr : int
        Sample rate.
    n_harmonics : int
        Number of harmonics to sum.
    warmth : float
        Controls harmonic amplitude rolloff — higher = darker.

    Returns
    -------
    np.ndarray
        Float32 array normalised to [-1, 1].
    """
    n_samples = int(duration * sr)
    if n_samples <= 0 or freq <= 0:
        return np.zeros(max(n_samples, 0), dtype=np.float32)

    t = np.linspace(0, duration, n_samples, endpoint=False, dtype=np.float64)
    signal = np.zeros(n_samples, dtype=np.float64)

    rng = np.random.default_rng()

    for k in range(1, n_harmonics + 1):
        amp = 1.0 / (k ** (1.0 + warmth))
        # ±2 cents random detune:  2 cents = 2^(2/1200) - 1 ≈ 0.001155
        cents = rng.uniform(-2.0, 2.0)
        detune_factor = 2.0 ** (cents / 1200.0)
        harmonic_freq = freq * k * detune_factor
        signal += amp * np.sin(2.0 * np.pi * harmonic_freq * t)

    # Slow ADSR
    env = adsr_envelope(n_samples, attack=0.3, decay=0.2, sustain_level=0.6, release=0.3)
    signal *= env.astype(np.float64)

    # Normalise
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak

    return signal.astype(np.float32)


# ---------------------------------------------------------------------------
# FM bell
# ---------------------------------------------------------------------------

def fm_bell(
    freq: float,
    duration: float,
    sr: int = SAMPLE_RATE,
    mod_ratio: float = 3.0,
    mod_index: float = 5.0,
) -> np.ndarray:
    """FM synthesis bell tone.

    Parameters
    ----------
    freq : float
        Carrier frequency in Hz.
    duration : float
        Duration in seconds.
    sr : int
        Sample rate.
    mod_ratio : float
        Modulator-to-carrier frequency ratio.
    mod_index : float
        Modulation depth.

    Returns
    -------
    np.ndarray
        Float32 array normalised to [-1, 1].
    """
    n_samples = int(duration * sr)
    if n_samples <= 0 or freq <= 0:
        return np.zeros(max(n_samples, 0), dtype=np.float32)

    t = np.linspace(0, duration, n_samples, endpoint=False, dtype=np.float64)
    carrier = freq
    modulator = freq * mod_ratio

    signal = np.sin(
        2.0 * np.pi * carrier * t
        + mod_index * np.sin(2.0 * np.pi * modulator * t)
    )

    # Exponential decay envelope
    env = np.exp(-t * 4.0 / duration)
    signal *= env

    # Normalise
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak

    return signal.astype(np.float32)


# ---------------------------------------------------------------------------
# Sub bass
# ---------------------------------------------------------------------------

def sub_bass(
    freq: float,
    duration: float,
    sr: int = SAMPLE_RATE,
    drive: float = 0.0,
) -> np.ndarray:
    """Sine-based sub bass with optional saturation.

    Parameters
    ----------
    freq : float
        Frequency in Hz.
    duration : float
        Duration in seconds.
    sr : int
        Sample rate.
    drive : float
        Saturation amount (0 = clean, higher = dirtier).

    Returns
    -------
    np.ndarray
        Float32 array normalised to [-1, 1].
    """
    n_samples = int(duration * sr)
    if n_samples <= 0 or freq <= 0:
        return np.zeros(max(n_samples, 0), dtype=np.float32)

    t = np.linspace(0, duration, n_samples, endpoint=False, dtype=np.float64)
    signal = np.sin(2.0 * np.pi * freq * t)

    # Saturation
    if drive > 0:
        signal = np.tanh(signal * (1.0 + drive * 3.0))

    # ADSR
    env = adsr_envelope(n_samples, attack=0.02, decay=0.1, sustain_level=0.8, release=0.05)
    signal *= env.astype(np.float64)

    # Normalise
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak

    return signal.astype(np.float32)


# ---------------------------------------------------------------------------
# Noise percussion hit
# ---------------------------------------------------------------------------

def noise_hit(
    duration: float,
    sr: int = SAMPLE_RATE,
    color: str = "white",
    cutoff: float = 2000.0,
) -> np.ndarray:
    """Noise percussion burst with optional lowpass filtering.

    Parameters
    ----------
    duration : float
        Duration in seconds.
    sr : int
        Sample rate.
    color : str
        ``"white"`` for unfiltered noise, anything else applies a lowpass at
        *cutoff* Hz.
    cutoff : float
        Lowpass cutoff frequency (only used when ``color != "white"``).

    Returns
    -------
    np.ndarray
        Float32 array normalised to [-1, 1].
    """
    n_samples = int(duration * sr)
    if n_samples <= 0:
        return np.zeros(max(n_samples, 0), dtype=np.float32)

    signal = np.random.uniform(-1.0, 1.0, n_samples).astype(np.float64)

    if color != "white":
        signal = lowpass(signal.astype(np.float32), cutoff, sr).astype(np.float64)

    # Fast exponential decay
    t = np.linspace(0, duration, n_samples, endpoint=False, dtype=np.float64)
    env = np.exp(-t * 10.0 / duration)
    signal *= env

    # Normalise
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak

    return signal.astype(np.float32)


# ---------------------------------------------------------------------------
# Band-limited sawtooth
# ---------------------------------------------------------------------------

def sawtooth_voice(
    freq: float,
    duration: float,
    sr: int = SAMPLE_RATE,
    n_harmonics: int = 16,
) -> np.ndarray:
    """Band-limited sawtooth wave via additive synthesis.

    Parameters
    ----------
    freq : float
        Fundamental frequency in Hz.
    duration : float
        Duration in seconds.
    sr : int
        Sample rate.
    n_harmonics : int
        Number of harmonics (controls bandwidth vs aliasing).

    Returns
    -------
    np.ndarray
        Float32 array normalised to [-1, 1].
    """
    n_samples = int(duration * sr)
    if n_samples <= 0 or freq <= 0:
        return np.zeros(max(n_samples, 0), dtype=np.float32)

    t = np.linspace(0, duration, n_samples, endpoint=False, dtype=np.float64)
    signal = np.zeros(n_samples, dtype=np.float64)

    for k in range(1, n_harmonics + 1):
        # Skip harmonics above Nyquist
        if k * freq > sr / 2:
            break
        sign = (-1.0) ** (k + 1)
        signal += sign * np.sin(2.0 * np.pi * k * freq * t) / k

    # ADSR
    env = adsr_envelope(n_samples, attack=0.01, decay=0.1, sustain_level=0.7, release=0.1)
    signal *= env.astype(np.float64)

    # Normalise
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal /= peak

    return signal.astype(np.float32)


# ---------------------------------------------------------------------------
# Filters & effects
# ---------------------------------------------------------------------------

def lowpass(signal: np.ndarray, cutoff: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """One-pole IIR lowpass filter.

    Parameters
    ----------
    signal : np.ndarray
        Input signal.
    cutoff : float
        Cutoff frequency in Hz.
    sr : int
        Sample rate.

    Returns
    -------
    np.ndarray
        Filtered float32 signal of the same length.
    """
    if len(signal) == 0:
        return np.array([], dtype=np.float32)

    rc = 2.0 * np.pi * cutoff / sr
    alpha = rc / (rc + 1.0)

    out = np.empty(len(signal), dtype=np.float64)
    out[0] = alpha * signal[0]
    for i in range(1, len(signal)):
        out[i] = alpha * signal[i] + (1.0 - alpha) * out[i - 1]

    return out.astype(np.float32)


def simple_reverb(
    signal: np.ndarray,
    sr: int = SAMPLE_RATE,
    decay: float = 0.3,
    wet: float = 0.2,
) -> np.ndarray:
    """Simple Schroeder reverb (4 parallel comb filters + 2 series allpass).

    Parameters
    ----------
    signal : np.ndarray
        Input signal.
    sr : int
        Sample rate.
    decay : float
        Feedback gain for comb filters (0–1).
    wet : float
        Wet/dry mix ratio (0 = fully dry, 1 = fully wet).

    Returns
    -------
    np.ndarray
        Float32 signal with reverb applied.
    """
    if len(signal) == 0:
        return np.array([], dtype=np.float32)

    sig = signal.astype(np.float64)
    n = len(sig)

    # --- Comb filters (parallel) ---
    comb_delays = [1557, 1617, 1491, 1422]
    comb_sum = np.zeros(n, dtype=np.float64)

    for delay in comb_delays:
        buf = np.zeros(n, dtype=np.float64)
        for i in range(n):
            buf[i] = sig[i]
            if i >= delay:
                buf[i] += decay * buf[i - delay]
        comb_sum += buf

    comb_sum /= len(comb_delays)

    # --- Allpass filters (series) ---
    allpass_delays = [225, 556]
    allpass_gain = 0.5

    out = comb_sum
    for delay in allpass_delays:
        buf = np.zeros(n, dtype=np.float64)
        for i in range(n):
            delayed = buf[i - delay] if i >= delay else 0.0
            buf[i] = -allpass_gain * out[i] + delayed + allpass_gain * (out[i] + allpass_gain * delayed)
            # Simplified allpass: y[n] = -g*x[n] + x[n-D] + g*y[n-D]
        # Re-derive with standard allpass form
        buf2 = np.zeros(n, dtype=np.float64)
        for i in range(n):
            x_delayed = out[i - delay] if i >= delay else 0.0
            y_delayed = buf2[i - delay] if i >= delay else 0.0
            buf2[i] = -allpass_gain * out[i] + x_delayed + allpass_gain * y_delayed
        out = buf2

    # Mix wet/dry
    result = (1.0 - wet) * sig + wet * out

    # Normalise if clipping
    peak = np.max(np.abs(result))
    if peak > 1.0:
        result /= peak

    return result.astype(np.float32)


def bitcrush(signal: np.ndarray, bits: int = 4) -> np.ndarray:
    """Quantize signal to the given bit depth.

    Parameters
    ----------
    signal : np.ndarray
        Input signal (expected range [-1, 1]).
    bits : int
        Target bit depth.

    Returns
    -------
    np.ndarray
        Quantized float32 signal.
    """
    if len(signal) == 0:
        return np.array([], dtype=np.float32)

    levels = 2 ** bits
    return (np.round(signal * levels) / levels).astype(np.float32)
