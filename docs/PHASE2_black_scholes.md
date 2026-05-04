# Phase 2 — Black-Scholes Engine (`core/black_scholes.py`)

## Purpose

The analytical heart of the project: closed-form European option pricing, put-call parity verification, and implied-volatility recovery. Class `BlackScholes(S, K, T, r, sigma, q=0)` validates inputs on construction and pre-computes d₁/d₂ once for reuse by prices and Greeks.

## The math

**d₁ and d₂** — standardised log-moneyness terms:

```
d₁ = [ln(S/K) + (r − q + σ²/2)·T] / (σ√T)
d₂ = d₁ − σ√T
```

Φ(d₂) is the risk-neutral probability the option expires in the money; Φ(d₁) additionally accounts for the conditional size of S when ITM.

**Prices** (with continuous dividend yield q):

```
C = S·e^(−qT)·Φ(d₁) − K·e^(−rT)·Φ(d₂)
P = K·e^(−rT)·Φ(−d₂) − S·e^(−qT)·Φ(−d₁)
```

**Put-call parity** — a model-free no-arbitrage identity:

```
C − P = S·e^(−qT) − K·e^(−rT)
```

`verify_put_call_parity()` returns both sides and the error; for this implementation the error is ~1e-15 (pure floating-point noise), which is strong evidence both pricing formulas are internally consistent.

**Implied volatility** — `implied_volatility(market_price, S, K, T, r, ...)` inverts the BS formula with Newton-Raphson:

```
σ_{n+1} = σ_n − (BS(σ_n) − market) / Vega(σ_n)
```

Vega is the exact derivative dPrice/dσ, so convergence is quadratic (~5 iterations for liquid strikes). Returns `nan` on non-convergence (e.g. price below intrinsic).

## Bug found and fixed in this phase

The Newton denominator originally used `Greeks.vega()`, which is **scaled per 1% vol move** (÷100). The Newton step was therefore 100× too large, and the solver returned `nan` for any true vol away from the 0.20 initial guess. The round-trip tests caught it immediately (7 failures). Fix: multiply by 100 to recover raw dPrice/dσ:

```python
# Newton denominator must be raw dPrice/dSigma; vega() reports per 1% vol
vega = bs.vega() * 100.0
```

After the fix all round-trips recover σ to <1e-6 across strikes 80/100/120 and vols 10%/20%/45%, calls and puts.

## Usage

```python
from core.black_scholes import BlackScholes

bs = BlackScholes(S=100, K=100, T=0.5, r=0.05, sigma=0.20)
bs.call_price()                 # 6.8887
bs.put_price()                  # 4.4197
bs.verify_put_call_parity()     # {'lhs (C-P)': ..., 'rhs (S-PV(K))': ..., 'error': ~1e-15}
BlackScholes.implied_volatility(6.8887, 100, 100, 0.5, 0.05)  # ≈ 0.20
```

## How it's tested (`tests/test_black_scholes.py` — 16 tests)

- Benchmark prices: ATM 6M call 6.8887 / put 4.4197 (tol 1e-3) — standard textbook values.
- Parity error < 1e-10.
- Limits: deep ITM call → S − K·e^(−rT) (forward intrinsic); deep OTM call → 0.
- IV round-trip: price at known σ, recover σ to 1e-6, parametrized over 3 strikes × 3 vols + put case.
- `price()` wrapper consistency and rejection of invalid option types.
