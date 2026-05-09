"""Phase 5 tests — BS-vs-MC comparison and volatility analytics."""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from core.black_scholes import BlackScholes
from analytics.comparison import BSvsMC
from analytics.volatility import VolatilityAnalytics


def test_bsvsmc_compare_consistency():
    c = BSvsMC(100, 100, 0.5, 0.05, 0.20, seed=42).compare("call", 50_000)
    assert abs(c["abs_error"] - abs(c["bs_price"] - c["mc_price"])) < 1e-12
    assert c["bs_in_ci"] is True


def test_convergence_table_has_bs_and_rel_error():
    rows = BSvsMC(100, 100, 0.5, 0.05, 0.20, seed=42).convergence_table("call", [500, 5_000])
    assert all("mc_price" in r and "bs_price" in r and "rel_error_pct" in r for r in rows)


def test_vol_smile_recovers_flat_vol():
    va = VolatilityAnalytics(S=100, r=0.05)
    strikes = [90.0, 100.0, 110.0]
    prices = {K: BlackScholes(100, K, 0.5, 0.05, 0.25).call_price() for K in strikes}
    smile = va.vol_smile(prices, T=0.5)
    assert all(abs(iv - 0.25) < 1e-6 for iv in smile.values())


def test_term_structure_recovers_vols():
    va = VolatilityAnalytics(S=100, r=0.05)
    atm = {T: BlackScholes(100, 100, T, 0.05, 0.22).call_price() for T in (0.25, 0.5, 1.0)}
    term = va.term_structure(atm)
    assert all(abs(iv - 0.22) < 1e-6 for iv in term.values())


def test_vol_surface_shape_and_values():
    va = VolatilityAnalytics(S=100, r=0.05)
    Ks, Ts = [95.0, 105.0], [0.25, 0.5, 1.0]
    pm = [[BlackScholes(100, K, T, 0.05, 0.3).call_price() for K in Ks] for T in Ts]
    surf = va.vol_surface(Ks, Ts, pm)
    assert len(surf) == 3 and len(surf[0]) == 2
    assert all(abs(iv - 0.3) < 1e-6 for row in surf for iv in row)


def test_historical_vol_constant_prices_is_zero():
    vols = VolatilityAnalytics.historical_vol([100.0] * 40, window=21)
    assert all(v == 0.0 for v in vols)


def test_historical_vol_positive_and_length():
    prices = [100.0 * (1.01 if i % 2 else 0.99) ** 1 * (1 + 0.001 * i) for i in range(40)]
    vols = VolatilityAnalytics.historical_vol(prices, window=21)
    assert len(vols) == 39 - 21 and all(v > 0 for v in vols)


def test_historical_vol_too_few_prices_raises():
    with pytest.raises(ValueError):
        VolatilityAnalytics.historical_vol([100.0] * 10, window=21)
