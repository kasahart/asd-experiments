"""Synthetic two-microphone input for waveform unit tests."""

import numpy as np

SYNTHETIC_PARAMETERS = {
    "sample_rate": 16000,
    "duration": 1.0,
    "noise": {
        "frequency": 1000,
        "amplitude": 0.6,
        "near_gain": 0.25,
        "near_delay_ms": 0.8,
        "far_gain": 0.75,
        "far_delay_ms": 0.0,
    },
    "machine": {
        "frequency": 1900,
        "amplitude": 0.6,
        "near_gain": 1.0,
        "near_delay_ms": 0.0,
        "far_gain": 0.3,
        "far_delay_ms": 0.8,
    },
}


def synthetic_components():
    """Two sources enter both microphones with distinct fixed gains and relative delays."""
    p = SYNTHETIC_PARAMETERS
    t = (
        np.arange(int(p["sample_rate"] * p["duration"]), dtype=np.float64)
        / p["sample_rate"]
    )
    parts = {}
    for role in ("noise", "machine"):
        source = p[role]
        angle = 2 * np.pi * source["frequency"] * t
        for microphone in ("near", "far"):
            parts[microphone + "_" + role] = (
                source["amplitude"]
                * source[microphone + "_gain"]
                * np.sin(
                    angle
                    - 2
                    * np.pi
                    * source["frequency"]
                    * source[microphone + "_delay_ms"]
                    / 1000
                )
            )
    return parts


def synthetic():
    parts = synthetic_components()
    return np.stack(
        [
            parts["near_machine"] + parts["near_noise"],
            parts["far_machine"] + parts["far_noise"],
        ]
    ).astype(np.float32)
