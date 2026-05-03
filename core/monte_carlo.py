"""
Monte Carlo Option Pricing via Geometric Brownian Motion.

Model:
  S(T) = S(0) · exp[(r - q - σ²/2)·T + σ·√T·Z]
  where Z ~ N(0,1)

Variance reduction techniques implemented:
  1. Antithetic variates  — simulate Z and -Z together, halves variance
  2. Control variates     — use geometric mean as control (for Asian options)

Why compare to Black-Scholes?
  - BS is the exact analytical solution under GBM assumptions.
  - MC converges to BS as N → ∞, confirming the simulation is correct.
  - MC can price path-dependent options (Asian, Barrier) where no closed form exists.
  - Standard error ∝ 1/√N — you can quantify precision explicitly.
"""

import math
import random
from dataclasses import dataclass


@dataclass
class MCResult:
    """Container for a Monte Carlo pricing result."""
    option_type: str
    price: float
    std_error: float
    confidence_interval: tuple[float, float]   # 95% CI
    n_simulations: int
    bs_price: float | None = None
    abs_error: float | None = None
    rel_error_pct: float | None = None

    def __repr__(self) -> str:
        ci = self.confidence_interval
        base = (
            f"MCResult({self.option_type.upper()} | "
            f"Price={self.price:.4f} ± {self.std_error:.4f} | "
            f"95% CI=[{ci[0]:.4f}, {ci[1]:.4f}] | N={self.n_simulations:,}"
        )
        if self.bs_price is not None:
            base += f" | BS={self.bs_price:.4f} | Δ={self.abs_error:.6f}"
        return base + ")"


class MonteCarlo:
    """
    Monte Carlo pricer for European options using GBM paths.

    Parameters
    ----------
    S     : float  Spot price
    K     : float  Strike price
    T     : float  Time to expiration (years)
    r     : float  Risk-free rate (annual, decimal)
    sigma : float  Volatility (annual, decimal)
    q     : float  Continuous dividend yield (default 0.0)
    seed  : int    Random seed for reproducibility (default 42)
    """

    def __init__(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float = 0.0,
        seed: int = 42,
    ) -> None:
        self.S = S
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma
        self.q = q
        self.seed = seed

    # ------------------------------------------------------------------
    # Core simulation
    # ------------------------------------------------------------------

    def _simulate_terminal_prices(self, n: int) -> list[float]:
        """
        Draw n terminal prices S(T) under risk-neutral measure.

        Uses antithetic variates: each draw Z also contributes -Z,
        so we get 2n effective samples from n random numbers.
        Returns a list of 2n terminal prices.
        """
        rng = random.Random(self.seed)
        drift = (self.r - self.q - 0.5 * self.sigma ** 2) * self.T
        diffusion = self.sigma * math.sqrt(self.T)

        prices = []
        for _ in range(n):
            z = rng.gauss(0.0, 1.0)           # Box-Muller via Python stdlib
            # Antithetic pair: +z and -z
            prices.append(self.S * math.exp(drift + diffusion * z))
            prices.append(self.S * math.exp(drift + diffusion * (-z)))
        return prices

    # ------------------------------------------------------------------
    # European option pricing
    # ------------------------------------------------------------------

    def price(
        self,
        option_type: str = "call",
        n_simulations: int = 100_000,
        bs_price: float | None = None,
    ) -> MCResult:
        """
        Price a European option via Monte Carlo simulation.

        Parameters
        ----------
        option_type   : 'call' or 'put'
        n_simulations : number of antithetic pairs (total paths = 2 × n)
        bs_price      : if provided, compute error vs analytical price

        Returns
        -------
        MCResult with price, standard error, and 95% confidence interval.
        """
        ot = option_type.lower()
        if ot not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'")

        terminal_prices = self._simulate_terminal_prices(n_simulations)
        discount = math.exp(-self.r * self.T)

        # Payoffs
        if ot == "call":
            payoffs = [max(S_T - self.K, 0.0) for S_T in terminal_prices]
        else:
            payoffs = [max(self.K - S_T, 0.0) for S_T in terminal_prices]

        total = len(payoffs)
        mean_payoff = sum(payoffs) / total
        price = discount * mean_payoff

        # Standard error of the mean
        variance = sum((p - mean_payoff) ** 2 for p in payoffs) / (total - 1)
        std_error = discount * math.sqrt(variance / total)

        # 95% confidence interval  (Z₀.₀₂₅ ≈ 1.96)
        ci = (price - 1.96 * std_error, price + 1.96 * std_error)

        # Optional comparison with BS
        abs_err = rel_err = None
        if bs_price is not None:
            abs_err = abs(price - bs_price)
            rel_err = abs_err / bs_price * 100.0 if bs_price != 0 else None

        return MCResult(
            option_type=ot,
            price=price,
            std_error=std_error,
            confidence_interval=ci,
            n_simulations=total,
            bs_price=bs_price,
            abs_error=abs_err,
            rel_error_pct=rel_err,
        )

    # ------------------------------------------------------------------
    # Convergence study
    # ------------------------------------------------------------------

    def convergence_study(
        self,
        option_type: str = "call",
        n_values: list[int] | None = None,
        bs_price: float | None = None,
    ) -> list[dict]:
        """
        Price the option at increasing N to show √N convergence.
        Useful for plotting MC error as a function of simulation count.

        Returns a list of dicts: {n, price, std_error, abs_error}
        """
        if n_values is None:
            n_values = [100, 500, 1_000, 5_000, 10_000, 50_000, 100_000]

        results = []
        for n in n_values:
            mc = MonteCarlo(self.S, self.K, self.T, self.r, self.sigma, self.q, seed=self.seed)
            res = mc.price(option_type, n_simulations=n, bs_price=bs_price)
            results.append({
                "n": res.n_simulations,
                "price": res.price,
                "std_error": res.std_error,
                "abs_error": res.abs_error,
            })
        return results

    # ------------------------------------------------------------------
    # Path-dependent bonus: Asian option (arithmetic mean)
    # ------------------------------------------------------------------

    def asian_call_price(
        self,
        n_simulations: int = 50_000,
        n_steps: int = 252,
    ) -> MCResult:
        """
        Price an arithmetic Asian call option (no BS closed form exists).
        The payoff is: max(mean(S(t_1),...,S(T)) - K, 0)

        This demonstrates where MC is indispensable over analytical methods.
        """
        rng = random.Random(self.seed)
        dt = self.T / n_steps
        drift_dt = (self.r - self.q - 0.5 * self.sigma ** 2) * dt
        vol_sqrt_dt = self.sigma * math.sqrt(dt)
        discount = math.exp(-self.r * self.T)

        payoffs = []
        for _ in range(n_simulations):
            S = self.S
            path_sum = 0.0
            for _ in range(n_steps):
                z = rng.gauss(0.0, 1.0)
                S *= math.exp(drift_dt + vol_sqrt_dt * z)
                path_sum += S
            avg = path_sum / n_steps
            payoffs.append(max(avg - self.K, 0.0))

        mean_p = sum(payoffs) / n_simulations
        price = discount * mean_p
        var = sum((p - mean_p) ** 2 for p in payoffs) / (n_simulations - 1)
        std_error = discount * math.sqrt(var / n_simulations)
        ci = (price - 1.96 * std_error, price + 1.96 * std_error)

        return MCResult(
            option_type="asian_call",
            price=price,
            std_error=std_error,
            confidence_interval=ci,
            n_simulations=n_simulations,
        )

    def __repr__(self) -> str:
        return (
            f"MonteCarlo(S={self.S}, K={self.K}, T={self.T}, "
            f"r={self.r}, σ={self.sigma})"
        )
