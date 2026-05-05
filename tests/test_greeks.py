"""Phase 3 tests — analytic Greeks vs central finite differences of BS price."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from core.black_scholes import BlackScholes
from core.greeks import Greeks

P = dict(S=100.0, K=100.0, T=0.5, r=0.05, sigma=0.20, q=0.0)
G = Greeks(**P)
H = 1e-4


def bs_price(option_type="call", **over):
    p = {**P, **over}
    b = BlackScholes(p["S"], p["K"], p["T"], p["r"], p["sigma"], p["q"])
    return b.call_price() if option_type == "call" else b.put_price()


def central(param, option_type="call", h=H):
    up = bs_price(option_type, **{param: P[param] + h})
    dn = bs_price(option_type, **{param: P[param] - h})
    return (up - dn) / (2 * h)


@pytest.mark.parametrize("ot", ["call", "put"])
def test_delta_fd(ot):
    assert abs(G.delta(ot) - central("S", ot)) < 1e-6


def test_gamma_fd():
    h = 1e-3
    fd = (bs_price(S=P["S"] + h) - 2 * bs_price() + bs_price(S=P["S"] - h)) / h**2
    assert abs(G.gamma() - fd) < 1e-5


@pytest.mark.parametrize("ot", ["call", "put"])
def test_theta_fd_per_day(ot):
    fd = -central("T", ot) / 365.0  # theta reported per calendar day
    assert abs(G.theta(ot) - fd) < 1e-6


def test_vega_fd_per_pct():
    fd = central("sigma") / 100.0  # vega reported per 1% vol
    assert abs(G.vega() - fd) < 1e-6


@pytest.mark.parametrize("ot", ["call", "put"])
def test_rho_fd_per_pct(ot):
    fd = central("r", ot) / 100.0  # rho reported per 1% rate
    assert abs(G.rho(ot) - fd) < 1e-6


def test_vanna_fd():
    h = 1e-4  # d(delta)/d(sigma), raw units
    up = Greeks(**{**P, "sigma": P["sigma"] + h}).delta("call")
    dn = Greeks(**{**P, "sigma": P["sigma"] - h}).delta("call")
    assert abs(G.vanna() - (up - dn) / (2 * h)) < 1e-4


def test_volga_fd():
    h = 1e-3  # d2V/dsigma2, raw units
    fd = (bs_price(sigma=P["sigma"] + h) - 2 * bs_price() + bs_price(sigma=P["sigma"] - h)) / h**2
    # volga() is built on the per-1% vega, so it reports d2V/dsigma2 / 100
    assert abs(G.volga() - fd / 100.0) < 1e-5


@pytest.mark.parametrize("ot", ["call", "put"])
def test_charm_fd_per_day(ot):
    h = 1e-5
    up = Greeks(**{**P, "T": P["T"] + h}).delta(ot)
    dn = Greeks(**{**P, "T": P["T"] - h}).delta(ot)
    fd = (up - dn) / (2 * h) / 365.0  # codebase convention: charm = +dDelta/dT per day
    assert abs(G.charm(ot) - fd) < 1e-6


def test_sanity_signs():
    assert 0 < G.delta("call") < 1
    assert -1 < G.delta("put") < 0
    assert G.gamma() > 0 and G.vega() > 0
    assert G.theta("call") < 0
    assert G.rho("call") > 0 > G.rho("put")
    assert set(G.all_greeks()) == {"delta", "gamma", "theta", "vega", "rho"}
