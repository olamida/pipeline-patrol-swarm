"""A pipeline network: a long backbone with branches and a few loops.

Nodes are inspection points; edge weights are lengths in abstract distance
units. All-pairs shortest paths are precomputed (N is small).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class Network:
    n: int
    adj: List[List[Tuple[int, int]]]       # node -> [(neighbour, length)]
    dist: np.ndarray                        # all-pairs shortest distance
    nxt: np.ndarray                         # nxt[u, v] = next hop from u toward v
    depot: int

    def path(self, u: int, v: int) -> List[int]:
        out = []
        while u != v:
            u = int(self.nxt[u, v])
            out.append(u)
        return out

    def edge_len(self, u: int, v: int) -> int:
        return next(w for x, w in self.adj[u] if x == v)


def make_network(n: int = 60, seed: int = 0, extra_edges: int = 3) -> Network:
    rng = random.Random(seed)
    edges = {}
    for i in range(1, n):
        j = rng.randint(max(0, i - 4), i - 1)       # mostly chain-like, with branches
        edges[(j, i)] = rng.randint(1, 3)
    for _ in range(extra_edges):
        a, b = rng.sample(range(n), 2)
        if (min(a, b), max(a, b)) not in edges:
            edges[(min(a, b), max(a, b))] = rng.randint(2, 4)
    adj: List[List[Tuple[int, int]]] = [[] for _ in range(n)]
    for (a, b), w in edges.items():
        adj[a].append((b, w))
        adj[b].append((a, w))
    inf = 10 ** 9
    d = np.full((n, n), inf, dtype=np.int64)
    nx = np.full((n, n), -1, dtype=np.int64)
    for i in range(n):
        d[i, i] = 0
        nx[i, i] = i
    for a, b in edges:
        w = edges[(a, b)]
        d[a, b] = d[b, a] = w
        nx[a, b], nx[b, a] = b, a
    for k in range(n):
        for i in range(n):
            via = d[i, k] + d[k, :]
            better = via < d[i]
            d[i] = np.where(better, via, d[i])
            nx[i] = np.where(better, nx[i, k], nx[i])
    ecc = d.max(axis=1)
    return Network(n, adj, d, nx, int(np.argmin(ecc)))
