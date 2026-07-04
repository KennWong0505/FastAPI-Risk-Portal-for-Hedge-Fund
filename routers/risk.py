from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from database.db import get_db
from database.models import RiskQuery
from models.schemas import PortfolioRequest
from services.data import get_price_data
from services import metrics
from datetime import datetime, timedelta
import json
import numpy as np

router = APIRouter(prefix="/risk", tags=["Risk"])

@router.post("/analyse")
def analyse_portfolio(request: PortfolioRequest, db: Session = Depends(get_db)):
    # Step 1: fetch log returns using request.tickers and request.lookback_days
    # Step 2: compute portfolio returns using request.weights
    # Step 3: call all 7 metric functions
    # Step 4: return the structured JSON response above
    try:
        log_returns = get_price_data(request.tickers, request.lookback_days)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    portfolio_returns = metrics.compute_portfolio_returns(log_returns, request.weights)

    historical_var = metrics.historical_var(portfolio_returns, request.confidence_level)
    historical_es = metrics.historical_es(portfolio_returns, request.confidence_level)
    variance_covariance_var = metrics.variance_covariance_var(log_returns, request.weights, request.confidence_level)
    monte_carlo_var = metrics.monte_carlo_var(log_returns, request.weights, request.confidence_level)
    annualised_volatility = metrics.annualised_volatility(portfolio_returns)
    sharpe_ratio = metrics.sharpe_ratio(portfolio_returns)
    max_drawdown = metrics.max_drawdown(portfolio_returns)

    cum = (1 + portfolio_returns).cumprod()
    daily = portfolio_returns.tolist()
    labels = [d.strftime("%Y-%m-%d") for d in portfolio_returns.index]
    cumulative = (cum - 1).tolist()

    result = {
        "portfolio": {
            "tickers": request.tickers,
            "weights": request.weights
        },
        "period": {
            "start_date": (datetime.today() - timedelta(days=request.lookback_days)).strftime("%Y-%m-%d"),
            "end_date": datetime.today().strftime("%Y-%m-%d"),
            "trading_days": len(log_returns)
        },
        "risk_metrics": {
            "var_historical": historical_var,
            "var_variance_covariance": variance_covariance_var,
            "var_monte_carlo": monte_carlo_var,
            "expected_shortfall": historical_es,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "annualised_volatility": annualised_volatility
        },
        "chart_data": {
            "labels": labels,
            "daily_returns": daily,
            "cumulative_returns": cumulative
        },
        "computed_at": datetime.utcnow().isoformat()
    }

    # Store the request and result in the database
    risk_query = RiskQuery(
        tickers=",".join(request.tickers),
        weights=",".join(map(str, request.weights)),
        lookback_days=request.lookback_days,
        confidence_level=request.confidence_level,
        result_json=json.dumps(result)
    )
    db.add(risk_query)
    db.commit()
    db.refresh(risk_query)

    return result

@router.get("/history")
def get_history(db: Session = Depends(get_db)):
    """Fetches all past risk queries from the database."""
    queries = db.query(RiskQuery).all()
    return [
        {
            "id": q.id,
            "tickers": q.tickers.split(","),
            "weights": list(map(float, q.weights.split(","))),
            "lookback_days": q.lookback_days,
            "confidence_level": q.confidence_level,
            "result": json.loads(q.result_json),
            "queried_at": q.queried_at.isoformat()
        }
        for q in queries
    ]