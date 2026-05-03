"""Phase 1 tests — mathematical foundations (core/utils.py)."""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from core.utils import normal_pdf, normal_cdf, validate_inputs


def test_normal_pdf_at_zero():
    assert abs(normal_pdf(0.0) - 1.0 / math.sqrt(2 * math.pi)) < 1e-12


def test_normal_pdf_symmetry():
    assert abs(normal_pdf(1.3) - normal_pdf(-1.3)) < 1e-15


def test_normal_cdf_known_values():
    assert abs(normal_cdf(0.0) - 0.5) < 1e-12
    assert abs(normal_cdf(1.959963985) - 0.975) < 1e-6
    assert abs(normal_cdf(-1.959963985) - 0.025) < 1e-6
    assert abs(normal_cdf(1.0) - 0.8413447461) < 1e-9


def test_normal_cdf_complement():
    for x in (0.3, 1.0, 2.5):
        assert abs(normal_cdf(x) + normal_cdf(-x) - 1.0) < 1e-14


@pytest.mark.parametrize("bad", [
    dict(S=-1, K=100, T=0.5, r=0.05, sigma=0.2),
    dict(S=100, K=0, T=0.5, r=0.05, sigma=0.2),
    dict(S=100, K=100, T=0.0, r=0.05, sigma=0.2),
    dict(S=100, K=100, T=0.5, r=0.05, sigma=-0.2),
])
def test_validate_inputs_rejects(bad):
    with pytest.raises(ValueError):
        validate_inputs(**bad)


def test_validate_inputs_allows_negative_rate():
    validate_inputs(S=100, K=100, T=0.5, r=-0.01, sigma=0.2)  # must not raise
