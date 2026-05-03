"""
Options Pricing & Greeks Calculator — End-to-End Demo
=====================================================

Run:  python main.py

Demonstrates:
  1. Black-Scholes pricing (call + put), no built-in functions
  2. All five analytic Greeks with interpretation
  3. Put-call parity verification
  4. Implied volatility recovery via Newton-Raphson
  5. Monte Carlo pricing with antithetic variates + convergence
  6. BS vs MC comparison table
  7. Asian option pricing (no closed form — MC only)
  8. Visualizations (toggle SHOW_PLOTS=True to enable)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.black_scholes import BlackScholes
from core.greeks import Greeks
from core.monte_carlo import MonteCarlo
from analytics.comparison import BSvsMC

SHOW_PLOTS = True   # set False to skip matplotlib output

# ====================================================================
# Parameters
# ====================================================================
S     = 100.0   # spot price
K     = 100.0   # strike (ATM)
T     = 0.5     # 6 months
r     = 0.05    # 5% risk-free rate
sigma = 0.20    # 20% implied vol
q     = 0.0     # no dividends


def separator(title: str = "") -> None:
    line = "=" * 60
    print(f"\n{line}")
    if title:
        print(f"  {title}")
        print(line)


# ====================================================================
# 1. Black-Scholes Pricing
# ====================================================================
separator("1. Black-Scholes Pricing (from scratch)")

bs = BlackScholes(S, K, T, r, sigma, q)
call_result = bs.price("call")
put_result  = bs.price("put")

print(f"  Parameters: S={S} | K={K} | T={T}y | r={r:.0%} | σ={sigma:.0%}")
print(f"\n  d1 = {bs.d1:.6f}")
print(f"  d2 = {bs.d2:.6f}")
print(f"\n  CALL Price = ${call_result.price:.4f}")
print(f"  PUT  Price = ${put_result.price:.4f}")


# ====================================================================
# 2. Five Greeks
# ====================================================================
separator("2. All Five Greeks (analytic)")

g = Greeks(S, K, T, r, sigma, q)

for ot in ("call", "put"):
    all_g = g.all_greeks(ot)
    print(f"\n  {ot.upper()}:")
    print(f"    Δ Delta  = {all_g['delta']:+.6f}   (dV/dS — $ per $1 move in spot)")
    print(f"    Γ Gamma  = {all_g['gamma']:+.6f}   (dΔ/dS — how fast delta changes)")
    print(f"    Θ Theta  = {all_g['theta']:+.6f}   (dV/dt — $ lost per calendar day)")
    print(f"    ν Vega   = {all_g['vega']:+.6f}   (dV/dσ — $ per 1% vol move)")
    print(f"    ρ Rho    = {all_g['rho']:+.6f}   (dV/dr — $ per 1% rate move)")

print(f"\n  Bonus Greeks (2nd order):")
print(f"    Charm (dΔ/dt) call  = {g.charm('call'):+.6f}  /day")
print(f"    Vanna (dΔ/dσ)       = {g.vanna():+.6f}")
print(f"    Volga (d²V/dσ²)     = {g.volga():+.6f}")


# ====================================================================
# 3. Put-Call Parity
# ====================================================================
separator("3. Put-Call Parity Verification")

parity = bs.verify_put_call_parity()
print(f"  C - P                = {parity['lhs (C-P)']:.8f}")
print(f"  S - PV(K) = S·e^-qT - K·e^-rT = {parity['rhs (S-PV(K))']:.8f}")
print(f"  Error                = {parity['error']:.2e}  ✓" if parity['error'] < 1e-10 else "  ✗ PARITY VIOLATED")


# ====================================================================
# 4. Implied Volatility Recovery
# ====================================================================
separator("4. Implied Volatility Recovery (Newton-Raphson)")

market_call_price = call_result.price   # pretend this is the market price
iv = BlackScholes.implied_volatility(market_call_price, S, K, T, r, "call")
print(f"  Input BS call price = {market_call_price:.6f}")
print(f"  Recovered IV        = {iv:.6f}  (true σ = {sigma:.6f})")
print(f"  Error               = {abs(iv - sigma):.2e}")


# ====================================================================
# 5. Monte Carlo Pricing
# ====================================================================
separator("5. Monte Carlo Pricing (antithetic variates, N=100,000)")

mc = MonteCarlo(S, K, T, r, sigma, q, seed=42)
mc_call = mc.price("call", n_simulations=100_000, bs_price=call_result.price)
mc_put  = mc.price("put",  n_simulations=100_000, bs_price=put_result.price)

print(f"\n  CALL:")
print(f"    MC Price    = {mc_call.price:.4f}  (BS = {call_result.price:.4f})")
print(f"    Std Error   = {mc_call.std_error:.4f}")
print(f"    95% CI      = [{mc_call.confidence_interval[0]:.4f}, {mc_call.confidence_interval[1]:.4f}]")
print(f"    |MC - BS|   = {mc_call.abs_error:.6f}  ({mc_call.rel_error_pct:.3f}%)")

print(f"\n  PUT:")
print(f"    MC Price    = {mc_put.price:.4f}  (BS = {put_result.price:.4f})")
print(f"    Std Error   = {mc_put.std_error:.4f}")
print(f"    95% CI      = [{mc_put.confidence_interval[0]:.4f}, {mc_put.confidence_interval[1]:.4f}]")
print(f"    |MC - BS|   = {mc_put.abs_error:.6f}  ({mc_put.rel_error_pct:.3f}%)")


# ====================================================================
# 6. Convergence Table
# ====================================================================
separator("6. BS vs MC Convergence (call)")

comp = BSvsMC(S, K, T, r, sigma)
comp.print_convergence("call")


# ====================================================================
# 7. Asian Option (MC only — no closed form)
# ====================================================================
separator("7. Asian Call Option (arithmetic mean — MC only)")

asian = mc.asian_call_price(n_simulations=50_000, n_steps=252)
print(f"  Asian Call Price = {asian.price:.4f}")
print(f"  Std Error        = {asian.std_error:.4f}")
print(f"  95% CI           = [{asian.confidence_interval[0]:.4f}, {asian.confidence_interval[1]:.4f}]")
print(f"  European BS Call = {call_result.price:.4f}  (Asian < European — averaging reduces vol)")


# ====================================================================
# 8. Visualizations
# ====================================================================
if SHOW_PLOTS:
    separator("8. Generating Plots ...")
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from visualizations.greeks_viz import plot_greeks_vs_spot, plot_greek_surface
    from visualizations.payoff_viz import plot_payoff_diagram
    from visualizations.vol_viz import plot_convergence

    print("  Plotting Greeks vs Spot ...")
    plot_greeks_vs_spot(K=K, T=T, r=r, sigma=sigma, option_type="call")

    print("  Plotting Payoff Diagram ...")
    plot_payoff_diagram(K=K, T=T, r=r, sigma=sigma, option_type="call")

    print("  Plotting Gamma Surface ...")
    plot_greek_surface("gamma", K=K, T=T, r=r, option_type="call")

    print("  Plotting MC Convergence ...")
    plot_convergence(S=S, K=K, T=T, r=r, sigma=sigma, option_type="call")

separator("Done")
print()
