"""
Black-Scholes vs Monte Carlo comparison utilities.

Provides a structured comparison table and convergence diagnostics,
showing how MC error falls as 1/√N toward the analytical BS price.
"""

from core.black_scholes import BlackScholes
from core.monte_carlo import MonteCarlo


class BSvsMC:
    """
    Side-by-side comparison of Black-Scholes and Monte Carlo pricing.

    Parameters
    ----------
    S, K, T, r, sigma, q : standard Black-Scholes parameters
    seed                  : random seed for reproducibility
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
        self.bs = BlackScholes(S, K, T, r, sigma, q)
        self.mc = MonteCarlo(S, K, T, r, sigma, q, seed)

    def compare(
        self,
        option_type: str = "call",
        n_simulations: int = 100_000,
    ) -> dict:
        """
        Run both pricers and return a structured comparison dict.

        Returns
        -------
        dict with keys: bs_price, mc_price, std_error,
                        abs_error, rel_error_pct, confidence_interval
        """
        bs_res = self.bs.price(option_type)
        mc_res = self.mc.price(option_type, n_simulations, bs_price=bs_res.price)

        return {
            "option_type":         option_type,
            "bs_price":            bs_res.price,
            "mc_price":            mc_res.price,
            "mc_std_error":        mc_res.std_error,
            "abs_error":           mc_res.abs_error,
            "rel_error_pct":       mc_res.rel_error_pct,
            "confidence_interval": mc_res.confidence_interval,
            "n_simulations":       mc_res.n_simulations,
            "bs_in_ci":            (
                mc_res.confidence_interval[0]
                <= bs_res.price
                <= mc_res.confidence_interval[1]
            ),
        }

    def convergence_table(
        self,
        option_type: str = "call",
        n_values: list[int] | None = None,
    ) -> list[dict]:
        """
        Show how MC price and error converge toward BS as N grows.

        Returns a list of rows suitable for printing or plotting.
        Each row: {n, mc_price, bs_price, abs_error, std_error, rel_error_pct}
        """
        bs_price = self.bs.call_price() if option_type == "call" else self.bs.put_price()
        rows = self.mc.convergence_study(option_type, n_values, bs_price=bs_price)
        for row in rows:
            row["bs_price"] = bs_price
            if row["abs_error"] is not None:
                row["rel_error_pct"] = row["abs_error"] / bs_price * 100.0
        return rows

    def print_convergence(
        self,
        option_type: str = "call",
        n_values: list[int] | None = None,
    ) -> None:
        """Pretty-print the convergence table to stdout."""
        rows = self.convergence_table(option_type, n_values)
        bs_px = rows[0]["bs_price"]
        print(f"\n{'BS vs Monte Carlo Convergence':^65}")
        print(f"  Option: {option_type.upper()}   BS Price: {bs_px:.4f}")
        print("-" * 65)
        print(f"{'N':>10}  {'MC Price':>10}  {'Abs Error':>10}  {'Std Error':>10}  {'Rel Err%':>8}")
        print("-" * 65)
        for r in rows:
            ae = r["abs_error"] or float("nan")
            se = r["std_error"]
            re = r.get("rel_error_pct") or float("nan")
            print(f"{r['n']:>10,}  {r['mc_price']:>10.4f}  {ae:>10.6f}  {se:>10.6f}  {re:>8.4f}%")
        print("-" * 65)
