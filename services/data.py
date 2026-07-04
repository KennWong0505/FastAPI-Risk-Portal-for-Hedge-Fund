from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np

def get_price_data(tickers: list[str], lookback_days: int) -> pd.DataFrame:
    """
    Fetches adjusted closing prices for given tickers over the lookback period,
    and returns a DataFrame of daily log returns.
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)

    df = yf.download(tickers, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), auto_adjust=True)

    prices = df["Close"]
    
    # Check for any invalid tickers
    prices = df["Close"]
    missing = [t for t in tickers if t not in prices.columns or prices[t].isna().all()]
    if missing:
        raise ValueError(f"Could not fetch data for tickers: {missing}")
    
    # To handle the single ticker case
    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])
    
    log_returns = np.log(prices / prices.shift(1)).dropna()

    return log_returns