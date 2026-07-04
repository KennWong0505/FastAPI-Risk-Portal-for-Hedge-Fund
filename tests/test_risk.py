import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError
from yfinance import data
from models.schemas import PortfolioRequest
from services.metrics import (
    compute_portfolio_returns, historical_var, historical_es,
    annualised_volatility, sharpe_ratio, max_drawdown
)
from fastapi.testclient import TestClient
from main import app

# Unit tests with known inputs
def test_historical_var_known_input():
    # If returns are [-0.05, -0.04, -0.03, ..., +0.05] (uniform distribution)
    # we can calculate the expected VaR analytically and verify
    arr = np.linspace(-0.05, 0.05, 100)
    returns = pd.Series(arr)
    confidence_level = 0.95
    expected_var = np.quantile(returns, 1 - confidence_level)
    computed_var = historical_var(returns, confidence_level)
    assert abs(computed_var - expected_var) < 1e-6

def test_max_drawdown_known_input():
    returns = pd.Series([0.1, 0.1, -0.5])
    computed_drawdown = max_drawdown(returns)
    # Peak cumulative = 1.21, trough = 0.605
    # drawdown = (0.605 - 1.21) / 1.21 ≈ -0.5
    expected_drawdown = (0.605 - 1.21) / 1.21
    assert abs(computed_drawdown - expected_drawdown) < 1e-6

def test_weights_not_summing_to_one():
    with pytest.raises(ValidationError):
        PortfolioRequest(tickers=["0700.HK"], weights=[0.7], 
                        lookback_days=365, confidence_level=0.95)

def test_invalid_confidence_level():
    # confidence_level=1.5 should raise ValidationError
    with pytest.raises(ValidationError):
        PortfolioRequest(tickers=["0700.HK"], weights=[1.0], 
                        lookback_days=365, confidence_level=1.5)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Step 1: Create a test HTTP client that talks to your FastAPI app
# WITHOUT starting a real server — it simulates HTTP in-process
client = TestClient(app)

def test_analyse_endpoint_structure():

    # Step 2: Send a real POST request with valid input
    response = client.post("/risk/analyse", json={
        "tickers": ["0700.HK"],
        "weights": [1.0],
        "lookback_days": 365,
        "confidence_level": 0.95
    })

    # Step 3: Verify the HTTP status code — 200 means success
    # If this fails, something crashed before even building the response
    assert response.status_code == 200

    # Step 4: Parse the JSON response body into a Python dict
    data = response.json()

    # Step 5: Verify the TOP-LEVEL structure
    # We're checking the response has the right shape, not the values
    # (values change daily — AAPL's VaR today ≠ tomorrow)
    assert "portfolio" in data       # { "tickers": [...], "weights": [...] }
    assert "risk_metrics" in data    # { "var_historical": ..., ... }
    assert "period" in data          # { "start_date": ..., ... }
    assert "computed_at" in data     # timestamp string

    # Step 6: Drill into the nested dict to verify risk_metrics keys
    # data["risk_metrics"] is itself a dict — check its keys exist
    assert "var_historical" in data["risk_metrics"]
    assert "expected_shortfall" in data["risk_metrics"]
    assert "annualised_volatility" in data["risk_metrics"]

def test_risk_analyse_response_shape():
    payload = {
        "tickers": ["0700.HK"],
        "weights": [1.0],
        "lookback_days": 365,
        "confidence_level": 0.95
    }

    response = client.post("/risk/analyse", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "risk_metrics" in data
    assert "chart_data" in data
    assert "var_historical" in data["risk_metrics"]
    assert "expected_shortfall" in data["risk_metrics"]
    assert "labels" in data["chart_data"]
    assert "daily_returns" in data["chart_data"]
    assert "cumulative_returns" in data["chart_data"]