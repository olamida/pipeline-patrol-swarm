# USER-GUIDE — pipeline-patrol-swarm

End-user manual. You do not need to edit code to follow this guide.

## 1. What you can do with it

Decentralized patrol of a synthetic 60-node pipeline graph under tamper events and agent failures.

The research question is: *How gracefully does a mixed UAV/UGV patrol degrade when agents are lost?*

## 2. Install

```bash
git clone https://github.com/olamida/pipeline-patrol-swarm.git
cd pipeline-patrol-swarm
pip install -r requirements.txt
```

Python 3.10+ is assumed. On Windows use `.venv\Scripts\activate` instead of
`source .venv/bin/activate` if you create a virtual environment.

## 3. Watch the animation

Open `figures/demo_patrol.gif` directly on GitHub or in any image viewer; GitHub plays
GIFs inline. The animation shows: Recorded gossip patrol over the schematic graph: agents move between inspection nodes while open tamper events are marked until first inspection.

To regenerate it from source:

```bash
python experiments/make_animation.py
```

## 4. Verify the installation

```bash
PYTHONPATH=src python -m pytest -q tests
```

A passing run prints a test summary with no failures. If a C compiler is
mentioned as missing, install a system C compiler (gcc on Linux, Xcode command
line tools on macOS, MinGW/MSVC on Windows) and rerun.

## 5. Run the full experiments

```bash
python experiments/run_experiments.py && python experiments/summarize.py && python experiments/make_figures.py
```

Outputs appear in `results/` (CSV/JSON/Markdown tables) and `figures/`
(PNG/GIF). Re-running with the shipped seeds should reproduce the shipped
numbers; small differences can occur with different library versions.

## 6. How to read the outputs

- Mean time-to-detect without failures: gossip 20.8 ± 1.1, cyclic 27.7 ± 2.1, partition 71.4 ± 3.9 — `results/summary.md`.
- With 60% agent failures: partition leaves 34.8% of events undetected; gossip 1.4% and cyclic 1.2% — `results/summary.md`.
- gossip and cyclic are statistically indistinguishable under failures (42.6 ± 5.0 vs 47.6 ± 5.4) — `results/summary.md`.
- With all gossip messages dropped, mean TTD is 22.6 ± 1.6 vs 20.8 ± 1.1 with full gossip — `results/summary.md`.

## 7. Known limitations (please read)

- Synthetic network and uniform event locations; no hotspot/risk weighting or sensing errors.
- Jitter and distance penalty were tuned on separate seeds (1000–1009); reported seeds are 0–29.
- Failure is not detected explicitly and `partition` never re-partitions.
- Communication range uses the last node, not the position on an edge; p95 treats undetected events as censored.

## 8. Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError` | Running from the wrong directory or missing `PYTHONPATH=src` | Run from the repository root and use the exact command in section 4. |
| Build fails with "gcc not found" | No system C compiler | Install gcc/Xcode CLT/MinGW; the pure-Python reference is only for the animation. |
| Animation script cannot find sibling repo | `stc-corridors` not beside `stc-formal` | Clone both repositories side by side, or install `stc` into the environment. |
| Numbers differ from README | Different seeds or library versions | Use the command in section 5 and compare against `results/` in the repo. |

## 9. Getting help

Open an issue with the exact command, your OS/Python version and the last 20
lines of output. Please do not attach private or employer data.
