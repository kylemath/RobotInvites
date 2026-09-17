"""Generate manuscript figures from experiment-results.json."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / "experiment-results.json").read_text(encoding="utf-8"))
SCENARIOS = DATA["scenarios"]
names = [item["name"] for item in SCENARIOS]
summary = [item["summary"] for item in SCENARIOS]
colors = ["#17211f", "#27756d", "#d9a441", "#7c91a5", "#c45d91", "#f26e4f"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 11})

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
x = np.arange(len(names))
axes[0].bar(x, [row["completion_time"] for row in summary], color=colors)
axes[0].set_title("Time until all robots enter")
axes[0].set_ylabel("seconds")
axes[0].set_xticks(x, names, rotation=35, ha="right")
axes[0].grid(axis="y", color="#dddddd", linewidth=.6)
axes[0].set_axisbelow(True)
for index, row in enumerate(summary):
    axes[0].text(index, row["completion_time"] + .15, f"{row['completion_time']:.1f}", ha="center", va="bottom", fontsize=8)

axes[1].bar(x, [row["average_wait"] for row in summary], color=colors)
axes[1].set_title("Mean admission wait")
axes[1].set_ylabel("seconds")
axes[1].set_xticks(x, names, rotation=35, ha="right")
axes[1].grid(axis="y", color="#dddddd", linewidth=.6)
axes[1].set_axisbelow(True)
for index, row in enumerate(summary):
    axes[1].text(index, row["average_wait"] + .08, f"{row['average_wait']:.1f}", ha="center", va="bottom", fontsize=8)
fig.suptitle("Robot Invites: repeated headless experiments", fontweight="bold")
fig.savefig(ROOT / "figures.pdf", bbox_inches="tight")
fig.savefig(ROOT / "figures.png", dpi=220, bbox_inches="tight")
print("Wrote figures.pdf and figures.png")
