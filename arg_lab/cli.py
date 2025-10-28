"""Command-line interface for the Accumulate–Release Gradualism lab."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate

from .analysis import compute_viability_margin, summarize_cycles
from .scenarios import Scenario, load_scenarios
from .simulate import simulate_cycle


def _scenario_index(scenarios: Iterable[Scenario]) -> Dict[str, Scenario]:
    return {scenario.id: scenario for scenario in scenarios}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run accumulate–release gradualism simulations and analytics.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="leaky_neuron",
        help="Scenario identifier to run (default: leaky_neuron).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the simulated trajectory as CSV.",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        default=None,
        help="Optional path to save a PNG plot of the trajectory.",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=3,
        help="Number of significant digits shown in console output.",
    )
    return parser


def render_plot(frame: pd.DataFrame, scenario: Scenario, output: Path | None) -> None:
    if output is None:
        return
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(frame["time"], frame["accumulator"], label="Accumulator", color="tab:blue")
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Accumulator", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    release_times = frame.loc[frame["release"] == 1, "time"].to_numpy()
    for time in release_times:
        ax1.axvline(time, color="tab:red", linestyle=":", alpha=0.4)

    ax2 = ax1.twinx()
    ax2.plot(
        frame["time"],
        frame["order_parameter"],
        label="Order parameter",
        color="tab:orange",
        linestyle="--",
    )
    ax2.set_ylabel("Order parameter", color="tab:orange")
    ax2.tick_params(axis="y", labelcolor="tab:orange")

    fig.suptitle(scenario.label)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200)
    plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    scenarios = _scenario_index(load_scenarios())

    if args.list:
        print("Available scenarios:\n")
        for scenario in scenarios.values():
            print(f"- {scenario.id}: {scenario.label}")
        return

    if args.scenario not in scenarios:
        parser.error(f"Scenario '{args.scenario}' not found. Use --list to view options.")
    scenario = scenarios[args.scenario]

    frame, events = simulate_cycle(scenario)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(args.output, index=False)

    precision = max(1, args.precision)

    cycles = summarize_cycles(frame, events, scenario.initial_state)
    if cycles.empty:
        print("No release events detected; nothing to summarise.")
    else:
        formatter = {col: precision for col in cycles.columns if cycles[col].dtype != object}
        formatted = cycles.copy()
        for column, digits in formatter.items():
            formatted[column] = formatted[column].map(lambda v: f"{v:.{digits}g}")
        print(tabulate(formatted.to_dict("records"), headers="keys", tablefmt="github"))

    margin = compute_viability_margin(frame, scenario.thresholds)
    print()
    print(
        f"End-state accumulator {margin['current_state']:.{precision}g} with margin "
        f"{margin['margin']:.{precision}g} to top threshold {margin['top_threshold']:.{precision}g}."
    )

    render_plot(frame, scenario, args.plot)


if __name__ == "__main__":
    main()
