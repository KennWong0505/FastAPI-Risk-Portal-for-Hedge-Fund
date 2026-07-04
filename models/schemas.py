from pydantic import BaseModel, Field, field_validator
from typing import Annotated

TickerStr = Annotated[str, Field(pattern=r"^[A-Z0-9.^=-]{1,20}$")]
PositiveFloat = Annotated[float, Field(gt=0.0)]

class PortfolioRequest(BaseModel):
    """Schema for validating input data."""
    tickers: list[TickerStr]
    weights: list[PositiveFloat] = Field(min_length=1)
    lookback_days: int = Field(gt=0, le=3650)  # sensible: 1 day to 10 years
    confidence_level: float = Field(ge=0.0, le=1.0)

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, weights: list[PositiveFloat]) -> list[PositiveFloat]:
        """Validates that the sum of weights is equal to 1."""
        if abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("Weights must sum to 1.0")
        return weights