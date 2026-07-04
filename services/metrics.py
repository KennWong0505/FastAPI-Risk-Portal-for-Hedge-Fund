import numpy as np
import pandas as pd
from scipy.stats import norm

def compute_portfolio_returns(
    log_returns: pd.DataFrame,
    weights: list[float]
) -> pd.Series:
    """Computes weighted portfolio returns from individual asset log returns."""
    return log_returns.dot(np.array(weights))

def historical_var(portfolio_returns: pd.Series, confidence_level: float) -> float:
    """Computes Historical Simulation VaR. VaR expressed as return (negative = loss)."""
    return float(np.quantile(portfolio_returns, 1 - confidence_level))

def historical_es(portfolio_returns: pd.Series, confidence_level: float) -> float:
    """Computes Expected Shortfall (CVaR) from historical returns."""
    var = historical_var(portfolio_returns, confidence_level)
    es = float(portfolio_returns[portfolio_returns <= var].mean())
    return es

def variance_covariance_var(
    log_returns: pd.DataFrame,
    weights: list[float],
    confidence_level: float
) -> float:
    """Computes Variance-Covariance (parametric) VaR assuming normality."""
    portfolio_returns = compute_portfolio_returns(log_returns, weights)
    mean_p = float(portfolio_returns.mean())
    vcov_matrix = log_returns.cov()
    weights_arr = np.array(weights)
    sigma_p = np.sqrt(weights_arr @ vcov_matrix @ weights_arr)
    z = norm.ppf(confidence_level)
    return float(mean_p - z * sigma_p)

def monte_carlo_var(
    log_returns: pd.DataFrame,
    weights: list[float],
    confidence_level: float,
    n_simulations: int = 10_000
) -> float:
    """Computes Monte Carlo VaR using correlated multivariate normal simulations."""
    cov = log_returns.cov()
    mean = log_returns.mean()
    simulated_returns = np.random.multivariate_normal(mean, cov, size=n_simulations)
    simulated_portfolio_returns = simulated_returns @ np.array(weights)
    var = np.quantile(simulated_portfolio_returns, 1 - confidence_level)
    return float(var)

def annualised_volatility(portfolio_returns: pd.Series) -> float:
    """Annualised portfolio volatility (252 trading days)."""
    return float(portfolio_returns.std() * np.sqrt(252))

def sharpe_ratio(portfolio_returns: pd.Series, risk_free_rate: float = 0.04) -> float:
    """Annualised Sharpe ratio. Default risk-free rate: HK 3-month HIBOR ~4%."""
    annualised_return = float(portfolio_returns.mean() * 252)
    annualised_vol = annualised_volatility(portfolio_returns)
    return float((annualised_return - risk_free_rate) / annualised_vol)

def max_drawdown(portfolio_returns: pd.Series) -> float:
    """Maximum peak-to-trough decline in cumulative returns."""
    cumulative_returns = (1 + portfolio_returns).cumprod()
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    return float(drawdown.min())