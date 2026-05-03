"""
Option payoff diagrams at expiry and at current time (with time value).
Covers calls, puts, and common multi-leg strategies.
"""

import numpy as np
import matplotlib.pyplot as plt
from core.black_scholes import BlackScholes


def plot_payoff_diagram(
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    premium: float | None = None,
    q: float = 0.0,
    spot_range: tuple[float, float] | None = None,
    save_path: str | None = None,
) -> None:
    """
    Plot payoff at expiry (intrinsic) vs current BS value (with time value).

    Shows:
      - Payoff at expiry (kinked hockey-stick)
      - Current BS price curve (smooth, above payoff)
      - Breakeven point
      - Time value shaded region
    """
    S0 = K  # reference spot = ATM
    if spot_range is None:
        spot_range = (0.5 * K, 1.6 * K)

    spots = np.linspace(spot_range[0], spot_range[1], 300)
    ot = option_type.lower()

    # Payoff at expiry (intrinsic value)
    if ot == "call":
        payoff = np.maximum(spots - K, 0)
    else:
        payoff = np.maximum(K - spots, 0)

    # Current BS price across spot range
    bs_prices = []
    for S in spots:
        try:
            bs = BlackScholes(float(S), K, T, r, sigma, q)
            bs_prices.append(bs.call_price() if ot == "call" else bs.put_price())
        except ValueError:
            bs_prices.append(float("nan"))
    bs_prices = np.array(bs_prices)

    # Premium (cost to enter position)
    if premium is None:
        bs_ref = BlackScholes(S0, K, T, r, sigma, q)
        premium = bs_ref.call_price() if ot == "call" else bs_ref.put_price()

    # P&L at expiry (payoff - premium)
    pnl = payoff - premium

    fig, ax = plt.subplots(figsize=(11, 7))

    # Shaded time value region
    ax.fill_between(spots, payoff, bs_prices, alpha=0.15, color="#2196F3", label="Time Value")

    # Lines
    ax.plot(spots, payoff,    color="#FF5722", linewidth=2.5, linestyle="--", label="Payoff at Expiry")
    ax.plot(spots, bs_prices, color="#2196F3", linewidth=2.5, label=f"BS Price (T={T}y)")
    ax.plot(spots, pnl,       color="#4CAF50", linewidth=2.0, linestyle="-.", label="P&L at Expiry")

    # Reference lines
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    ax.axvline(K, color="black", linewidth=1.2, linestyle=":", alpha=0.7, label=f"Strike K={K}")
    ax.axhline(-premium, color="gray", linewidth=1, linestyle=":", alpha=0.6, label=f"Premium={premium:.2f}")

    # Breakeven
    if ot == "call":
        breakeven = K + premium
    else:
        breakeven = K - premium
    ax.axvline(breakeven, color="#FF9800", linewidth=1.5, linestyle="--", alpha=0.8,
               label=f"Breakeven={breakeven:.2f}")

    ax.set_xlabel("Spot Price at Expiry", fontsize=12)
    ax.set_ylabel("Value / P&L ($)", fontsize=12)
    ax.set_title(
        f"{'Call' if ot=='call' else 'Put'} Option Payoff & BS Value\n"
        f"K={K} | T={T}y | σ={sigma:.0%} | r={r:.1%} | Premium={premium:.4f}",
        fontsize=13, fontweight="bold",
    )
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
