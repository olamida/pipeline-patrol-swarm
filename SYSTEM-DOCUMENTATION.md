# SYSTEM-DOCUMENTATION — pipeline-patrol-swarm

Deep technical / developer documentation. For running instructions see
`USER-GUIDE.md`; for the work ledger see `PENDING-TASKS.md`.

## 1. Purpose and scope

Decentralized patrol of a synthetic 60-node pipeline graph under tamper events and agent failures.

Research question: **How gracefully does a mixed UAV/UGV patrol degrade when agents are lost?**

This is a simulation study. No hardware measurements, external datasets or
proprietary data are involved. The repository is intentionally small enough to
be read end-to-end by a reviewer in one sitting.

## 2. Architecture

| Component | Responsibility |
|---|---|
| `src/patrol/graph.py` | Synthetic network, shortest paths and edge lengths. |
| `src/patrol/sim.py` | Heterogeneous agents, tamper events, failures, gossip merge and result metrics. |
| `experiments/run_experiments.py` | 30-seed policy/failure/loss sweeps. |
| `experiments/summarize.py` | Mean and 95% CI tables. |

Dependencies flow one way: configuration/scenario → model/algorithm →
experiment runner → results → figures/animation. The simulator does not read
its own results; results are an output only.

## 3. Data flow

1. A seeded scenario, task set, signal or topology is constructed.
2. The core model advances in discrete steps (ticks or control steps).
3. Metrics are accumulated independently of the decision logic where possible
   (for example, a ground-truth collision checker rather than the agents' beliefs).
4. `experiments/` writes machine-readable results under `results/`.
5. `make_figures.py` and `make_animation.py` read those results or re-run the
   seeded simulator to produce visual artefacts.

## 4. Algorithms / numerical methods

See `README.md` for the high-level description and, where present,
`docs/DESIGN.md` or `DEVELOPMENT_GUIDE.md` for the full derivation. The
implementation is the authoritative reference: start at the module table in
section 2 and follow the entry point used by `PYTHONPATH=src python -m pytest -q tests`.

Reproducibility rules:
- Every stochastic component is driven by an explicit seed.
- Experiment parameters are recorded in the result rows.
- A change to a result number requires regenerating the CSV/JSON, not editing prose.

## 5. Results and evidence

- Mean time-to-detect without failures: gossip 20.8 ± 1.1, cyclic 27.7 ± 2.1, partition 71.4 ± 3.9 — `results/summary.md`.
- With 60% agent failures: partition leaves 34.8% of events undetected; gossip 1.4% and cyclic 1.2% — `results/summary.md`.
- gossip and cyclic are statistically indistinguishable under failures (42.6 ± 5.0 vs 47.6 ± 5.4) — `results/summary.md`.
- With all gossip messages dropped, mean TTD is 22.6 ± 1.6 vs 20.8 ± 1.1 with full gossip — `results/summary.md`.

## 6. Animation pipeline

`python experiments/make_animation.py` renders `figures/demo_patrol.gif`. It uses the project's own simulator
(or an explicitly documented pure-Python reference of the same controller) and
Matplotlib's Pillow writer. Frames are subsampled to keep the GIF small; the
underlying trajectory is not resampled or smoothed. Recorded gossip patrol over the schematic graph: agents move between inspection nodes while open tamper events are marked until first inspection.

## 7. Build, test and CI

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m pytest -q tests
python experiments/run_experiments.py && python experiments/summarize.py && python experiments/make_figures.py
python experiments/make_animation.py
```

CI (`.github/workflows/ci.yml`) runs on push and pull request. Jobs install the
documented dependencies, set `PYTHONPATH=src` where required, and run the test
suite. Repositories that call C code install a system compiler in CI; footprint
measurement with cross-compilers is deliberately optional.

## 8. Extension points

- Add a new scenario/policy by extending the corresponding factory or registry
  and a seeded test, then re-run the full experiment suite.
- Add a new metric by writing it into the result row and updating
  `experiments/summarize.py` and the README table together.
- Add a new animation by recording the relevant simulator state (prefer an
  optional `record` flag over duplicating the stepping logic) and saving via
  `FuncAnimation`/`PillowWriter` in `experiments/`.

## 9. Known limitations

- Synthetic network and uniform event locations; no hotspot/risk weighting or sensing errors.
- Jitter and distance penalty were tuned on separate seeds (1000–1009); reported seeds are 0–29.
- Failure is not detected explicitly and `partition` never re-partitions.
- Communication range uses the last node, not the position on an edge; p95 treats undetected events as censored.

## 10. Relation to the rest of the portfolio

Application rung of the same research ladder as `stc-corridors`; uses decentralized ideas related to `mesh-routing-sim`.

## 11. Release metadata

`CITATION.cff` carries title, author (Yusuf Ndanusa Yahaya), version 0.1.0,
release date, repository URL and MIT license. No DOI or ORCID is claimed.
