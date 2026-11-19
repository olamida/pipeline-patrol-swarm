"""Patrol simulator: heterogeneous agents, tamper events, failures, gossip.

Agents move along shortest paths between inspection nodes. Every node an agent
passes counts as inspected at that tick (ground truth). A *tamper event* appears
at (node, t0) and is detected at the first inspection of that node at t >= t0.

Policies (who decides where to go next):
  random     random feasible node
  partition  nodes split among agents once (nearest home), fixed cyclic tour each
  cyclic     everyone walks one shared cyclic order, staggered
  gossip     decentralized: idleness-greedy from a *local* last-visit map that is
             merged by gossip when agents are within comm range, with claim avoidance
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .graph import Network


@dataclass(frozen=True)
class AgentSpec:
    kind: str                 # "uav" | "ugv"
    speed: float              # distance units per tick
    endurance: float = 1e18   # distance units per charge (uav)
    recharge: int = 0         # ticks spent at depot to recharge


@dataclass
class Config:
    policy: str = "gossip"
    horizon: int = 3000
    n_events: int = 40
    fail_prob: float = 0.0          # chance each agent fails once, uniformly in [fail_lo, fail_hi]
    fail_lo: int = 500
    fail_hi: int = 2000
    comm_range: float = 6.0
    comm_loss: float = 0.0          # prob a gossip exchange is dropped
    claims: bool = True             # gossip: honour/announce target claims
    jitter: float = 10.0            # gossip: uniform noise added to target scores
    beta: float = 1.0               # gossip: distance penalty weight
    seed: int = 0
    record: bool = False            # optional per-tick snapshot for the demo animation


@dataclass
class Result:
    n_events: int
    detected: int
    undetected_frac: float
    mean_ttd: float                 # detected events only
    p95_ttd: float                  # undetected events censored at (horizon - t0)
    mean_idleness: float            # time-average over nodes of (t - last true visit)
    failed_agents: int
    trace: Optional[List[dict]] = None   # only populated when Config.record is True


DEFAULT_FLEET = [AgentSpec("uav", 3.0, 120.0, 20), AgentSpec("uav", 3.0, 120.0, 20),
                 AgentSpec("ugv", 1.0), AgentSpec("ugv", 1.0), AgentSpec("ugv", 1.0)]


class _Agent:
    def __init__(self, i: int, spec: AgentSpec, net: Network, n_agents: int):
        self.i, self.spec, self.net = i, spec, net
        self.cur = net.depot
        self.path: List[int] = []
        self.rem = 0.0                  # distance left on current edge
        self.fuel = spec.endurance
        self.charging = 0
        self.alive = True
        self.belief = np.full(net.n, -1.0)       # last-visit time as this agent believes
        self.claims: Dict[int, tuple] = {}       # node -> (agent, eta, t_claim)
        self.target: Optional[int] = None
        self.tour: List[int] = []
        self.tour_i = 0


def _tour_order(net: Network, nodes: List[int], start: int) -> List[int]:
    """Nearest-neighbour ordering of `nodes` starting from `start`."""
    left, out, cur = set(nodes), [], start
    while left:
        cur = min(left, key=lambda v: (net.dist[cur, v], v))
        left.remove(cur)
        out.append(cur)
    return out


def run(net: Network, fleet: List[AgentSpec], cfg: Config) -> Result:
    rng = random.Random(cfg.seed)
    n = net.n
    agents = [_Agent(i, s, net, len(fleet)) for i, s in enumerate(fleet)]
    # --- ground truth -------------------------------------------------------
    last_true = np.zeros(n)
    events = sorted((rng.randint(200, cfg.horizon - 200), rng.randrange(n)) for _ in range(cfg.n_events))
    ttd: List[Optional[float]] = [None] * len(events)
    pending: Dict[int, List[int]] = {}
    fail_at = {}
    for a in agents:
        if rng.random() < cfg.fail_prob:
            fail_at[a.i] = rng.randint(cfg.fail_lo, cfg.fail_hi)
    idle_sum = 0.0
    # --- static policy setup --------------------------------------------------
    if cfg.policy == "partition":
        owner = {v: min(range(len(agents)), key=lambda k: (net.dist[net.depot, v] * 0 + _home(net, agents, k, v), k))
                 for v in range(n)}
        for a in agents:
            a.tour = _tour_order(net, [v for v in range(n) if owner[v] == a.i], net.depot)
    elif cfg.policy == "cyclic":
        order = _tour_order(net, list(range(n)), net.depot)
        for a in agents:
            a.tour = order
            a.tour_i = (a.i * n) // len(agents)

    ev_i = 0
    trace: Optional[List[dict]] = [] if cfg.record else None
    for t in range(cfg.horizon):
        while ev_i < len(events) and events[ev_i][0] <= t:
            pending.setdefault(events[ev_i][1], []).append(ev_i)
            ev_i += 1
        for a in agents:
            if a.alive and a.i in fail_at and t >= fail_at[a.i]:
                a.alive = False
        for a in agents:
            if not a.alive:
                continue
            _step(a, t, net, agents, cfg, rng, last_true, pending, ttd, events)
        if cfg.policy == "gossip":
            _gossip(agents, net, cfg, rng, t)
        idle_sum += float((t - last_true).mean())
        if cfg.record:
            trace.append({"t": t,
                          "pos": [a.cur for a in agents],
                          "alive": [a.alive for a in agents],
                          "pending": sorted(pending.keys()),
                          "detected": sum(1 for x in ttd if x is not None)})
    det = [x for x in ttd if x is not None]
    cens = [x if x is not None else cfg.horizon - e[0] for x, e in zip(ttd, events)]
    return Result(len(events), len(det), 1 - len(det) / len(events),
                  float(np.mean(det)) if det else float("nan"),
                  float(np.percentile(cens, 95)), idle_sum / cfg.horizon,
                  sum(1 for a in agents if not a.alive), trace)


def _home(net, agents, k, v):
    """Static assignment cost: distance from the depot, scaled by agent speed
    so faster agents get farther nodes (a fair static baseline)."""
    return net.dist[net.depot, v] / agents[k].spec.speed + 0.01 * k


def _visit(a, v, t, last_true, pending, ttd, events):
    last_true[v] = t
    a.belief[v] = t
    for k in pending.pop(v, []):
        ttd[k] = t - events[k][0]


def _feasible(a, v, net):
    return a.fuel >= net.dist[a.cur, v] + net.dist[v, net.depot]


def _choose(a, t, net, agents, cfg, rng):
    spec = a.spec
    if a.cur == net.depot and a.fuel < spec.endurance - 1e-9 and spec.recharge:
        a.charging, a.fuel = spec.recharge, spec.endurance
        return None
    if cfg.policy == "random":
        cands = [v for v in range(net.n) if v != a.cur and _feasible(a, v, net)]
        v = rng.choice(cands) if cands else net.depot
    elif cfg.policy in ("partition", "cyclic"):
        v = None
        if a.tour:
            for _ in range(len(a.tour)):
                c = a.tour[a.tour_i % len(a.tour)]
                if c != a.cur and _feasible(a, c, net):
                    v = c
                    a.tour_i += 1
                    break
                if c == a.cur:
                    a.tour_i += 1
                else:
                    break                     # next stop infeasible: refuel first
        if v is None:
            v = net.depot
    else:  # gossip
        now = float(t)
        best, v = -1e18, None
        for c in range(net.n):
            if c == a.cur or not _feasible(a, c, net):
                continue
            cost = net.dist[a.cur, c] / spec.speed
            cl = a.claims.get(c)
            if cfg.claims and cl and cl[0] != a.i and cl[1] > now and cl[1] <= now + cost:
                continue                       # someone else gets there first
            score = (now + cost - a.belief[c]) - cfg.beta * cost * 10
            if cfg.jitter:
                score += rng.uniform(0, cfg.jitter)
            if score > best:
                best, v = score, c
        if v is None:
            v = net.depot
        a.claims[v] = (a.i, t + net.dist[a.cur, v] / spec.speed, t)
    if v == a.cur:
        return None
    return v


def _step(a, t, net, agents, cfg, rng, last_true, pending, ttd, events):
    if a.charging > 0:
        a.charging -= 1
        return
    if not a.path:
        v = _choose(a, t, net, agents, cfg, rng)
        if v is None:
            return
        a.target = v
        a.path = net.path(a.cur, v)
        a.rem = float(net.edge_len(a.cur, a.path[0])) if a.path else 0.0
    budget = a.spec.speed
    while budget > 1e-12 and a.path:
        if a.rem <= budget:
            budget -= a.rem
            nxt = a.path.pop(0)
            a.fuel -= net.edge_len(a.cur, nxt)
            a.cur = nxt
            _visit(a, nxt, t, last_true, pending, ttd, events)
            a.rem = float(net.edge_len(a.cur, a.path[0])) if a.path else 0.0
        else:
            a.rem -= budget
            budget = 0.0


def _gossip(agents, net, cfg, rng, t):
    live = [a for a in agents if a.alive]
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            if net.dist[a.cur, b.cur] > cfg.comm_range:
                continue
            if rng.random() < cfg.comm_loss:
                continue
            m = np.maximum(a.belief, b.belief)
            a.belief, b.belief = m.copy(), m.copy()
            for x, y in ((a, b), (b, a)):
                for node, cl in x.claims.items():
                    if node not in y.claims or y.claims[node][2] < cl[2]:
                        y.claims[node] = cl


POLICIES = ("random", "partition", "cyclic", "gossip")
