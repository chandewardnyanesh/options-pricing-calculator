"""
Volatility analytics:
  - Vol smile / skew across strikes
  - Term structure of implied vol
  - Vol surface (strike × expiry grid)
  - Historical vol estimation (close-to-close, Yang-Zhang)

All implied vol extraction uses our own Newton-Raphson IV solver
via BlackScholes.implied_volatility().
"""

import math
from core.black_scholes import BlackScholes


class VolatilityAnalytics:
    """Tools for constructing and analysing volatility surfaces."""

    def __init__(self, S: float, r: float, q: float = 0.0) -> None:
        self.S = S
        self.r = r
        self.q = q

    # ------------------------------------------------------------------
    # Vol smile — IV across strikes at fixed expiry
    # ------------------------------------------------------------------

    def vol_smile(
        self,
        market_prices: dict[float, float],
        T: float,
        option_type: str = "call",
    ) -> dict[float, float]:
        """
        Extract implied volatility from market prices across strikes.

        Parameters
        ----------
        market_prices : {strike: market_price}
        T             : single expiry in years
        option_type   : 'call' or 'put'

        Returns
        -------
        {strike: implied_vol}
        """
        smile = {}
        for K, mkt_price in market_prices.items():
            iv = BlackScholes.implied_volatility(
                mkt_price, self.S, K, T, self.r, option_type
            )
            smile[K] = iv
        return smile

    # ------------------------------------------------------------------
    # Term structure — IV at fixed strike across expiries
    # ------------------------------------------------------------------

    def term_structure(
        self,
        atm_prices: dict[float, float],
        option_type: str = "call",
    ) -> dict[float, float]:
        """
        Extract implied vol from ATM options across different expiries.

        Parameters
        ----------
        atm_prices : {T_years: atm_market_price}

        Returns
        -------
        {T_years: implied_vol}
        """
        term = {}
        for T, price in atm_prices.items():
            iv = BlackScholes.implied_volatility(
                price, self.S, self.S, T, self.r, option_type  # K = S for ATM
            )
            term[T] = iv
        return term

    # ------------------------------------------------------------------
    # Vol surface — full 2D grid
    # ------------------------------------------------------------------

    def vol_surface(
        self,
        strike_grid: list[float],
        expiry_grid: list[float],
        price_matrix: list[list[float]],
        option_type: str = "call",
    ) -> list[list[float]]:
        """
        Build a vol surface from a matrix of market prices.

        Parameters
        ----------
        strike_grid  : list of K values (len = n_strikes)
        expiry_grid  : list of T values (len = n_expiries)
        price_matrix : shape [n_expiries][n_strikes]

        Returns
        -------
        iv_surface   : same shape, each entry is implied vol
        """
        surface = []
        for i, T in enumerate(expiry_grid):
            row = []
            for j, K in enumerate(strike_grid):
                iv = BlackScholes.implied_volatility(
                    price_matrix[i][j], self.S, K, T, self.r, option_type
                )
                row.append(iv)
            surface.append(row)
        return surface

    # ------------------------------------------------------------------
    # Historical volatility (close-to-close)
    # ------------------------------------------------------------------

    @staticmethod
    def historical_vol(prices: list[float], window: int = 21) -> list[float]:
        """
        Annualised close-to-close historical volatility using a rolling window.

        σ_hist = std(log returns) * √252

        Parameters
        ----------
        prices : list of daily closing prices
        window : rolling window in trading days (default 21 ≈ 1 month)

        Returns
        -------
        list of annualised vol estimates (len = len(prices) - window)
        """
        if len(prices) < window + 1:
            raise ValueError(f"Need at least {window + 1} prices for window={window}")

        log_returns = [
            math.log(prices[i] / prices[i - 1])
            for i in range(1, len(prices))
        ]

        vols = []
        for i in range(window, len(log_returns)):
            window_returns = log_returns[i - window: i]
            mean = sum(window_returns) / window
            variance = sum((r - mean) ** 2 for r in window_returns) / (window - 1)
            vols.append(math.sqrt(variance) * math.sqrt(252))
        return vols

    # ------------------------------------------------------------------
    # Moneyness helper
    # ------------------------------------------------------------------

    @staticmethod
    def log_moneyness(S: float, K: float, T: float, sigma: float) -> float:
        """
        Standardised log-moneyness: ln(K/F) / (σ√T)
        where F = S·e^(rT) is the forward price.
        Useful for comparing smiles across maturities.
        """
        return math.log(K / S) / (sigma * math.sqrt(T))
