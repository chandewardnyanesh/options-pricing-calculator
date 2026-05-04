"""
Black-Scholes Option Pricing Model — implemented from scratch.

Assumptions (standard GBM framework):
  - Constant volatility and risk-free rate
  - European-style exercise only
  - No dividends (continuous dividend yield q can be added via cost-of-carry)
  - No transaction costs or taxes
  - Continuous trading

Formulae:
  d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)
  d2 = d1 - σ√T

  Call = S·Φ(d1) - K·e^(-rT)·Φ(d2)
  Put  = K·e^(-rT)·Φ(-d2) - S·Φ(-d1)
"""

import math
from dataclasses import dataclass
from .utils import normal_cdf, validate_inputs


@dataclass
class BSResult:
    """Container for a Black-Scholes pricing result."""
    option_type: str   # 'call' or 'put'
    price: float
    d1: float
    d2: float
    S: float
    K: float
    T: float
    r: float
    sigma: float

    def __repr__(self) -> str:
        return (
            f"BSResult({self.option_type.upper()} | "
            f"Price={self.price:.4f} | d1={self.d1:.4f} | d2={self.d2:.4f})"
        )


class BlackScholes:
    """
    Black-Scholes pricing engine for European options.

    Parameters
    ----------
    S     : float  Current spot price of the underlying
    K     : float  Strike price
    T     : float  Time to expiration in years (e.g. 0.5 = 6 months)
    r     : float  Annualised risk-free interest rate (decimal, e.g. 0.05 = 5%)
    sigma : float  Annualised volatility of the underlying (decimal, e.g. 0.2 = 20%)
    q     : float  Continuous dividend yield (default 0.0)
    """

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0.0,
    ) -> None:
        validate_inputs(S, K, T, r, sigma)
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.q = q          # continuous dividend yield

        # Pre-compute shared quantities used by price AND greeks
        self._sqrt_T = math.sqrt(T)
        self._d1, self._d2 = self._compute_d1_d2()

    # ------------------------------------------------------------------
    # Core computations
    # ------------------------------------------------------------------

    def _compute_d1_d2(self) -> tuple[float, float]:
        """Compute d1 and d2 — the standardised log-moneyness terms."""
        numerator = math.log(self.S / self.K) + (self.r - self.q + 0.5 * self.sigma ** 2) * self.T
        denominator = self.sigma * self._sqrt_T
        d1 = numerator / denominator
        d2 = d1 - self.sigma * self._sqrt_T
        return d1, d2

    @property
    def d1(self) -> float:
        return self._d1

    @property
    def d2(self) -> float:
        return self._d2

    # ------------------------------------------------------------------
    # Option prices
    # ------------------------------------------------------------------

    def call_price(self) -> float:
        """European call price via Black-Scholes.

        C = S·e^(-qT)·Φ(d1) - K·e^(-rT)·Φ(d2)
        """
        discount_S = self.S * math.exp(-self.q * self.T)
        discount_K = self.K * math.exp(-self.r * self.T)
        return discount_S * normal_cdf(self._d1) - discount_K * normal_cdf(self._d2)

    def put_price(self) -> float:
        """European put price via Black-Scholes.

        P = K·e^(-rT)·Φ(-d2) - S·e^(-qT)·Φ(-d1)
        """
        discount_S = self.S * math.exp(-self.q * self.T)
        discount_K = self.K * math.exp(-self.r * self.T)
        return discount_K * normal_cdf(-self._d2) - discount_S * normal_cdf(-self._d1)

    def price(self, option_type: str = "call") -> BSResult:
        """Return a BSResult for 'call' or 'put'."""
        ot = option_type.lower()
        if ot not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")
        px = self.call_price() if ot == "call" else self.put_price()
        return BSResult(
            option_type=ot,
            price=px,
            d1=self._d1,
            d2=self._d2,
            S=self.S, K=self.K, T=self.T, r=self.r, sigma=self.sigma,
        )

    # ------------------------------------------------------------------
    # Put-Call Parity verification
    # ------------------------------------------------------------------

    def verify_put_call_parity(self) -> dict:
        """
        Verify: C - P = S·e^(-qT) - K·e^(-rT)
        Returns both sides and the absolute error.
        """
        C = self.call_price()
        P = self.put_price()
        lhs = C - P
        rhs = self.S * math.exp(-self.q * self.T) - self.K * math.exp(-self.r * self.T)
        return {"lhs (C-P)": lhs, "rhs (S-PV(K))": rhs, "error": abs(lhs - rhs)}

    # ------------------------------------------------------------------
    # Implied Volatility (Newton-Raphson)
    # ------------------------------------------------------------------

    @staticmethod
    def implied_volatility(
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = "call",
        tol: float = 1e-8,
        max_iter: int = 200,
    ) -> float:
        """
        Recover implied volatility from a market price using Newton-Raphson.

        Converges in ~5 iterations for most liquid strikes.
        Returns float('nan') if it fails to converge.
        """
        sigma = 0.2  # initial guess
        for _ in range(max_iter):
            bs = BlackScholes(S, K, T, r, sigma)
            price = bs.call_price() if option_type == "call" else bs.put_price()
            # Newton denominator must be raw dPrice/dSigma; vega() reports per 1% vol
            vega = bs.vega() * 100.0
            diff = price - market_price
            if abs(diff) < tol:
                return sigma
            if abs(vega) < 1e-12:
                break
            sigma -= diff / vega
            if sigma <= 0:
                sigma = 1e-6  # keep sigma positive
        return float("nan")

    # ------------------------------------------------------------------
    # Convenience: delegate to Greeks
    # ------------------------------------------------------------------

    def _greeks(self):
        from .greeks import Greeks
        return Greeks(self.S, self.K, self.T, self.r, self.sigma, self.q)

    def delta(self, option_type: str = "call") -> float:
        return self._greeks().delta(option_type)

    def gamma(self) -> float:
        return self._greeks().gamma()

    def theta(self, option_type: str = "call") -> float:
        return self._greeks().theta(option_type)

    def vega(self) -> float:
        return self._greeks().vega()

    def rho(self, option_type: str = "call") -> float:
        return self._greeks().rho(option_type)

    def all_greeks(self, option_type: str = "call") -> dict:
        return self._greeks().all_greeks(option_type)

    def __repr__(self) -> str:
        return (
            f"BlackScholes(S={self.S}, K={self.K}, T={self.T}, "
            f"r={self.r}, σ={self.sigma}, q={self.q})"
        )
