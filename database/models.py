from sqlalchemy import Integer, Float, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from database.db import Base
from datetime import datetime, timezone

class RiskQuery(Base):
    __tablename__ = "risk_queries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tickers: Mapped[str] = mapped_column(Text, nullable=False)  # Store as a comma-separated string
    weights: Mapped[str] = mapped_column(Text, nullable=False)  # Store as a comma-separated string
    lookback_days: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)  # Store the JSON result as a string
    queried_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
