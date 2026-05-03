# Phase 1 — Mathematical Foundations (`core/utils.py`)

## Purpose

The math kernel everything else builds on. Deliberately **zero-scipy**: only the Python standard library (`math`), so every formula in the project is transparent and auditable. Three functions:

| Function | What it does |
|---|---|
| `normal_pdf(x)` | Standard normal density φ(x) |
| `normal_cdf(x)` | Standard normal cumulative Φ(x) |
| `validate_inputs(S, K, T, r, sigma)` | Rejects nonsensical Black-Scholes inputs with descriptive errors |

## The math

**PDF** — the bell curve itself:

```
φ(x) = (1 / √(2π)) · e^(−x²/2)
```

Used by Gamma, Vega, Vanna, Volga and the Newton-Raphson implied-vol solver (Vega is the derivative in the Newton step).

**CDF** — probability that a standard normal draw lands below x:

```
Φ(x) = ½ · [1 + erf(x / √2)]
```

`math.erf` is part of the C standard library exposed by Python, accurate to ~15 significant digits — there is no precision penalty versus `scipy.stats.norm.cdf`. Φ(d₁) and Φ(d₂) are the heart of Black-Scholes: Φ(d₂) is the risk-neutral probability the option finishes in the money.

**Validation rules:**
- `S`, `K`, `T`, `sigma` must be strictly positive (an expired option, T=0, is intrinsic value — not a pricing problem).
- `r` may be **negative** — negative interest rates exist (EUR, JPY, CHF regimes), so it is intentionally unchecked.

## Design decisions

- Plain functions, not a class — these are stateless and pure.
- Validation raises `ValueError` with the offending value embedded, so errors surface at construction time of `BlackScholes`/`Greeks`, not deep inside a formula as a cryptic `math.log` domain error.

## Usage

```python
from core.utils import normal_pdf, normal_cdf, validate_inputs

normal_cdf(1.96)   # ≈ 0.975  (the classic 95% two-tailed z)
normal_pdf(0.0)    # ≈ 0.3989
validate_inputs(S=100, K=100, T=0.5, r=0.05, sigma=0.2)  # silent if OK
```

## How it's tested (`tests/test_utils.py` — 9 tests)

- φ(0) = 1/√(2π) exactly; symmetry φ(x) = φ(−x).
- Φ against known values: Φ(0)=0.5, Φ(±1.95996)≈0.975/0.025, Φ(1)≈0.84134 (tolerances 1e-6 to 1e-12).
- Complement identity Φ(x) + Φ(−x) = 1 to 1e-14.
- Validation rejects S≤0, K≤0, T≤0, σ≤0 (parametrized) and **accepts** negative r.

Run: `.venv/bin/python -m pytest tests/test_utils.py -v` → 9 passed.
