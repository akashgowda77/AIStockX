from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class OrderCreateRequest(BaseModel):
    """Schema for placing a simulated BUY or SELL order."""
    symbol: str = Field(..., example="AAPL")
    side: Optional[str] = Field(None, example="BUY")  # 'BUY' or 'SELL'
    action: Optional[str] = Field(None, example="BUY")
    quantity: float = Field(..., gt=0, example=10.0)


class SimulatedPositionResponse(BaseModel):
    """Schema for a position holding response."""
    id: int
    symbol: str
    quantity: float
    average_buy_price: float
    current_price: float
    total_market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float

    class Config:
        from_attributes = True


class SimulatedOrderResponse(BaseModel):
    """Schema for a simulated order ledger record."""
    id: int
    symbol: str
    side: str
    quantity: float
    execution_price: float
    total_value: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class PortfolioSummaryResponse(BaseModel):
    """Schema for overall simulation account summary."""
    account_id: int
    starting_cash: float
    cash_balance: float
    total_stock_value: float = 0.0
    portfolio_value: float
    total_unrealized_pnl: float
    total_realized_pnl: float
    total_profit_loss: float
    total_return_percentage: float
    positions: List[SimulatedPositionResponse] = []
    recent_orders: List[SimulatedOrderResponse] = []
