"""Phase 4 tests — Monte Carlo pricer vs Black-Scholes ground truth."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from core.black_scholes import BlackScholes
from core.monte_carlo import MonteCarlo

P = (100.0, 100.0, 0.5, 0.05, 0.20)
BS_CALL = BlackScholes(*P).call_price()
BS_PUT = BlackScholes(*P).put_price()


@pytest.mark.parametrize("ot,bs_px", [("call", BS_CALL), ("put", BS_PUT)])
def test_mc_within_3se_of_bs(ot, bs_px):
    res = MonteCarlo(*P, seed=42).price(ot, n_simulations=100_000, bs_price=bs_px)
    assert abs(res.price - bs_px) < 3 * res.std_error
    assert res.n_simulations == 200_000  # antithetic doubles paths


def test_mc_deterministic_with_seed():
    a = MonteCarlo(*P, seed=7).price("call", 10_000).price
    b = MonteCarlo(*P, seed=7).price("call", 10_000).price
    assert a == b


def test_std_error_shrinks_with_n():
    mc = MonteCarlo(*P, seed=42)
    se_small = mc.price("call", 1_000).std_error
    se_big = mc.price("call", 100_000).std_error
    assert se_big < se_small / 5  # ~1/sqrt(100x) = 10x, allow slack


def test_convergence_study_rows():
    rows = MonteCarlo(*P, seed=42).convergence_study("call", [100, 1000], bs_price=BS_CALL)
    assert len(rows) == 2 and rows[1]["std_error"] < rows[0]["std_error"]


def test_asian_call_below_european():
    mc = MonteCarlo(*P, seed=42)
    asian = mc.asian_call_price(n_simulations=20_000, n_steps=50)
    assert 0 < asian.price < BS_CALL  # averaging reduces effective vol


def test_invalid_option_type():
    with pytest.raises(ValueError):
        MonteCarlo(*P).price("digital")
