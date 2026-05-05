# Phase 3 — Greeks Engine (`core/greeks.py`)

## Purpose

Analytic sensitivities of the Black-Scholes price. Class `Greeks(S, K, T, r, sigma, q=0)` pre-computes d₁, d₂, φ(d₁), Φ(d₁), Φ(d₂) once; each Greek is then a one-line formula. `BlackScholes` delegates its `delta()/gamma()/...` convenience methods here.

## Units conventions (important!)

| Greek | Definition | Reported as |
|---|---|---|
| Delta | dV/dS | raw |
| Gamma | d²V/dS² | raw |
| Theta | −dV/dT | **per calendar day** (÷365) |
| Vega | dV/dσ | **per 1% vol move** (÷100) |
| Rho | dV/dr | **per 1% rate move** (÷100) |
| Charm | dΔ/dT | **per day** (÷365), sign = sensitivity to time-to-maturity |
| Vanna | dΔ/dσ = dVega/dS | raw |
| Volga | d²V/dσ² | **÷100** (built on the per-1% vega) |

These are trader-desk conventions ("theta of −0.02 means the option bleeds 2 cents a day"). Finite-difference tests must apply the same scaling — a 100× or 365× "error" is usually a units mismatch, not a math bug.

## The formulas (q-adjusted)

- **Delta**: call e^(−qT)Φ(d₁) ∈ (0,1); put −e^(−qT)Φ(−d₁) ∈ (−1,0). Also ≈ risk-neutral probability of finishing ITM, and the hedge ratio.
- **Gamma**: e^(−qT)φ(d₁)/(S σ√T). Convexity of value in spot; same for calls and puts; peaks ATM near expiry.
- **Theta**: −Sφ(d₁)σe^(−qT)/(2√T) − rKe^(−rT)Φ(d₂) + qSe^(−qT)Φ(d₁), ÷365. Time decay; the price a long-option holder pays for gamma.
- **Vega**: Se^(−qT)φ(d₁)√T ÷ 100. Same for calls and puts; peaks ATM, grows with √T.
- **Rho**: ±KTe^(−rT)Φ(±d₂) ÷ 100. Calls positive, puts negative.
- **Charm** (delta bleed), **Vanna** (spot-vol cross), **Volga** (vol convexity) — second-order Greeks used in vol-surface risk management.

## Convention findings from testing

1. **Volga** uses `self.vega()` internally, so it inherits the ÷100 scaling: it reports d²V/dσ²/100. Consistent with the vega convention, documented here rather than "fixed".
2. **Charm** returns +dΔ/dT per day — the sensitivity of delta to *time-to-maturity*. Many references define charm as delta decay per unit of *calendar time* (−dΔ/dT). Same magnitude, opposite sign. The test pins the implemented convention.

## Usage

```python
from core.greeks import Greeks

g = Greeks(S=100, K=100, T=0.5, r=0.05, sigma=0.20)
g.delta("call")   # 0.598
g.gamma()         # 0.0274
g.theta("call")   # -0.0180  (loses ~1.8 cents/day)
g.vega()          # 0.2742   (per 1% vol move)
g.all_greeks("put")  # dict of the five first-order Greeks
```

## How it's tested (`tests/test_greeks.py` — 13 tests)

Every Greek is validated against a **central finite difference** of the BS price (or of delta, for charm/vanna) with the convention scaling applied:

- delta/theta/rho for call and put, vega, gamma — tolerance 1e-5..1e-6.
- vanna, volga, charm — second-order, tolerance 1e-4..1e-5.
- Sign/sanity battery: call delta ∈ (0,1), put delta ∈ (−1,0), gamma>0, vega>0, theta(call)<0, rho call>0>put, `all_greeks` keys.
