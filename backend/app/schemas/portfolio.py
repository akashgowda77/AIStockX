from datetime import datetime
from typing import List, Optional, Any
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
    # Alias fields for frontend JS compatibility
    total_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    ai_recommendation: Optional[str] = "HOLD"
    ai_predicted_return_pct: Optional[float] = 0.0

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
    created_at: Any
    # Alias fields for frontend JS compatibility
    transaction_type: Optional[str] = None
    price_per_share: Optional[float] = None
    total_amount: Optional[float] = None
    timestamp: Optional[Any] = None

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
    # Alias fields for frontend JS compatibility
    total_portfolio_value: Optional[float] = None
    total_profit_loss_pct: Optional[float] = None
    holdings: List[SimulatedPositionResponse] = []
    today_pnl: Optional[float] = 0.0
    today_pnl_pct: Optional[float] = 0.0
    unrealized_pnl: Optional[float] = 0.0
    unrealized_pnl_pct: Optional[float] = 0.0
