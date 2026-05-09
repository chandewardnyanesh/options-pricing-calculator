# Options Pricing & Greeks Calculator

European option pricing built **from scratch** — no scipy, no QuantLib. Black-Scholes closed forms, all eight Greeks, Monte Carlo simulation with variance reduction, implied-volatility analytics, and matplotlib visualizations, cross-validated against each other and a 59-test pytest suite.

## Architecture

```
options_pricing/
├── main.py                  # End-to-end demo (run this)
├── core/                    # Pure math — no deps on other layers
│   ├── utils.py             #   normal pdf/cdf (math.erf), input validation
│   ├── black_scholes.py     #   BS pricing, parity, implied vol (Newton-Raphson)
│   ├── greeks.py            #   Delta Gamma Theta Vega Rho + Charm Vanna Volga
│   └── monte_carlo.py       #   GBM simulation, antithetic variates, Asian options
├── analytics/               # Composes core
│   ├── comparison.py        #   BS vs MC cross-validation + convergence tables
│   └── volatility.py        #   vol smile / term structure / surface, historical vol
├── visualizations/          # matplotlib charts (presentation only)
├── tests/                   # 59 tests, benchmark + finite-difference validated
└── docs/                    # Per-phase documentation (below)
```

## Quickstart

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py          # narrated end-to-end demo
.venv/bin/python -m pytest tests/ # full suite
```

Set `SHOW_PLOTS = True` in `main.py` to also render the charts.

## Documentation by phase

| Phase | Doc | Covers |
|---|---|---|
| 1 | [PHASE1_foundations.md](docs/PHASE1_foundations.md) | Normal pdf/cdf from scratch, validation rules |
| 2 | [PHASE2_black_scholes.md](docs/PHASE2_black_scholes.md) | BS formulas, d₁/d₂, parity, Newton-Raphson IV |
| 3 | [PHASE3_greeks.md](docs/PHASE3_greeks.md) | All 8 Greeks: formulas, intuition, unit conventions |
| 4 | [PHASE4_monte_carlo.md](docs/PHASE4_monte_carlo.md) | GBM, antithetic variates, √N convergence, Asian options |
| 5 | [PHASE5_analytics.md](docs/PHASE5_analytics.md) | BS-vs-MC validation, vol surface construction, historical vol |
| 6 | [PHASE6_visualizations.md](docs/PHASE6_visualizations.md) | The six charts and how to read them |
| 7 | [PHASE7_integration.md](docs/PHASE7_integration.md) | main.py walkthrough with verified output |

## Conventions

Theta and Charm are **per calendar day** (÷365); Vega, Rho, and Volga are **per 1% move** (÷100); Delta, Gamma, Vanna are raw derivatives. Tests validate every Greek against central finite differences with these scalings.

## Bugs found & fixed during verification (2026-05-09)

1. **Implied vol always NaN** — Newton-Raphson divided by the per-1% `vega()`, making the step 100× too large. Fixed with raw dPrice/dσ (`core/black_scholes.py`).
2. **Convergence table crash** — `convergence_study` emitted key `"price"` while `print_convergence` expected `"mc_price"` (`KeyError`). Fixed in `BSvsMC.convergence_table` (`analytics/comparison.py`).

Both have regression tests.

## Benchmarks used by the test suite

ATM 6-month option, S=K=100, r=5%, σ=20%: call **6.8887**, put **4.4197**; parity error ~1e-15; MC within 3 standard errors of BS at 200k paths; flat-vol smile round-trips to 1e-6.
