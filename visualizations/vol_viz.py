"""
Volatility visualizations:
  - Vol smile across strikes
  - MC convergence vs Black-Scholes
"""

import numpy as np
import matplotlib.pyplot as plt
from analytics.comparison import BSvsMC


def plot_vol_smile(
    smile_data: dict[float, float],
    S: float,
    T: float,
    title: str = "Implied Volatility Smile",
    save_path: str | None = None,
) -> None:
    """
    Plot implied volatility as a function of strike (the vol smile).

    Parameters
    ----------
    smile_data : {strike: implied_vol}  (from VolatilityAnalytics.vol_smile)
    S          : current spot (draws ATM reference line)
    T          : expiry in years (for the title)
    """
    strikes = sorted(smile_data.keys())
    ivols = [smile_data[k] * 100 for k in strikes]  # convert to percent

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(strikes, ivols, "o-", color="#9C27B0", linewidth=2.5, markersize=6, label="Implied Vol")
    ax.axvline(S, color="#FF5722", linestyle="--", linewidth=1.5, label=f"Spot S={S}")
    ax.fill_between(strikes, ivols, min(ivols), alpha=0.08, color="#9C27B0")

    ax.set_xlabel("Strike (K)", fontsize=12)
    ax.set_ylabel("Implied Volatility (%)", fontsize=12)
    ax.set_title(f"{title}\nT={T}y | ATM Spot={S}", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_convergence(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    n_values: list[int] | None = None,
    save_path: str | None = None,
) -> None:
    """
    Plot MC convergence toward BS price as N increases.

    Shows:
      - MC price ± 1 std error vs N  (log scale x-axis)
      - BS analytical price as horizontal reference
      - MC error ∝ 1/√N theoretical line

    Demonstrates that MC is an unbiased estimator of the BS price.
    """
    if n_values is None:
        n_values = [100, 500, 1_000, 5_000, 10_000, 50_000, 100_000, 500_000]

    comp = BSvsMC(S, K, T, r, sigma)
    rows = comp.convergence_table(option_type, n_values)

    ns         = np.array([r["n"] for r in rows])
    mc_prices  = np.array([r["mc_price"] for r in rows])
    std_errors = np.array([r["std_error"] for r in rows])
    bs_price   = rows[0]["bs_price"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(
        f"Monte Carlo Convergence to Black-Scholes\n"
        f"{option_type.upper()} | S={S} | K={K} | T={T}y | σ={sigma:.1%} | r={r:.1%}",
        fontsize=13, fontweight="bold",
    )

    # --- Left: price convergence ---
    ax1.semilogx(ns, mc_prices, "o-", color="#2196F3", linewidth=2, markersize=6, label="MC Price")
    ax1.fill_between(
        ns,
        mc_prices - std_errors,
        mc_prices + std_errors,
        alpha=0.2, color="#2196F3", label="±1 Std Error",
    )
    ax1.axhline(bs_price, color="#FF5722", linewidth=2, linestyle="--", label=f"BS Price={bs_price:.4f}")
    ax1.set_xlabel("Number of Simulations (log scale)", fontsize=11)
    ax1.set_ylabel("Option Price ($)", fontsize=11)
    ax1.set_title("Price Convergence", fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # --- Right: error vs 1/√N ---
    abs_errors = np.array([r["abs_error"] or float("nan") for r in rows])
    theoretical = std_errors[0] * np.sqrt(ns[0]) / np.sqrt(ns)   # 1/√N scaling

    ax2.loglog(ns, abs_errors,    "s-", color="#4CAF50", linewidth=2, markersize=6, label="|MC - BS|")
    ax2.loglog(ns, theoretical,   "--", color="gray",    linewidth=1.5, label="1/√N reference")
    ax2.loglog(ns, std_errors,    "^-", color="#FF9800", linewidth=2, markersize=6, label="Std Error")
    ax2.set_xlabel("Number of Simulations (log scale)", fontsize=11)
    ax2.set_ylabel("Error (log scale)", fontsize=11)
    ax2.set_title("Error Decay (should follow 1/√N)", fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
