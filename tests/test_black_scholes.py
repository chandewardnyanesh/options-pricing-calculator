"""Phase 2 tests — Black-Scholes pricing, parity, implied volatility."""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from core.black_scholes import BlackScholes

BS = BlackScholes(100, 100, 0.5, 0.05, 0.20)


def test_benchmark_call_price():
    assert abs(BS.call_price() - 6.8887) < 1e-3


def test_benchmark_put_price():
    assert abs(BS.put_price() - 4.4197) < 1e-3


def test_put_call_parity():
    assert BS.verify_put_call_parity()["error"] < 1e-10


def test_price_wrapper_and_invalid_type():
    assert BS.price("call").price == BS.call_price()
    assert BS.price("put").price == BS.put_price()
    with pytest.raises(ValueError):
        BS.price("straddle")


def test_deep_itm_call_approaches_forward_intrinsic():
    b = BlackScholes(100, 1, 0.5, 0.05, 0.20)
    intrinsic = 100 - 1 * math.exp(-0.05 * 0.5)
    assert abs(b.call_price() - intrinsic) < 1e-6


def test_deep_otm_call_near_zero():
    assert BlackScholes(100, 300, 0.25, 0.05, 0.20).call_price() < 1e-6


@pytest.mark.parametrize("sigma_true", [0.10, 0.20, 0.45])
@pytest.mark.parametrize("K", [80, 100, 120])
def test_implied_vol_round_trip(K, sigma_true):
    price = BlackScholes(100, K, 0.5, 0.05, sigma_true).call_price()
    iv = BlackScholes.implied_volatility(price, 100, K, 0.5, 0.05, "call")
    assert abs(iv - sigma_true) < 1e-6


def test_implied_vol_put_round_trip():
    price = BlackScholes(100, 100, 0.5, 0.05, 0.30).put_price()
    iv = BlackScholes.implied_volatility(price, 100, 100, 0.5, 0.05, "put")
    assert abs(iv - 0.30) < 1e-6
