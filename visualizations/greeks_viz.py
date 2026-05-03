"""
Visualizations for option Greeks.

Plots:
  1. All 5 Greeks vs spot price (S) — fixed vol and expiry
  2. All 5 Greeks vs implied vol  — fixed spot and expiry
  3. Greek surface (2D heatmap): Greek as f(S, σ)
"""

import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from core.greeks import Greeks


# ------------------------------------------------------------------
# 1. Greeks vs Spot Price
# ------------------------------------------------------------------

def plot_greeks_vs_spot(
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float = 0.0,
    option_type: str = "call",
    spot_range: tuple[float, float] | None = None,
    n_points: int = 200,
    save_path: str | None = None,
) -> None:
    """
    Plot all five Greeks as a function of spot price S.

    Useful for understanding how sensitivities shift as the option
    moves from deep OTM → ATM → deep ITM.
    """
    if spot_range is None:
        spot_range = (0.5 * K, 1.5 * K)

    spots = np.linspace(spot_range[0], spot_range[1], n_points)
    greek_names = ["delta", "gamma", "theta", "vega", "rho"]
    greek_data = {g: [] for g in greek_names}

    for S in spots:
        try:
            g = Greeks(float(S), K, T, r, sigma, q)
            greek_data["delta"].append(g.delta(option_type))
            greek_data["gamma"].append(g.gamma())
            greek_data["theta"].append(g.theta(option_type))
            greek_data["vega"].append(g.vega())
            greek_data["rho"].append(g.rho(option_type))
        except ValueError:
            for gn in greek_names:
                greek_data[gn].append(math.nan)

    colors = ["#2196F3", "#4CAF50", "#FF5722", "#9C27B0", "#FF9800"]
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    axes = axes.flatten()
    fig.suptitle(
        f"Option Greeks vs Spot Price\n"
        f"{option_type.upper()} | K={K} | T={T}y | r={r:.1%} | σ={sigma:.1%}",
        fontsize=14, fontweight="bold",
    )

    for idx, (gname, color) in enumerate(zip(greek_names, colors)):
        ax = axes[idx]
        ax.plot(spots, greek_data[gname], color=color, linewidth=2, label=gname.capitalize())
        ax.axvline(K, color="black", linestyle="--", alpha=0.5, label="Strike K")
        ax.axhline(0, color="gray", linestyle="-", alpha=0.3)
        ax.set_xlabel("Spot Price (S)", fontsize=10)
        ax.set_ylabel(gname.capitalize(), fontsize=10)
        ax.set_title(
            f"{'Δ' if gname=='delta' else 'Γ' if gname=='gamma' else 'Θ' if gname=='theta' else 'ν' if gname=='vega' else 'ρ'} "
            f"({gname.capitalize()})",
            fontsize=11,
        )
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    axes[-1].set_visible(False)  # hide unused subplot
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


# ------------------------------------------------------------------
# 2. Greeks vs Implied Volatility
# ------------------------------------------------------------------

def plot_greeks_vs_vol(
    S: float,
    K: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: str = "call",
    vol_range: tuple[float, float] = (0.05, 1.0),
    n_points: int = 200,
    save_path: str | None = None,
) -> None:
    """
    Plot all five Greeks as a function of implied volatility σ.

    Vega peaks ATM and falls toward zero at extremes.
    Gamma similarly peaks ATM.
    """
    vols = np.linspace(vol_range[0], vol_range[1], n_points)
    greek_names = ["delta", "gamma", "theta", "vega", "rho"]
    greek_data = {g: [] for g in greek_names}

    for sigma in vols:
        g = Greeks(S, K, T, r, float(sigma), q)
        greek_data["delta"].append(g.delta(option_type))
        greek_data["gamma"].append(g.gamma())
        greek_data["theta"].append(g.theta(option_type))
        greek_data["vega"].append(g.vega())
        greek_data["rho"].append(g.rho(option_type))

    colors = ["#2196F3", "#4CAF50", "#FF5722", "#9C27B0", "#FF9800"]
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    axes = axes.flatten()
    fig.suptitle(
        f"Option Greeks vs Implied Volatility\n"
        f"{option_type.upper()} | S={S} | K={K} | T={T}y | r={r:.1%}",
        fontsize=14, fontweight="bold",
    )

    for idx, (gname, color) in enumerate(zip(greek_names, colors)):
        ax = axes[idx]
        ax.plot(vols * 100, greek_data[gname], color=color, linewidth=2)
        ax.axhline(0, color="gray", linestyle="-", alpha=0.3)
        ax.set_xlabel("Implied Volatility (%)", fontsize=10)
        ax.set_ylabel(gname.capitalize(), fontsize=10)
        ax.set_title(gname.capitalize(), fontsize=11)
        ax.grid(True, alpha=0.3)

    axes[-1].set_visible(False)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


# ------------------------------------------------------------------
# 3. Greek Surface (2D heatmap): f(S, σ)
# ------------------------------------------------------------------

def plot_greek_surface(
    greek_name: str,
    K: float,
    T: float,
    r: float,
    q: float = 0.0,
    option_type: str = "call",
    spot_range: tuple[float, float] | None = None,
    vol_range: tuple[float, float] = (0.05, 0.80),
    n_points: int = 80,
    save_path: str | None = None,
) -> None:
    """
    2D heatmap of a single Greek over the (S, σ) grid.

    Useful for visualising how Gamma spikes around ATM at low vol,
    or how Theta accelerates near expiry for ATM options.
    """
    if spot_range is None:
        spot_range = (0.6 * K, 1.4 * K)

    spots = np.linspace(spot_range[0], spot_range[1], n_points)
    vols  = np.linspace(vol_range[0],  vol_range[1],  n_points)
    S_grid, V_grid = np.meshgrid(spots, vols)
    Z = np.zeros_like(S_grid)

    for i in range(n_points):
        for j in range(n_points):
            try:
                g = Greeks(float(S_grid[i, j]), K, T, r, float(V_grid[i, j]), q)
                val = getattr(g, greek_name)(option_type) if greek_name in ("delta", "theta", "rho") \
                      else getattr(g, greek_name)()
                Z[i, j] = val
            except Exception:
                Z[i, j] = math.nan

    fig, ax = plt.subplots(figsize=(10, 7))
    hm = ax.contourf(S_grid, V_grid * 100, Z, levels=40, cmap="RdYlGn")
    plt.colorbar(hm, ax=ax, label=greek_name.capitalize())
    ax.axvline(K, color="white", linestyle="--", linewidth=1.5, label="Strike K")
    ax.set_xlabel("Spot Price (S)", fontsize=12)
    ax.set_ylabel("Implied Volatility (%)", fontsize=12)
    ax.set_title(
        f"{greek_name.capitalize()} Surface ({option_type.upper()}) | K={K} | T={T}y",
        fontsize=13, fontweight="bold",
    )
    ax.legend()
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
