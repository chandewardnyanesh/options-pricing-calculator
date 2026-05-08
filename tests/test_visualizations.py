"""Phase 6 smoke tests — every plot function runs headless without error."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import pytest

from visualizations.payoff_viz import plot_payoff_diagram
from visualizations.greeks_viz import plot_greeks_vs_spot, plot_greeks_vs_vol, plot_greek_surface
from visualizations.vol_viz import plot_vol_smile, plot_convergence


@pytest.fixture(autouse=True)
def no_show(monkeypatch):
    monkeypatch.setattr(plt, "show", lambda *a, **k: None)
    yield
    plt.close("all")


def test_payoff_diagram_runs():
    plot_payoff_diagram(K=100, T=0.5, r=0.05, sigma=0.2)
    plot_payoff_diagram(K=100, T=0.5, r=0.05, sigma=0.2, option_type="put", premium=4.42)


def test_greeks_vs_spot_runs():
    plot_greeks_vs_spot(K=100, T=0.5, r=0.05, sigma=0.2, n_points=40)


def test_greeks_vs_vol_runs():
    plot_greeks_vs_vol(S=100, K=100, T=0.5, r=0.05, n_points=40)


def test_greek_surface_runs():
    plot_greek_surface("gamma", K=100, T=0.5, r=0.05, n_points=20)


def test_vol_smile_runs():
    plot_vol_smile({90.0: 0.28, 100.0: 0.25, 110.0: 0.26}, S=100, T=0.5)


def test_convergence_plot_runs():
    plot_convergence(S=100, K=100, T=0.5, r=0.05, sigma=0.2, n_values=[100, 500, 1000])
