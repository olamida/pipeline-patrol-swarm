import csv, collections, math, os, statistics as st
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
H = os.path.dirname(__file__)
d = collections.defaultdict(list)
for r in csv.DictReader(open(f"{H}/../results/patrol.csv")):
    d[(r["label"], r["fail_prob"])].append(float(r["mean_ttd"]))
labs = ["random", "partition", "cyclic", "gossip-nojitter", "gossip"]
fig, ax = plt.subplots(figsize=(8, 4))
w = 0.38
for k, (fp, name, c) in enumerate((("0.0", "no failures", "#2a6f97"), ("0.6", "60% of agents fail", "#c0392b"))):
    m = [st.mean(d[(l, fp)]) for l in labs]
    e = [1.96 * st.stdev(d[(l, fp)]) / math.sqrt(len(d[(l, fp)])) for l in labs]
    ax.bar([i + (k - .5) * w for i in range(len(labs))], m, w, yerr=e, label=name, color=c, capsize=3)
ax.set_xticks(range(len(labs))); ax.set_xticklabels(labs)
ax.set_ylabel("mean time to detect tamper (ticks)"); ax.legend(); ax.set_title("Pipeline patrol, 30 seeds, 95% CI")
plt.tight_layout(); os.makedirs(f"{H}/../figures", exist_ok=True); plt.savefig(f"{H}/../figures/fig_patrol.png", dpi=160)
