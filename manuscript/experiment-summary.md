# Robot Invites Experiment Results

> Headless comparison of 6 scenarios, 20 deterministic seeds per scenario.
> Each run advances the same Python model in 0.25-second ticks until every robot is inside.

## Executive Summary

The doorway is the dominant constraint in the baseline. Widening the door from three to five robot widths improves flow, while adding a second door produces the largest throughput gain. Arrival variability reduces the size of the synchronized peak but does not increase the physical doorway capacity. The 100-robot case shows that the bottleneck persists as the invite list grows.

## Results

Values are averages across repeated runs. Wait is measured from each robot's scheduled arrival time until admission. Peak queue counts robots that have arrived but are still outside.

| Scenario | Robots | Door capacity / tick | Complete (s) | Throughput (robots/min) | Avg wait (s) | Max wait (s) | Peak queue |
|---|---:|---:|---:|---:|---:|---:|---:|
| One door | 30 | 3 | 2.5 | 720.0 | 1.4 | 2.5 | 27.0 |
| More doors | 30 | 6 | 1.2 | 1440.0 | 0.8 | 1.2 | 24.0 |
| Bigger door | 30 | 5 | 1.5 | 1200.0 | 0.9 | 1.5 | 25.0 |
| Invite timing | 30 | 3 | 7.0 | 257.1 | 0.1 | 0.2 | 0.0 |
| Robot personality | 30 | 3 | 3.6 | 495.9 | 0.2 | 0.7 | 2.6 |
| At the limit | 100 | 3 | 8.5 | 705.9 | 4.3 | 8.5 | 97.0 |

## Change From Baseline

| Scenario | Completion time | Throughput | Average wait | Peak queue |
|---|---:|---:|---:|---:|
| More doors | 0.50x | 2.00x | -0.6s | -3.0 |
| Bigger door | 0.60x | 1.67x | -0.5s | -2.0 |
| Invite timing | 2.80x | 0.36x | -1.2s | -27.0 |
| Robot personality | 1.46x | 0.69x | -1.2s | -24.4 |
| At the limit | 3.40x | 0.98x | +2.9s | +70.0 |

## Interpretation

### More doors
This is the strongest structural intervention in the tested set. Two doors double the modeled admission capacity from three to six robots per tick, so completion time and waiting fall substantially.

### Bigger door
A five-robot-wide door increases capacity from three to five robots per tick. It improves the flow without changing the invitation pattern, but it is less powerful than adding an equally sized second door in this model.

### Invite timing
Spreading arrival times reduces synchronized queue pressure. It changes when robots arrive, not how many the door can admit, so its benefit is strongest as a peak-management strategy rather than a pure throughput strategy.

### Robot personality
Moderate punctuality differences create a smaller version of the invite-timing effect. This makes the crowd less synchronized, but it does not remove the fixed-capacity bottleneck.

### At the limit
The larger invite list makes the baseline bottleneck persistent: the queue and completion time scale with demand while the door capacity stays fixed. This is the clearest demonstration that an infinite or growing invite list cannot be solved by punctuality alone.

## Caveats

- This is a simplified discrete model: robots are admitted in FIFO order and collision avoidance is not modeled.
- The current timing and personality scenarios use randomized arrival offsets, not strategic scheduling or social utility.
- Door capacity is represented as robots admitted per simulation tick; the visual frontend interpolates their movement between backend states.
- The metrics are useful for relative comparison, not a physical prediction of a real building.

## Reproduce

```bash
python3 run_experiments.py
```

Generated on 2026-09-16 with 20 repetitions per scenario.
