# Options Pricing & Greeks Calculator

A European option pricing library built **from first principles** — no SciPy, no QuantLib. Black-Scholes closed forms, all eight Greeks, Monte Carlo simulation with variance reduction, and implied-volatility analytics, cross-validated against each other and backed by a 59-test suite.

Every formula is implemented by hand on top of the Python standard library (`math.erf` is the only "special function" used), so the entire pricing stack is transparent and auditable end to end.

## Highlights

- **Black-Scholes engine** — call/put pricing with continuous dividend yield, put-call parity verification (error ~1e-15), and implied-volatility recovery via Newton-Raphson with the exact vega derivative (quadratic convergence, ~5 iterations).
- **Eight Greeks** — Delta, Gamma, Theta, Vega, Rho plus second-order Charm, Vanna, Volga; every one validated against central finite differences of the pricing function.
- **Monte Carlo pricer** — exact GBM terminal-price sampling (no discretisation error for European payoffs), antithetic variates, standard errors with 95% confidence intervals, √N convergence studies, and arithmetic-average Asian options where no closed form exists.
- **Volatility analytics** — implied-vol smile, ATM term structure, full vol surface from price grids, and rolling close-to-close historical volatility.
- **Visualizations** — payoff diagrams with time value, Greeks vs spot/vol, Greek heatmaps over the (S, σ) grid, smile plots, and MC convergence charts.

## Architecture

Strictly layered — lower layers never import upper ones:

```
options_pricing/
├── main.py                  # End-to-end narrated demo (run this)
├── core/                    # Pure math — stdlib only
│   ├── utils.py             #   normal pdf/cdf, input validation
│   ├── black_scholes.py     #   pricing, parity, implied vol (Newton-Raphson)
│   ├── greeks.py            #   8 analytic Greeks
│   └── monte_carlo.py       #   GBM simulation, antithetic variates, Asian options
├── analytics/               # Composes core
│   ├── comparison.py        #   BS vs MC cross-validation + convergence tables
│   └── volatility.py        #   smile / term structure / surface, historical vol
├── visualizations/          # matplotlib charts (presentation only)
├── tests/                   # 59 tests
└── docs/                    # Per-module deep-dive documentation
```

## Quickstart

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py            # narrated end-to-end demo
.venv/bin/python -m pytest tests/   # full suite
```

Set `SHOW_PLOTS = True` in `main.py` to also render the charts. For fast iteration, skip the plot smoke tests (they run real Monte Carlo): `pytest tests/ --ignore=tests/test_visualizations.py` (~35 s).

## Documentation

| Module | Doc | Covers |
|---|---|---|
| Foundations | [PHASE1_foundations.md](docs/PHASE1_foundations.md) | Normal pdf/cdf from scratch, validation rules |
| Black-Scholes | [PHASE2_black_scholes.md](docs/PHASE2_black_scholes.md) | Pricing formulas, d₁/d₂, parity, Newton-Raphson IV |
| Greeks | [PHASE3_greeks.md](docs/PHASE3_greeks.md) | All 8 Greeks: formulas, intuition, unit conventions |
| Monte Carlo | [PHASE4_monte_carlo.md](docs/PHASE4_monte_carlo.md) | GBM, antithetic variates, √N convergence, Asian options |
| Analytics | [PHASE5_analytics.md](docs/PHASE5_analytics.md) | BS-vs-MC validation, vol surface construction, historical vol |
| Visualizations | [PHASE6_visualizations.md](docs/PHASE6_visualizations.md) | The six charts and how to read them |
| Integration | [PHASE7_integration.md](docs/PHASE7_integration.md) | main.py walkthrough with verified output |

## Conventions

Trader-desk units throughout: Theta and Charm are **per calendar day** (÷365); Vega, Rho, and Volga are **per 1% move** (÷100); Delta, Gamma, and Vanna are raw derivatives. The finite-difference tests apply the same scalings — a clean 100× or 365× discrepancy when validating Greeks is almost always a units mismatch, not a math error.

## Testing philosophy

Nothing is trusted until two independent methods agree:

- **Analytic vs textbook** — ATM 6-month option (S=K=100, r=5%, σ=20%): call **6.8887**, put **4.4197**; parity error at floating-point noise.
- **Analytic vs numeric** — every Greek checked against central finite differences (tolerances 1e-4 to 1e-6).
- **Simulation vs analytic** — seeded MC must land within 3 standard errors of the closed form at 200k paths; standard error must shrink as 1/√N.
- **Inversion round-trips** — prices generated at a known vol must recover that vol through the IV solver to 1e-6, across strikes and vol levels.

This caught two real defects during hardening: an implied-vol solver whose Newton step used the per-1% vega (100× too large, returning NaN away from the initial guess), and a `KeyError` in the convergence-table formatter. Both are fixed with regression tests in place.

## Roadmap

- Binomial/trinomial trees and American early exercise
- Barrier options via Brownian-bridge Monte Carlo
- Live option-chain ingestion and market IV surfaces

## License

MIT — see [LICENSE](LICENSE).
