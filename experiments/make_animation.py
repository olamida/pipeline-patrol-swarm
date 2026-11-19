"""Render a patrol run as an animation from the real gossip simulator.

Run from the repository root:
    PYTHONPATH=src python experiments/make_animation.py

Agent positions, failures and tamper events are taken from ``patrol.sim.run``
with ``Config(record=True)``.  The graph layout is schematic (node index on the
x axis) because the synthetic network has no geographic coordinates.
"""
from __future__ import annotations

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from patrol.graph import make_network  # noqa: E402
from patrol.sim import Config, DEFAULT_FLEET, run  # noqa: E402


def main() -> None:
    net = make_network(seed=0)
    cfg = Config(policy="gossip", horizon=600, n_events=8, fail_prob=0.0,
                 seed=0, record=True)
    result = run(net, DEFAULT_FLEET, cfg)
    trace = result.trace
    assert trace is not None

    pos = {v: (float(v), 0.9 * math.sin(v * 1.7)) for v in range(net.n)}
    fig, ax = plt.subplots(figsize=(8.0, 3.6))
    for a, b, _ in {(min(u, v), max(u, v), w) for u in range(net.n) for v, w in net.adj[u]}:
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                color="#B8B8B2", lw=0.8, zorder=1)
    ax.plot(pos[net.depot][0], pos[net.depot][1], "s", color="#333", ms=7)
    markers = []
    colors = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]
    for i, spec in enumerate(DEFAULT_FLEET):
        m, = ax.plot([], [], "o" if spec.kind == "ugv" else "^",
                     color=colors[i], ms=10, mec="black", mew=0.6, zorder=4)
        markers.append(m)
    (events,) = ax.plot([], [], "x", color="#D55E00", ms=11, mew=2, zorder=5)
    info = ax.set_title("", fontsize=11, loc="left")
    ax.set_xlabel("schematic node index (chain backbone + branches)")
    ax.set_yticks([])
    fig.tight_layout()

    def frame(idx):
        snap = trace[idx]
        for i, m in enumerate(markers):
            if snap["alive"][i]:
                v = snap["pos"][i]
                m.set_data([pos[v][0]], [pos[v][1]])
            else:
                m.set_data([], [])
        ev = snap["pending"]
        events.set_data([pos[v][0] for v in ev], [pos[v][1] for v in ev])
        info.set_text(f"gossip patrol   t = {snap['t']:3d}   "
                      f"detected {snap['detected']}/{result.n_events}   "
                      f"open tamper events {len(ev)}")
        return markers + [events]

    out = os.path.join(ROOT, "figures", "demo_patrol.gif")
    anim = FuncAnimation(fig, frame, frames=range(0, len(trace), 5), blit=False)
    anim.save(out, writer=PillowWriter(fps=12), dpi=80)
    plt.close(fig)
    print(f"wrote {out}")
    print(f"mean_ttd={result.mean_ttd:.1f} undetected={result.undetected_frac:.0%}")


if __name__ == "__main__":
    main()
