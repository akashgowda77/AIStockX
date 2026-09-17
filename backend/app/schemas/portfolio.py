from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TradeRequest(BaseModel):
    """Schema for submitting a trade request."""
    symbol: str = Field(..., example="INFY")
    action: str = Field(..., example="BUY")  # 'BUY' or 'SELL'
    quantity: float = Field(..., gt=0, example=5.0)


class HoldingResponse(BaseModel):
    """Schema for an individual holding item."""
    id: int
    symbol: str
    quantity: float
    average_buy_price: float
    current_price: float
    total_value: float
    profit_loss: float
    profit_loss_pct: float
    ai_recommendation: Optional[str] = "HOLD"
    ai_predicted_return_pct: Optional[float] = 0.0

    class Config:
        from_attributes = True


class PortfolioSummaryResponse(BaseModel):
    """Schema for overall portfolio summary."""
    cash_balance: float
    total_stock_value: float
    total_portfolio_value: float
    total_profit_loss: float
    total_profit_loss_pct: float
    initial_balance: float = 10000.0
    holdings: List[HoldingResponse] = []


class TransactionResponse(BaseModel):
    """Schema for trade transaction history item."""
    id: int
    symbol: str
    transaction_type: str
    quantity: float
    price_per_share: float
    total_amount: float
    timestamp: datetime

    class Config:
        from_attributes = True
