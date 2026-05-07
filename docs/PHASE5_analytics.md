# Phase 5 — Analytics Layer (`analytics/`)

## Purpose

Composes the core engines into higher-level analysis. Two modules:

- `comparison.py` (`BSvsMC`) — cross-validation of the two pricers.
- `volatility.py` (`VolatilityAnalytics`) — implied-vol structures and historical vol.

## BS vs MC (`BSvsMC`)

Black-Scholes is the **exact** solution under GBM; Monte Carlo simulates the same model. So BS serves as ground truth: `compare()` runs both and reports `abs_error`, `rel_error_pct`, and `bs_in_ci` — whether the analytical price falls inside the MC 95% confidence interval (it should ~95% of the time; with 100k antithetic pairs the interval is tight). `convergence_table()` shows the error and standard error shrinking as ~1/√N.

This pattern — analytic benchmark validates the simulator, simulator then extends to payoffs the analytics can't reach — is the standard quant workflow.

## Volatility analytics (`VolatilityAnalytics`)

All implied-vol tools invert market prices through the Phase 2 Newton-Raphson solver:

- **`vol_smile({K: price}, T)`** — IV across strikes at one expiry. Real equity markets show a *skew* (higher IV for low strikes — crash insurance premium); under pure BS the smile is flat.
- **`term_structure({T: atm_price})`** — ATM IV across expiries (K = S).
- **`vol_surface(strikes, expiries, price_matrix)`** — the full 2D grid, shape `[n_expiries][n_strikes]`.
- **`historical_vol(prices, window=21)`** — realised close-to-close vol: std of log returns over a rolling window, annualised by √252. Comparing implied vs historical vol is the classic "is optionality rich or cheap" question.
- **`log_moneyness`** — ln(K/S)/(σ√T) for comparing smiles across maturities.

## Usage

```python
from analytics.comparison import BSvsMC
from analytics.volatility import VolatilityAnalytics

cmp = BSvsMC(100, 100, 0.5, 0.05, 0.20, seed=42)
cmp.compare("call")                  # {'bs_price': 6.8887, 'mc_price': ..., 'bs_in_ci': True}
cmp.print_convergence("call")        # pretty table

va = VolatilityAnalytics(S=100, r=0.05)
va.vol_smile({90: 12.1, 100: 6.9, 110: 3.4}, T=0.5)   # {strike: IV}
VolatilityAnalytics.historical_vol(closes, window=21)   # annualised realised vol
```

## How it's tested (`tests/test_analytics.py` — 8 tests)

- `compare()` internal consistency (abs_error matches |bs−mc|) and BS inside the MC CI.
- Convergence table rows carry `bs_price` and `rel_error_pct`.
- **Round-trip recovery**: generate prices from BS at a known flat vol, run them through smile / term-structure / surface — recovered IVs must equal the input vol to 1e-6. (These tests depend on the Phase 2 IV fix; they were impossible before it.)
- Historical vol: zero for constant prices, positive and correct length for a noisy series, `ValueError` when the window exceeds the data.
