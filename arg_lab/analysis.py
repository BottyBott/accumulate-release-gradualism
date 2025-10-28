from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
import pandas as pd

from .scenarios import Scenario, ThresholdSpec
from .simulate import Event


@dataclass(frozen=True)
class CycleSummary:
    """Key statistics for a single accumulate–release cycle."""

    start_time: float
    end_time: float
    duration: float
    ramp_amplitude: float
    mean_slope: float
    release_gain: float
    theta: float
    reset_level: float


def summarize_cycles(frame: pd.DataFrame, events: List[Event], initial_state: float) -> pd.DataFrame:
    """Return per-cycle statistics using the recorded release events."""

    if not events:
        return pd.DataFrame(
            columns=[
                "start_time",
                "end_time",
                "duration",
                "ramp_amplitude",
                "mean_slope",
                "release_gain",
                "theta",
                "reset_level",
            ]
        )

    summaries: List[CycleSummary] = []
    last_time = frame["time"].iloc[0]
    last_state = initial_state
    last_order = 0.0

    for event in events:
        duration = event.time - last_time
        if duration <= 0:
            duration = np.nan
        amplitude = event.state_before - last_state
        mean_slope = amplitude / duration if duration and not np.isnan(duration) else np.nan
        release_gain = event.delta_s
        summaries.append(
            CycleSummary(
                start_time=last_time,
                end_time=event.time,
                duration=duration,
                ramp_amplitude=amplitude,
                mean_slope=mean_slope,
                release_gain=release_gain,
                theta=event.theta,
                reset_level=event.reset,
            )
        )
        last_time = event.time
        last_state = event.reset
        last_order += event.delta_s

    return pd.DataFrame(summaries)


def compute_viability_margin(frame: pd.DataFrame, thresholds: Iterable[ThresholdSpec]) -> dict:
    """Compute live margin to the highest threshold at the end of the simulation."""

    top_threshold = max(th.theta for th in thresholds)
    current_state = float(frame["accumulator"].iloc[-1])
    margin = top_threshold - current_state
    relative = margin / top_threshold if top_threshold != 0 else np.nan
    return {
        "current_state": current_state,
        "top_threshold": top_threshold,
        "margin": margin,
        "relative_margin": relative,
    }
