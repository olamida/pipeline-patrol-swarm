"""30 seeds per cell. Seeds 0..29 (beta was tuned on seeds 1000..1007)."""
import csv, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from patrol import Config, make_network, run, POLICIES
from patrol.sim import DEFAULT_FLEET
OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)
SEEDS = 5 if "--quick" in sys.argv else 30
cells = [(p, p, fp, 0.0, None) for p in POLICIES for fp in (0.0, 0.6)]
cells += [("gossip-nojitter", "gossip", fp, 0.0, 0.0) for fp in (0.0, 0.6)]
cells += [(f"gossip-loss{l}", "gossip", fp, l, None) for l in (0.5, 0.95, 1.0) for fp in (0.0, 0.6)]
rows = []
for label, pol, fp, loss, jit in cells:
    for s in range(SEEDS):
        kw = {} if jit is None else {"jitter": jit}
        r = run(make_network(60, seed=s), DEFAULT_FLEET,
                Config(policy=pol, fail_prob=fp, comm_loss=loss, seed=s, **kw))
        rows.append(dict(label=label, policy=pol, fail_prob=fp, comm_loss=loss, seed=s,
                         mean_ttd=r.mean_ttd, p95_ttd=r.p95_ttd, undetected=r.undetected_frac,
                         idleness=r.mean_idleness, failed=r.failed_agents))
    print(label, fp, flush=True)
dest = f"{OUT}/{'quick' if SEEDS == 5 else 'patrol'}.csv"
with open(dest, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
