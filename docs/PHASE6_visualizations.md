# Phase 6 — Visualizations (`visualizations/`)

## Purpose

Matplotlib charts that turn the engines' numbers into intuition. Pure presentation layer — imports from `core`/`analytics`, never the other way round. Every function takes an optional `save_path` to write a PNG instead of (or as well as) showing a window.

## The charts

| Function | What it shows | How to read it |
|---|---|---|
| `plot_payoff_diagram(K, T, r, sigma, option_type, premium, ...)` | Hockey-stick payoff at expiry vs the smooth BS value today | The vertical gap between the curves is **time value**; the kink is the strike; breakeven marked where P&L crosses zero |
| `plot_greeks_vs_spot(K, T, r, sigma, ...)` | All five Greeks as spot sweeps 0.5K → 1.5K | Delta S-curve OTM→ITM; Gamma and Vega peak ATM; Theta most negative ATM |
| `plot_greeks_vs_vol(S, K, T, r, ...)` | Greeks as σ sweeps 5% → 100% | Shows how risk changes in a vol spike — e.g. delta drifts toward 0.5+ as vol rises |
| `plot_greek_surface(greek_name, K, T, r, ...)` | Heatmap of one Greek over the (S, σ) grid | Gamma spikes around ATM at low vol — the classic "pin risk" picture |
| `plot_vol_smile(smile_data, S, T)` | IV (%) vs strike, ATM line marked | Takes the dict from `VolatilityAnalytics.vol_smile`; skew/smile shape vs the flat BS assumption |
| `plot_convergence(S, K, T, r, sigma, n_values)` | MC price ± CI vs N, against the BS line | Error band shrinks ~1/√N; MC hugs BS as N grows |

## Generating them

```python
from visualizations.payoff_viz import plot_payoff_diagram
plot_payoff_diagram(K=100, T=0.5, r=0.05, sigma=0.2, premium=6.89,
                    save_path="payoff.png")
```

Or simply set `SHOW_PLOTS = True` in `main.py` and run it — section 8 of the demo generates the full set.

## How it's tested (`tests/test_visualizations.py` — 6 smoke tests)

Plot output isn't pixel-asserted (brittle, low value). Instead each function is executed headless:

- `matplotlib.use("Agg")` — no display required (CI-safe).
- `plt.show` monkeypatched to a no-op; `plt.close("all")` after each test to free figures.
- Each of the six plot functions is called once with standard parameters (reduced `n_points` to keep the suite fast); the test fails on any exception — catching API drift, bad imports, or formula errors inside the plotting math.
