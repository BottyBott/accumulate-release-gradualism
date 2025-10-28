from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from .scenarios import DriverSpec, Scenario, ThresholdSpec


@dataclass(frozen=True)
class Event:
    """Represents a threshold crossing and release."""

    time: float
    theta: float
    reset: float
    delta_s: float
    state_before: float
    state_after: float


def _piecewise_rate(driver: DriverSpec, time: float) -> float:
    assert driver.segments is not None
    for segment in driver.segments:
        if time <= segment["end"]:
            return float(segment["rate"])
    return float(driver.segments[-1]["rate"])


def _driver_derivative(driver: DriverSpec, time: float, state: float) -> float:
    if driver.type == "leaky":
        if driver.rate is None or driver.leak is None:
            raise ValueError("Leaky driver requires rate and leak parameters")
        return driver.rate - driver.leak * state
    if driver.type == "linear":
        if driver.rate is None:
            raise ValueError("Linear driver requires rate parameter")
        return driver.rate
    if driver.type == "piecewise":
        return _piecewise_rate(driver, time)
    raise ValueError(f"Unsupported driver type: {driver.type}")


def simulate_cycle(scenario: Scenario, seed: int | None = None) -> Tuple[pd.DataFrame, List[Event]]:
    """Simulate a single accumulate–release trajectory for the provided scenario."""

    rng = np.random.default_rng(seed)
    steps = int(np.ceil(scenario.duration / scenario.dt)) + 1
    times = np.linspace(0.0, scenario.duration, steps)
    x = np.zeros(steps)
    order = np.zeros(steps)
    releases = np.zeros(steps, dtype=int)
    driver_values = np.zeros(steps)
    x[0] = scenario.initial_state
    order[0] = 0.0
    events: List[Event] = []
    thresholds = sorted(scenario.thresholds, key=lambda th: th.theta)

    for idx in range(1, steps):
        t_prev = times[idx - 1]
        state = x[idx - 1]
        derivative = _driver_derivative(scenario.driver, t_prev, state)
        if scenario.driver.noise_std > 0.0:
            derivative += rng.normal(scale=scenario.driver.noise_std)
        driver_values[idx - 1] = derivative
        state_next = state + derivative * scenario.dt

        crossed: List[ThresholdSpec] = []
        for threshold in thresholds:
            if state_next >= threshold.theta:
                crossed.append(threshold)

        if crossed:
            # apply the highest threshold reached first
            selected = crossed[-1]
            event = Event(
                time=times[idx],
                theta=selected.theta,
                reset=selected.reset,
                delta_s=selected.delta_s,
                state_before=state_next,
                state_after=selected.reset,
            )
            events.append(event)
            state_next = selected.reset
            order[idx] = order[idx - 1] + selected.delta_s
            releases[idx] = 1
        else:
            order[idx] = order[idx - 1]

        x[idx] = max(state_next, 0.0)

    driver_values[-1] = driver_values[-2] if steps > 1 else 0.0

    frame = pd.DataFrame(
        {
            "time": times,
            "accumulator": x,
            "order_parameter": order,
            "driver": driver_values,
            "release": releases,
        }
    )
    return frame, events


def simulate_ensemble(
    scenario: Scenario,
    size: int,
    jitter: Dict[str, float] | None = None,
    seed: int | None = None,
) -> List[pd.DataFrame]:
    """Simulate an ensemble of trajectories with optional parameter jitter."""

    rng = np.random.default_rng(seed)
    results: List[pd.DataFrame] = []
    jitter = jitter or {}
    for index in range(size):
        # shallow copy scenario parameters with perturbations on rate/leak/reset
        rate_scale = 1.0 + rng.normal(scale=jitter.get("rate", 0.0))
        leak_scale = 1.0 + rng.normal(scale=jitter.get("leak", 0.0))
        thresholds: List[ThresholdSpec] = []
        for th in scenario.thresholds:
            theta = th.theta * (1.0 + rng.normal(scale=jitter.get("theta", 0.0)))
            reset = th.reset * (1.0 + rng.normal(scale=jitter.get("reset", 0.0)))
            delta_s = th.delta_s
            thresholds.append(ThresholdSpec(theta=theta, reset=reset, delta_s=delta_s))
        driver = scenario.driver
        driver_copy = DriverSpec(
            type=driver.type,
            rate=(driver.rate * rate_scale) if driver.rate is not None else None,
            leak=(driver.leak * leak_scale) if driver.leak is not None else None,
            segments=driver.segments,
            noise_std=driver.noise_std,
        )
        perturbed = Scenario(
            id=f"{scenario.id}_member{index}",
            label=scenario.label,
            description=scenario.description,
            dt=scenario.dt,
            duration=scenario.duration,
            initial_state=scenario.initial_state,
            driver=driver_copy,
            thresholds=tuple(thresholds),
        )
        frame, _ = simulate_cycle(perturbed, seed=rng.integers(0, 2**32 - 1))
        frame["member"] = index
        results.append(frame)
    return results
