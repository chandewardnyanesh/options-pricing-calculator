"""
Analytic Greeks for European options under Black-Scholes.

All five Greeks are derived analytically from the BS closed-form,
NOT via finite differences.

Greek       Interpretation                       Units
---------   -----------------------------------  ----------------------
Delta (Δ)   dV/dS   — price sensitivity          dimensionless (0–1 call, -1–0 put)
Gamma (Γ)   d²V/dS² — convexity of delta         per unit of S
Theta (Θ)   dV/dT   — time decay per calendar day  $/day (reported /day)
Vega  (ν)   dV/dσ   — vol sensitivity            $ per 1% move in vol
Rho   (ρ)   dV/dr   — rate sensitivity           $ per 1% move in rates

Formulae (with continuous dividend yield q):
  d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
  d2 = d1 - σ√T

  Δ_call = e^(-qT) · Φ(d1)
  Δ_put  = -e^(-qT) · Φ(-d1)

  Γ = e^(-qT) · φ(d1) / (S · σ · √T)        [same for call and put]

  Θ_call = [-S·e^(-qT)·φ(d1)·σ/(2√T)
             - r·K·e^(-rT)·Φ(d2)
             + q·S·e^(-qT)·Φ(d1)] / 365
  Θ_put  = [-S·e^(-qT)·φ(d1)·σ/(2√T)
             + r·K·e^(-rT)·Φ(-d2)
             - q·S·e^(-qT)·Φ(-d1)] / 365

  ν = S·e^(-qT)·φ(d1)·√T / 100              [per 1% move in σ]

  ρ_call = K·T·e^(-rT)·Φ(d2)  / 100
  ρ_put  = -K·T·e^(-rT)·Φ(-d2) / 100
"""

import math
from .utils import normal_cdf, normal_pdf, validate_inputs


