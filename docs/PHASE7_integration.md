# Phase 7 — Integration (`main.py`)

## Purpose

A single script that exercises every layer in sequence, printing a narrated walkthrough. Run with `SHOW_PLOTS = False` (the committed default) for a pure-terminal demo; flip to `True` to also generate the Phase 6 charts.

```
.venv/bin/python main.py
```

Standard parameters throughout: S=100, K=100 (ATM), T=0.5y, r=5%, σ=20%, q=0.

## Walkthrough with verified sample output

**1. Black-Scholes pricing** — d₁=0.247487, d₂=0.106066; **call $6.8887, put $4.4197** (matches the test benchmarks).

**2. Greeks** — call: Δ +0.5977, Γ +0.0274, Θ −0.0222/day, ν +0.2736/1%, ρ +0.2644/1%; put: Δ −0.4023, Θ −0.0089, ρ −0.2232 (Γ and ν identical to the call, as parity requires). Second-order: Charm +0.000262/day, Vanna −0.2052, Volga +0.0359.

**3. Put-call parity** — C−P = S−PV(K) = 2.46900880 on both sides; error 7.1e-15 (floating-point noise).

**4. Implied vol recovery** — feeds the BS call price back into Newton-Raphson; recovers σ = 0.200000 with 0 error. (Exercises the Phase 2 vega-scaling fix.)

**5. Monte Carlo (N=100,000 antithetic pairs)** — call 6.9066 ± 0.0219, 95% CI [6.8636, 6.9496] contains the BS 6.8887; put 4.4323 ± 0.0151, CI contains 4.4197. Relative errors <0.3%.

**6. Convergence table** — MC price/error vs N from 100 to 100,000. This section exposed the **second real bug** of the project: `MonteCarlo.convergence_study` emits rows keyed `"price"`, but `BSvsMC.print_convergence` (and its own docstring) expect `"mc_price"` — a `KeyError` crash. Fixed in `convergence_table` by renaming the key; regression-tested in `tests/test_analytics.py`.

**7. Asian option** — arithmetic-average Asian call = **3.9120** vs European 6.8887, confirming averaging reduces effective volatility.

**8. Visualizations** — skipped when `SHOW_PLOTS = False`.

## Final verification

- `python main.py` exits 0, full output as above.
- Full suite: **59 tests passing** across 6 test files (`pytest tests/`).
