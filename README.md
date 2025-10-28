# Accumulate–Release Gradualism Lab

This repository packages the accumulate–release gradualism (ARG) discipline into a runnable, inspectable project. ARG systems store energy, mass, charge, or backlog until a viability threshold is reached, then release part of that state and reset. Examples include neurons, hydraulic buffers, order queues, and avalanche electronics. The code here models those dynamics, extracts cycle statistics, and visualises how whole-of-system behaviour emerges from simple ramp-and-release rules.

## What the project does
- **Simulates canonical ARG systems.** Three ready-to-run scenarios cover a leaky integrate–and–fire oscillator, a staircase ladder with multiple release levels, and a capacity-limited queue with stochastic inflow.
- **Tracks constraint ledgers.** Time-series outputs include the live accumulator, event markers, and an order parameter counting released quanta.
- **Summarises cycles.** The analytics module reports period, amplitude, mean slope, release gain, and reset levels so you can see whether the ensemble remains viable.
- **Quantifies slack.** Margin calculations show how far the final state sits from the active threshold, supplying an immediate health indicator.

## Repository layout
- `arg_lab/` – Python package with scenario loading, simulation, analysis, and CLI glue.
- `data/scenarios.json` – Fully specified scenario catalogue (no placeholders).
- `tests/` – Unit tests that verify time-step integration and cycle-statistic logic.
- `requirements.txt` – Minimal dependency set (`numpy`, `pandas`, `matplotlib`, `tabulate`).
- `build/` – Default output folder (ignored by git) for generated CSV or PNG files.

## Getting started
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m arg_lab.cli --list
python -m arg_lab.cli --scenario leaky_neuron --output build/leaky.csv --plot build/leaky.png
```

The last command simulates two seconds of leaky integrate–and–fire behaviour, writes the trajectory to CSV, prints per-cycle metrics, and stores a plot with accumulator traces and release markers.

## Scenario catalogue
| ID | Description | Key parameters |
|----|-------------|----------------|
| `leaky_neuron` | Constant drive with linear leakage and a single threshold, representing textbook saw-tooth activity. | Drive rate 1.35, leak 1.0, threshold 1.0, reset 0.25. |
| `staircase_ladder` | Linear ramp climbing three thresholds that trigger partial releases before the full reset. | Rates 0.55, thresholds [1.2, 1.9, 2.4], resets [0.8, 0.9, 0.3]. |
| `queue_release` | Buffer with piecewise inflow and noise; a relief valve fires near capacity leaving a controlled residue. | Segment rates (0.35, 0.5, 0.25), threshold 4.5, reset 0.9, noise σ=0.03. |

Scenario definitions live inside `data/scenarios.json`, so runs are reproducible without extra configuration.

## Output interpretation
The CLI prints a cycle summary table with the following columns:
- `start_time` / `end_time` – Ramp boundaries.
- `duration` – Time spent accumulating before the release.
- `ramp_amplitude` – Change in the accumulator across the cycle.
- `mean_slope` – Average accumulation rate (amplitude ÷ duration).
- `release_gain` – Order-parameter increment applied during the release.
- `theta` / `reset_level` – Threshold hit and post-release state.

It also reports the live margin between the last accumulator value and the highest threshold. Positive margin confirms viable headroom; shrinking margin warns that the system is drifting toward instability.

## Visualisation
When `--plot` is provided the tool produces a dual-axis figure: the blue line shows the accumulator, orange dashed line shows the order parameter, and red vertical markers highlight release events. This makes it easy to verify whether thresholds are firing as intended and whether releases stay desynchronised.

## Testing
```bash
pytest
```

Tests validate the leaky integrate–and–fire solution against the analytic period, ensure the simulator handles staircases correctly, and confirm that cycle summaries match event logs.