class Greeks:
    """
    Analytic Black-Scholes Greeks.

    Parameters
    ----------
    S, K, T, r, sigma : same as BlackScholes
    q                 : continuous dividend yield (default 0.0)
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
        self.q = q

        # Pre-compute shared quantities
        self._sqrt_T = math.sqrt(T)
        self._d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * self._sqrt_T)
        self._d2 = self._d1 - sigma * self._sqrt_T
        self._phi_d1 = normal_pdf(self._d1)           # standard normal PDF at d1
        self._Phi_d1 = normal_cdf(self._d1)           # standard normal CDF at d1
        self._Phi_d2 = normal_cdf(self._d2)
        self._eq_T = math.exp(-q * T)                  # e^(-qT)
        self._er_T = math.exp(-r * T)                  # e^(-rT)

    # ------------------------------------------------------------------
    # Delta — Δ = dV/dS
    # ------------------------------------------------------------------

    def delta(self, option_type: str = "call") -> float:
        """
        Rate of change of option price with respect to spot price.

        Call Δ ∈ (0, 1)  — approaches 1 deep ITM, 0 deep OTM
        Put  Δ ∈ (-1, 0) — approaches -1 deep ITM, 0 deep OTM

        Also approximates the risk-neutral probability of finishing ITM.
        """
        if option_type.lower() == "call":
            return self._eq_T * self._Phi_d1
        else:
            return -self._eq_T * normal_cdf(-self._d1)

    # ------------------------------------------------------------------
    # Gamma — Γ = d²V/dS²  (same for call and put by put-call parity)
    # ------------------------------------------------------------------

    def gamma(self) -> float:
        """
        Rate of change of delta with respect to spot.
        Measures convexity — high gamma = delta changes rapidly near the strike.
        Identical for calls and puts (put-call parity).

        Γ = e^(-qT) · φ(d1) / (S · σ · √T)
        """
        return self._eq_T * self._phi_d1 / (self.S * self.sigma * self._sqrt_T)

    # ------------------------------------------------------------------
    # Theta — Θ = dV/dt  (reported per calendar day)
    # ------------------------------------------------------------------

    def theta(self, option_type: str = "call") -> float:
        """
        Daily time decay — how much value the option loses per calendar day.
        Almost always negative (options bleed value as expiry approaches).

        Reported per calendar day (divide full formula by 365).
        """
        common = -self.S * self._eq_T * self._phi_d1 * self.sigma / (2.0 * self._sqrt_T)

        if option_type.lower() == "call":
            rate_term = -self.r * self.K * self._er_T * self._Phi_d2
            div_term  = self.q * self.S * self._eq_T * self._Phi_d1
        else:
            rate_term = self.r * self.K * self._er_T * normal_cdf(-self._d2)
            div_term  = -self.q * self.S * self._eq_T * normal_cdf(-self._d1)

        return (common + rate_term + div_term) / 365.0

    # ------------------------------------------------------------------
    # Vega — ν = dV/dσ  (reported per 1% move in vol)
    # ------------------------------------------------------------------

    def vega(self) -> float:
        """
        Sensitivity of option price to a 1% change in implied volatility.
        Identical for calls and puts (put-call parity).

        ν = S · e^(-qT) · φ(d1) · √T / 100
        """
        return self.S * self._eq_T * self._phi_d1 * self._sqrt_T / 100.0

    # ------------------------------------------------------------------
    # Rho — ρ = dV/dr  (reported per 1% move in rates)
    # ------------------------------------------------------------------

    def rho(self, option_type: str = "call") -> float:
        """
        Sensitivity of option price to a 1% change in the risk-free rate.

        Calls have positive rho (higher rates → higher call value).
        Puts  have negative rho (higher rates → lower put value).

        ρ_call = K · T · e^(-rT) · Φ(d2)  / 100
        ρ_put  = -K · T · e^(-rT) · Φ(-d2) / 100
        """
        base = self.K * self.T * self._er_T / 100.0
        if option_type.lower() == "call":
            return base * self._Phi_d2
        else:
            return -base * normal_cdf(-self._d2)

    # ------------------------------------------------------------------
    # Convenience: return all greeks at once
    # ------------------------------------------------------------------

    def all_greeks(self, option_type: str = "call") -> dict:
        """Return a dict of all five Greeks for the given option type."""
        return {
            "delta": self.delta(option_type),
            "gamma": self.gamma(),
            "theta": self.theta(option_type),
            "vega":  self.vega(),
            "rho":   self.rho(option_type),
        }

    # ------------------------------------------------------------------
    # Charm and Speed (second-order, bonus)
    # ------------------------------------------------------------------

    def charm(self, option_type: str = "call") -> float:
        """
        Charm = dΔ/dt  (delta decay per day).
        Also called delta bleed — how much delta shifts as time passes.

        Charm_call = e^(-qT) · [φ(d1) · (2(r-q)T - d2·σ·√T) / (2T·σ·√T)
                                 - q·Φ(d1)]
        """
        num = 2.0 * (self.r - self.q) * self.T - self._d2 * self.sigma * self._sqrt_T
        denom = 2.0 * self.T * self.sigma * self._sqrt_T
        if option_type.lower() == "call":
            return self._eq_T * (self._phi_d1 * num / denom - self.q * self._Phi_d1) / 365.0
        else:
            return self._eq_T * (self._phi_d1 * num / denom + self.q * normal_cdf(-self._d1)) / 365.0

    def vanna(self) -> float:
        """
        Vanna = dΔ/dσ = dν/dS.
        Cross-sensitivity between spot and vol — important for hedging.

        Vanna = -e^(-qT) · φ(d1) · d2 / σ
        """
        return -self._eq_T * self._phi_d1 * self._d2 / self.sigma

    def volga(self) -> float:
        """
        Volga / Vomma = d²V/dσ².
        Convexity of option price with respect to vol.

        Volga = Vega · d1 · d2 / σ
        """
        return self.vega() * self._d1 * self._d2 / self.sigma

    def __repr__(self) -> str:
        return (
            f"Greeks(S={self.S}, K={self.K}, T={self.T}, "
            f"r={self.r}, σ={self.sigma}, q={self.q})"
        )
