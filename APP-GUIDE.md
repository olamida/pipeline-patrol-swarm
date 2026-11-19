# APP-GUIDE — pipeline-patrol-swarm

**Question:** How gracefully does a mixed UAV/UGV patrol degrade when agents are lost?

**One-line summary:** Decentralized patrol of a synthetic 60-node pipeline graph under tamper events and agent failures.

This guide records what the application/project has already done and what is still
to be done. It is the session-to-session entry point: read this first, then
`USER-GUIDE.md` to run it, `SYSTEM-DOCUMENTATION.md` to change it, and
`PENDING-TASKS.md` for the live work ledger.

## Work already executed

- Built a connected 60-node synthetic network (backbone, branches, 3 loops) with an all-pairs shortest-path table.
- Modelled 2 fast endurance-limited UAVs and 3 unlimited UGVs, 40 tamper events per run and one failure per agent with configurable probability.
- Implemented four policies: random, static partition, cyclic tour and idleness-greedy gossip with local last-visit maps, claims and jitter.
- Ran 30-seed experiments including failures, total failure, message loss and a no-jitter ablation; results in `results/patrol.csv` and `results/summary.md`.
- Found and fixed a herding bug: identical shared beliefs made agents choose the same target; a small score jitter improved mean TTD from 45.0 to 20.8.
- Wrote 12 tests and a CI workflow; added optional per-tick recording for the demo animation.
- Rendered `figures/demo_patrol.gif` directly from a recorded gossip run.

## Work to be executed (next)

- Add risk/hotspot weighting for tamper events and sensing errors.
- Add a stronger re-partitioning baseline when agents die.
- Compute communication range from the agent's position on an edge rather than its last node.
- Validate on real pipeline topology and with realistic UAV endurance/recharge models.

## High-level flow

1. Configure a seeded scenario / task set / signal.
2. Run the simulator or experiment script in this repository.
3. Metrics are written to `results/`; figures to `figures/`.
4. The animation in `figures/demo_patrol.gif` is rendered from the same simulator state.

## Commands at a glance

| Purpose | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Verify | `PYTHONPATH=src python -m pytest -q tests` |
| Experiments | `python experiments/run_experiments.py && python experiments/summarize.py && python experiments/make_figures.py` |
| Animation | `python experiments/make_animation.py` |

## Where this connects

Application rung of the same research ladder as `stc-corridors`; uses decentralized ideas related to `mesh-routing-sim`.

## Honesty notes

All numbers quoted in this repository come from files under `results/`.
Simulation-only results are not hardware measurements, and the documented
limitations in `README.md` are part of the deliverable.
