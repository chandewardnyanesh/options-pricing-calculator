"""
Mathematical utilities implemented from scratch.
No scipy or statsmodels — only the Python standard library.
"""

import math


def normal_pdf(x: float) -> float:
    """Standard normal probability density function.

    φ(x) = (1 / √(2π)) * exp(-x²/2)
    """
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function.

    Φ(x) = (1/2) * [1 + erf(x / √2)]

    Uses math.erf which is part of the Python standard library.
    Accurate to ~15 significant digits.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def validate_inputs(S: float, K: float, T: float, r: float, sigma: float) -> None:
    """Sanity-check Black-Scholes inputs and raise descriptive errors."""
    if S <= 0:
        raise ValueError(f"Spot price S must be positive, got {S}")
    if K <= 0:
        raise ValueError(f"Strike K must be positive, got {K}")
    if T <= 0:
        raise ValueError(f"Time to expiry T must be positive (in years), got {T}")
    if sigma <= 0:
        raise ValueError(f"Volatility sigma must be positive, got {sigma}")
    # r can be negative (negative rates exist), so no check there
