# Phase 4 — Monte Carlo Engine (`core/monte_carlo.py`)

## Purpose

Simulation-based pricing under the same model assumptions as Black-Scholes. Two jobs:
1. **Validation** — MC must converge to the BS price as N→∞ (if it doesn't, the simulation is wrong).
2. **Capability** — MC prices path-dependent payoffs (Asian options here) where no closed form exists.

## The model

Geometric Brownian Motion under the risk-neutral measure; terminal price sampled directly (exact, no discretisation error for European payoffs):

```
S(T) = S(0) · exp[(r − q − σ²/2)·T + σ·√T·Z],   Z ~ N(0,1)
```

Price = e^(−rT) · mean(payoff). Standard error = e^(−rT)·std(payoff)/√N, 95% CI = price ± 1.96·SE.

## Variance reduction: antithetic variates

Each draw Z contributes two paths: +Z and −Z. The pair's payoffs are negatively correlated, so the mean of the pair has lower variance than two independent draws — and you get 2N paths from N random numbers. `n_simulations` counts *pairs*; `MCResult.n_simulations` reports total paths (2N), verified by test.

## Asian option (`asian_call_price`)

Arithmetic-average Asian call: payoff `max(mean(S(t₁)…S(T)) − K, 0)`, simulated with 252 steps/year (daily fixing). No BS closed form exists — this is where MC earns its keep. Averaging reduces the effective volatility of the payoff variable, so the Asian call is always **cheaper** than the European call with the same parameters (verified by test).

## Determinism

Constructor takes `seed` (default 42); every pricing call builds its own `random.Random(seed)`, so results are exactly reproducible — same seed, same price. This is what makes statistical tests stable in CI.

## Usage

```python
from core.monte_carlo import MonteCarlo

mc = MonteCarlo(S=100, K=100, T=0.5, r=0.05, sigma=0.20, seed=42)
res = mc.price("call", n_simulations=100_000, bs_price=6.8887)
res.price, res.std_error, res.confidence_interval   # MC estimate ± precision
mc.convergence_study("call", bs_price=6.8887)        # rows of (n, price, se, abs_error)
mc.asian_call_price(n_simulations=50_000)            # path-dependent pricing
```

## How it's tested (`tests/test_monte_carlo.py` — 7 tests)

- **Statistical correctness**: with 200k paths, |MC − BS| < 3·SE for both call and put (a ~99.7% confidence bound — fails only if the estimator is biased or the SE is wrong).
- **Antithetic accounting**: 100k pairs → 200k reported paths.
- **Determinism**: identical seed → bit-identical price.
- **√N convergence**: SE at 100k pairs is >5× smaller than at 1k pairs; convergence-study rows shrink monotonically.
- **Asian < European** and rejection of invalid option types.
