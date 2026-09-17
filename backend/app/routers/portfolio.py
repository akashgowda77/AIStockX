from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_current_user
from ..models.user import User
from ..schemas.portfolio import OrderCreateRequest, PortfolioSummaryResponse, SimulatedOrderResponse
from ..services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])


@router.get("", response_model=PortfolioSummaryResponse)
def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve current user's simulation account summary, cash balance, positions, and P&L."""
    return portfolio_service.get_portfolio_summary(db, current_user.id)


@router.post("/order")
def execute_order(
    order: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a simulated BUY or SELL order."""
    side_val = order.side or order.action
    return portfolio_service.execute_order(
        db=db,
        user_id=current_user.id,
        symbol=order.symbol,
        side=side_val,
        quantity=order.quantity
    )


@router.post("/trade")
def execute_trade_alias(
    order: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a simulated BUY or SELL order (compatibility endpoint)."""
    side_val = order.side or order.action
    return portfolio_service.execute_order(
        db=db,
        user_id=current_user.id,
        symbol=order.symbol,
        side=side_val,
        quantity=order.quantity
    )


@router.get("/orders", response_model=List[SimulatedOrderResponse])
def get_order_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve history of executed simulated orders."""
    summary = portfolio_service.get_portfolio_summary(db, current_user.id)
    return summary.get("recent_orders", [])


@router.get("/transactions", response_model=List[SimulatedOrderResponse])
def get_transactions_alias(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve history of executed simulated orders (compatibility endpoint)."""
    summary = portfolio_service.get_portfolio_summary(db, current_user.id)
    return summary.get("recent_orders", [])


@router.post("/reset")
def reset_simulation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset virtual simulation account back to $10,000.00 initial cash balance."""
    return portfolio_service.reset_simulation_account(db, current_user.id)
