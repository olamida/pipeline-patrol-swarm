import csv, collections, math, os, statistics as st
R = os.path.join(os.path.dirname(__file__), "..", "results")
d = collections.defaultdict(list)
for r in csv.DictReader(open(f"{R}/patrol.csv")):
    d[(r["label"], r["fail_prob"])].append(r)
lines = ["| policy | agent failures | mean time-to-detect | p95 TTD (censored) | undetected | mean idleness |", "|---|---|---|---|---|---|"]
for (lab, fp), v in d.items():
    f = lambda c: [float(x[c]) for x in v]
    ci = lambda c: 1.96 * st.stdev(f(c)) / math.sqrt(len(v))
    lines.append(f"| {lab} | {'60%' if fp == '0.6' else 'none'} | {st.mean(f('mean_ttd')):.1f} ± {ci('mean_ttd'):.1f} | "
                 f"{st.mean(f('p95_ttd')):.0f} ± {ci('p95_ttd'):.0f} | {100*st.mean(f('undetected')):.1f}% | {st.mean(f('idleness')):.1f} |")
open(f"{R}/summary.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
