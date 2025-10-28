from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import json


@dataclass(frozen=True)
class ThresholdSpec:
    """Threshold definition for accumulate–release dynamics."""

    theta: float
    reset: float
    delta_s: float


@dataclass(frozen=True)
class DriverSpec:
    """Definition of the accumulator drive."""

    type: str
    rate: float | None = None
    leak: float | None = None
    segments: Sequence[dict] | None = None
    noise_std: float = 0.0


@dataclass(frozen=True)
class Scenario:
    """Encapsulates a complete accumulate–release configuration."""

    id: str
    label: str
    description: str
    dt: float
    duration: float
    initial_state: float
    driver: DriverSpec
    thresholds: Sequence[ThresholdSpec]

    @property
    def period_hint(self) -> float:
        """Return a rough period estimate for plotting axes."""

        total_driver = self.driver.rate or (
            self.driver.segments[-1]["rate"] if self.driver.segments else 1.0
        )
        top_threshold = max(th.theta for th in self.thresholds)
        return max((top_threshold - self.initial_state) / max(total_driver, 1e-6), 1e-6)


def _load_payload(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_scenarios(path: Path | None = None) -> List[Scenario]:
    """Load scenario definitions from disk.

    Parameters
    ----------
    path:
        Optional override for the JSON file path. When omitted the packaged
        `data/scenarios.json` file is used.
    """

    if path is None:
        path = Path(__file__).resolve().parent.parent / "data" / "scenarios.json"
    payload = _load_payload(path)
    scenarios: List[Scenario] = []
    for entry in payload.get("scenarios", []):
        driver_entry = entry["driver"]
        driver = DriverSpec(
            type=str(driver_entry["type"]),
            rate=driver_entry.get("rate"),
            leak=driver_entry.get("leak"),
            segments=tuple(driver_entry.get("segments", [])),
            noise_std=float(driver_entry.get("noise_std", 0.0)),
        )
        thresholds = tuple(
            ThresholdSpec(
                theta=float(th["theta"]),
                reset=float(th["reset"]),
                delta_s=float(th["delta_s"]),
            )
            for th in entry["thresholds"]
        )
        scenarios.append(
            Scenario(
                id=str(entry["id"]),
                label=str(entry["label"]),
                description=str(entry["description"]),
                dt=float(entry["dt"]),
                duration=float(entry["duration"]),
                initial_state=float(entry["initial_state"]),
                driver=driver,
                thresholds=thresholds,
            )
        )
    return scenarios
