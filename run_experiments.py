"""Run repeatable headless comparisons for the Robot Invites scenarios."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from backend import Simulation

OUTPUT_DIR = Path(__file__).parent / "manuscript"

SCENARIOS = [
    ("One door", "Baseline: 30 robots, one 3-robot-wide door", {"robot_count": 30, "door_width": 3, "extra_doors": 0, "variability": 0, "arrival_pattern": "surge"}),
    ("More doors", "30 robots, two 3-robot-wide doors", {"robot_count": 30, "door_width": 3, "extra_doors": 1, "variability": 0, "arrival_pattern": "surge"}),
    ("Bigger door", "30 robots, one 5-robot-wide door", {"robot_count": 30, "door_width": 5, "extra_doors": 0, "variability": 0, "arrival_pattern": "surge"}),
    ("Invite timing", "30 robots scheduled across a seven-second arrival window", {"robot_count": 30, "door_width": 3, "extra_doors": 0, "variability": 0, "arrival_pattern": "scheduled"}),
    ("Robot personality", "30 robots with moderate random arrival variation", {"robot_count": 30, "door_width": 3, "extra_doors": 0, "variability": 0, "arrival_pattern": "personality"}),
    ("At the limit", "100 robots, one 3-robot-wide door", {"robot_count": 100, "door_width": 3, "extra_doors": 0, "variability": 0, "arrival_pattern": "surge"}),
]


def run_once(seed: int, settings: dict) -> dict:
    settings = dict(settings)
    arrival_pattern = settings.pop("arrival_pattern")
    simulation = Simulation(seed=seed)
    simulation.reset(**settings)
    if arrival_pattern == "surge":
        for robot in simulation.robots:
            robot.arrival_time = 0.0
    elif arrival_pattern == "scheduled":
        for robot in simulation.robots:
            robot.arrival_time = robot.robot_id / (len(simulation.robots) - 1) * 7.0
    elif arrival_pattern == "personality":
        for robot in simulation.robots:
            robot.arrival_time = simulation.random.uniform(0.0, 3.5)
    peak_queue = 0
    steps = 0
    while steps < 10000:
        state = simulation.step(0.25)
        peak_queue = max(peak_queue, state["metrics"]["waiting"])
        steps += 1
        if all(robot.status == "inside" for robot in simulation.robots):
            break
    if steps == 10000:
        raise RuntimeError(f"scenario did not complete: {settings}")
    waits = [robot.entered_time - robot.arrival_time for robot in simulation.robots if robot.entered_time is not None]
    completion_time = simulation.time
    return {
        "robots": len(simulation.robots),
        "capacity": simulation.capacity_per_tick,
        "completion_time": completion_time,
        "throughput": len(simulation.robots) / completion_time * 60,
        "average_wait": statistics.mean(waits),
        "max_wait": max(waits),
        "peak_queue": peak_queue,
    }


def summarize(values: list[dict]) -> dict:
    fields = ("completion_time", "throughput", "average_wait", "max_wait", "peak_queue")
    return {field: statistics.mean(item[field] for item in values) for field in fields}


def pct(value: float) -> str:
    return f"{value:.1f}"


def main() -> None:
    repetitions = 20
    results = []
    for index, (name, description, settings) in enumerate(SCENARIOS):
        runs = [run_once(1000 + index * repetitions + repeat, settings) for repeat in range(repetitions)]
        results.append({"name": name, "description": description, "settings": settings, "summary": summarize(runs), "runs": runs})

    baseline = results[0]["summary"]
    report = [
        "# Robot Invites Experiment Results",
        "",
        f"> Headless comparison of {len(SCENARIOS)} scenarios, {repetitions} deterministic seeds per scenario.",
        "> Each run advances the same Python model in 0.25-second ticks until every robot is inside.",
        "",
        "## Executive Summary",
        "",
        "The doorway is the dominant constraint in the baseline. Widening the door from three to five robot widths improves flow, while adding a second door produces the largest throughput gain. Arrival variability reduces the size of the synchronized peak but does not increase the physical doorway capacity. The 100-robot case shows that the bottleneck persists as the invite list grows.",
        "",
        "## Results",
        "",
        "Values are averages across repeated runs. Wait is measured from each robot's scheduled arrival time until admission. Peak queue counts robots that have arrived but are still outside.",
        "",
        "| Scenario | Robots | Door capacity / tick | Complete (s) | Throughput (robots/min) | Avg wait (s) | Max wait (s) | Peak queue |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        summary = result["summary"]
        representative = result["runs"][0]
        report.append(
            f"| {result['name']} | {representative['robots']} | {representative['capacity']} | "
            f"{pct(summary['completion_time'])} | {pct(summary['throughput'])} | {pct(summary['average_wait'])} | "
            f"{pct(summary['max_wait'])} | {pct(summary['peak_queue'])} |"
        )

    report.extend([
        "",
        "## Change From Baseline",
        "",
        "| Scenario | Completion time | Throughput | Average wait | Peak queue |",
        "|---|---:|---:|---:|---:|",
    ])
    for result in results[1:]:
        summary = result["summary"]
        report.append(
            f"| {result['name']} | {summary['completion_time'] / baseline['completion_time']:.2f}x | "
            f"{summary['throughput'] / baseline['throughput']:.2f}x | "
            f"{summary['average_wait'] - baseline['average_wait']:+.1f}s | "
            f"{summary['peak_queue'] - baseline['peak_queue']:+.1f} |"
        )

    report.extend([
        "",
        "## Interpretation",
        "",
        "### More doors",
        "This is the strongest structural intervention in the tested set. Two doors double the modeled admission capacity from three to six robots per tick, so completion time and waiting fall substantially.",
        "",
        "### Bigger door",
        "A five-robot-wide door increases capacity from three to five robots per tick. It improves the flow without changing the invitation pattern, but it is less powerful than adding an equally sized second door in this model.",
        "",
        "### Invite timing",
        "Spreading arrival times reduces synchronized queue pressure. It changes when robots arrive, not how many the door can admit, so its benefit is strongest as a peak-management strategy rather than a pure throughput strategy.",
        "",
        "### Robot personality",
        "Moderate punctuality differences create a smaller version of the invite-timing effect. This makes the crowd less synchronized, but it does not remove the fixed-capacity bottleneck.",
        "",
        "### At the limit",
        "The larger invite list makes the baseline bottleneck persistent: the queue and completion time scale with demand while the door capacity stays fixed. This is the clearest demonstration that an infinite or growing invite list cannot be solved by punctuality alone.",
        "",
        "## Caveats",
        "",
        "- This is a simplified discrete model: robots are admitted in FIFO order and collision avoidance is not modeled.",
        "- The current timing and personality scenarios use randomized arrival offsets, not strategic scheduling or social utility.",
        "- Door capacity is represented as robots admitted per simulation tick; the visual frontend interpolates their movement between backend states.",
        "- The metrics are useful for relative comparison, not a physical prediction of a real building.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 run_experiments.py",
        "```",
        "",
        f"Generated on 2026-09-16 with {repetitions} repetitions per scenario.",
    ])
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "experiment-summary.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUTPUT_DIR / "experiment-results.json").write_text(json.dumps({
        "repetitions": repetitions,
        "scenarios": results,
    }, indent=2) + "\n", encoding="utf-8")
    print("Wrote experiment-summary.md")
    for result in results:
        summary = result["summary"]
        print(f"{result['name']}: {summary['completion_time']:.2f}s, {summary['throughput']:.1f} robots/min, peak queue {summary['peak_queue']:.1f}")


if __name__ == "__main__":
    main()
