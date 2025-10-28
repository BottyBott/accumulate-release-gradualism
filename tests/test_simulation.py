import math

from arg_lab.analysis import summarize_cycles
from arg_lab.scenarios import load_scenarios
from arg_lab.simulate import simulate_cycle


def _get_scenario(scenario_id: str):
    scenarios = {scenario.id: scenario for scenario in load_scenarios()}
    return scenarios[scenario_id]


def test_leaky_neuron_period_matches_analytic():
    scenario = _get_scenario("leaky_neuron")
    frame, events = simulate_cycle(scenario)
    cycles = summarize_cycles(frame, events, scenario.initial_state)
    assert not cycles.empty
    measured_period = cycles["duration"].iloc[0]
    a = scenario.driver.rate
    b = scenario.driver.leak
    assert a is not None and b is not None
    expected = (1 / b) * math.log((a / b - scenario.thresholds[0].reset) / (a / b - scenario.thresholds[0].theta))
    assert math.isclose(measured_period, expected, rel_tol=0.02, abs_tol=0.01)


def test_queue_release_emits_multiple_events():
    scenario = _get_scenario("queue_release")
    frame, events = simulate_cycle(scenario, seed=42)
    assert len(events) >= 2
    cycles = summarize_cycles(frame, events, scenario.initial_state)
    assert len(cycles) == len(events)
    assert (cycles["ramp_amplitude"] > 0).all()
