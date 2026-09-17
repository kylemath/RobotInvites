# Robot Invites / Doorway Lab

A dependency-free Python backend and Three.js overhead frontend for exploring the robot-party doorway problem.

## Project links

- [Live doorway lab](index.html)
- [Academic manuscript PDF](manuscript/manuscript.pdf)
- [Manuscript source](manuscript/manuscript.tex)
- [Experiment summary](manuscript/experiment-summary.md)
- [Raw experiment results](manuscript/experiment-results.json)
- [Interactive frontend source](sketch.js)
- [Python simulation backend](backend.py)

## Run

```bash
python3 backend.py
```

Open <http://127.0.0.1:8000>.

The backend also supports headless runs:

```bash
curl -X POST http://127.0.0.1:8000/api/reset -H 'Content-Type: application/json' -d '{"robot_count":30}'
curl -X POST http://127.0.0.1:8000/api/step -H 'Content-Type: application/json' -d '{"seconds":0.25}'
curl http://127.0.0.1:8000/api/log
```

The log rows are JSON objects with time, inside, waiting, not-yet-arrived, throughput, average wait, maximum wait, door capacity, and utilization.

## Manuscript and reproducible figures

The academic manuscript lives in the [manuscript](manuscript/) folder. The source is [manuscript.tex](manuscript/manuscript.tex), with references in [references.bib](manuscript/references.bib). Recreate the experiment data and figures with:

```bash
python3 run_experiments.py
python3 -m pip install --user matplotlib numpy
python3 plot_experiments.py
```

This writes `experiment-results.json`, `experiment-summary.md`, `figures.pdf`, and `figures.png` inside `manuscript/`. With a LaTeX installation available, build the manuscript with:

```bash
make -C manuscript
```

The manuscript treats Operation Igloo White as historical context for sensor-mediated decision systems. It does not claim that the historical system used modern machine learning or autonomously authorized strikes.

The frontend is designed to be published as a GitHub Pages project site. The interactive API controls require the Python backend; the static page remains a visual entry point and links to the reproducible manuscript materials.
