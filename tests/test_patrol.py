import numpy as np
import pytest
from patrol import Config, make_network, run, POLICIES
from patrol.sim import AgentSpec, DEFAULT_FLEET


def test_network_is_connected_and_metric():
    net = make_network(60, seed=3)
    assert (net.dist < 10 ** 8).all()
    assert (net.dist == net.dist.T).all()
    for u in range(0, 60, 7):
        for v in range(0, 60, 11):
            p = net.path(u, v)
            length, cur = 0, u
            for x in p:
                length += net.edge_len(cur, x)
                cur = x
            assert length == net.dist[u, v]


@pytest.mark.parametrize("policy", POLICIES)
def test_deterministic(policy):
    net = make_network(30, seed=1)
    cfg = Config(policy=policy, horizon=600, n_events=10, seed=4)
    a, b = run(net, DEFAULT_FLEET, cfg), run(net, DEFAULT_FLEET, cfg)
    assert a == b


@pytest.mark.parametrize("policy", POLICIES)
def test_everyone_eventually_found_when_no_failures(policy):
    net = make_network(40, seed=2)
    r = run(net, DEFAULT_FLEET, Config(policy=policy, horizon=2000, n_events=25, seed=1))
    assert r.undetected_frac <= 0.05


def test_total_failure_leaves_events_undetected():
    net = make_network(40, seed=2)
    r = run(net, DEFAULT_FLEET, Config(policy="gossip", horizon=2000, n_events=30, fail_prob=1.0,
                                       fail_lo=5, fail_hi=50, seed=1))
    assert r.failed_agents == len(DEFAULT_FLEET) and r.undetected_frac > 0.8


def test_faster_fleet_is_not_slower():
    net = make_network(40, seed=5)
    slow = [AgentSpec("ugv", 1.0)] * 3
    fast = [AgentSpec("ugv", 3.0)] * 3
    cfg = Config(policy="cyclic", horizon=2000, n_events=30, seed=2)
    assert run(net, fast, cfg).mean_ttd < run(net, slow, cfg).mean_ttd


def test_uav_with_tiny_endurance_still_returns_and_detects():
    net = make_network(30, seed=0)
    fleet = [AgentSpec("uav", 3.0, 2 * float(net.dist[net.depot].max()) + 2, 5)]
    r = run(net, fleet, Config(policy="gossip", horizon=3000, n_events=15, seed=3))
    assert r.detected >= 12
