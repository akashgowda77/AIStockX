from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from ..models.user import User
from ..schemas.portfolio import TradeRequest, PortfolioSummaryResponse, TransactionResponse
from ..services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioSummaryResponse)
def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve current user's virtual portfolio summary, cash balance, holdings, and P&L."""
    return portfolio_service.get_portfolio_summary(db, current_user.id)


@router.post("/trade")
def execute_trade(
    trade: TradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a simulated BUY or SELL trade for a stock symbol."""
    return portfolio_service.execute_trade(
        db=db,
        user_id=current_user.id,
        symbol=trade.symbol,
        action=trade.action,
        quantity=trade.quantity
    )


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve history of executed simulated trades."""
    return portfolio_service.get_transactions(db, current_user.id)


@router.post("/reset")
def reset_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset virtual portfolio balance back to $10,000.00 and clear holdings."""
    return portfolio_service.reset_portfolio(db, current_user.id)
