import logging
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.portfolio import SimulationAccount, SimulatedPosition, SimulatedOrder
from .stock_service import get_current_price, validate_symbol

logger = logging.getLogger(__name__)

INITIAL_STARTING_CASH = 10000.0


def get_or_create_account(db: Session, user_id: int) -> SimulationAccount:
    """Retrieve or initialize user's SimulationAccount with $10,000 starting cash."""
    account = db.query(SimulationAccount).filter(SimulationAccount.user_id == user_id).first()
    if not account:
        account = SimulationAccount(
            user_id=user_id,
            starting_cash=INITIAL_STARTING_CASH,
            cash_balance=INITIAL_STARTING_CASH,
            realized_pnl=0.0
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        logger.info("Created SimulationAccount with $10,000 for user_id=%s", user_id)
    return account


def execute_order(db: Session, user_id: int, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
    """Execute a simulated BUY or SELL order atomically within a database transaction."""
    if quantity is None or quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than zero."
        )

    side_upper = side.upper() if side else ""
    if side_upper not in ["BUY", "SELL"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order side must be 'BUY' or 'SELL'."
        )

    # Validate stock symbol
    try:
        symbol_norm = validate_symbol(symbol)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    # Fetch live execution price
    try:
        quote = get_current_price(symbol_norm)
        execution_price = quote.get("price") if quote else None
        if not execution_price or execution_price <= 0:
            raise ValueError("Invalid market quote price.")
    except Exception as exc:
        logger.error("Failed to retrieve market price for %s: %s", symbol_norm, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market price unavailable for stock symbol '{symbol_norm}'."
        )

    total_value = round(quantity * execution_price, 4)

    # Atomic DB Transaction
    try:
        with db.begin_nested():
            account = db.query(SimulationAccount).filter(SimulationAccount.user_id == user_id).with_for_update().first()
            if not account:
                account = SimulationAccount(
                    user_id=user_id,
                    starting_cash=INITIAL_STARTING_CASH,
                    cash_balance=INITIAL_STARTING_CASH,
                    realized_pnl=0.0
                )
                db.add(account)
                db.flush()

            if side_upper == "BUY":
                if account.cash_balance < total_value:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient virtual cash. Required: ${total_value:,.2f}, Available: ${account.cash_balance:,.2f}"
                    )

                # Deduct cash balance
                account.cash_balance -= total_value

                # Update or create position
                position = db.query(SimulatedPosition).filter(
                    SimulatedPosition.account_id == account.id,
                    SimulatedPosition.symbol == symbol_norm
                ).with_for_update().first()

                if position:
                    new_qty = position.quantity + quantity
                    total_cost_basis = (position.quantity * position.average_buy_price) + total_value
                    position.average_buy_price = total_cost_basis / new_qty
                    position.quantity = new_qty
                else:
                    position = SimulatedPosition(
                        account_id=account.id,
                        symbol=symbol_norm,
                        quantity=quantity,
                        average_buy_price=execution_price
                    )
                    db.add(position)

            elif side_upper == "SELL":
                position = db.query(SimulatedPosition).filter(
                    SimulatedPosition.account_id == account.id,
                    SimulatedPosition.symbol == symbol_norm
                ).with_for_update().first()

                if not position or position.quantity < quantity:
                    avail_shares = position.quantity if position else 0.0
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient shares to sell. Owned: {avail_shares}, Requested: {quantity}"
                    )

                # Calculate realized P&L on sold portion
                realized_gain = quantity * (execution_price - position.average_buy_price)
                account.realized_pnl += realized_gain

                # Add cash proceeds
                account.cash_balance += total_value
                position.quantity -= quantity

                if position.quantity <= 0.0001:
                    db.delete(position)

            # Record order entry
            order = SimulatedOrder(
                account_id=account.id,
                symbol=symbol_norm,
                side=side_upper,
                quantity=quantity,
                execution_price=execution_price,
                total_value=total_value,
                status="COMPLETED",
                created_at=datetime.utcnow()
            )
            db.add(order)

        db.commit()
        db.refresh(account)

        return {
            "success": True,
            "message": f"Successfully executed {side_upper} order for {quantity} shares of {symbol_norm} @ ${execution_price:,.2f}",
            "order_id": order.id,
            "side": side_upper,
            "symbol": symbol_norm,
            "quantity": quantity,
            "execution_price": execution_price,
            "total_value": total_value,
            "cash_balance": round(account.cash_balance, 2)
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Database transaction error during order execution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction error during order execution."
        )


def get_portfolio_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Compute portfolio value, unrealized P&L, realized P&L, return %, positions, and recent orders."""
    account = get_or_create_account(db, user_id)
    positions_list = []
    total_market_value_holdings = 0.0
    total_unrealized_pnl = 0.0

    positions = db.query(SimulatedPosition).filter(SimulatedPosition.account_id == account.id).all()

    for pos in positions:
        if pos.quantity <= 0:
            continue

        symbol = pos.symbol
        current_price = pos.average_buy_price

        try:
            quote = get_current_price(symbol)
            if quote and quote.get("price"):
                current_price = quote["price"]
        except Exception as exc:
            logger.warning("Market quote fallback for %s: %s", symbol, exc)

        holding_market_value = pos.quantity * current_price
        cost_basis = pos.quantity * pos.average_buy_price
        unrealized_pnl = holding_market_value - cost_basis
        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0

        total_market_value_holdings += holding_market_value
        total_unrealized_pnl += unrealized_pnl

        positions_list.append({
            "id": pos.id,
            "symbol": pos.symbol,
            "quantity": round(pos.quantity, 4),
            "average_buy_price": round(pos.average_buy_price, 2),
            "current_price": round(current_price, 2),
            "total_market_value": round(holding_market_value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
            "total_value": round(holding_market_value, 2),
            "profit_loss": round(unrealized_pnl, 2),
            "profit_loss_pct": round(unrealized_pnl_pct, 2),
        })

    portfolio_value = account.cash_balance + total_market_value_holdings
    starting_cash = account.starting_cash if account.starting_cash > 0 else INITIAL_STARTING_CASH
    total_profit_loss = portfolio_value - starting_cash
    total_return_percentage = ((portfolio_value - starting_cash) / starting_cash) * 100.0

    # Recent orders history
    orders = db.query(SimulatedOrder).filter(SimulatedOrder.account_id == account.id).order_by(SimulatedOrder.created_at.desc()).limit(20).all()
    recent_orders_list = [
        {
            "id": ord.id,
            "symbol": ord.symbol,
            "side": ord.side,
            "transaction_type": ord.side,
            "quantity": ord.quantity,
            "execution_price": round(ord.execution_price, 2),
            "price_per_share": round(ord.execution_price, 2),
            "total_value": round(ord.total_value, 2),
            "total_amount": round(ord.total_value, 2),
            "status": ord.status,
            "created_at": ord.created_at,
            "timestamp": ord.created_at.isoformat() if hasattr(ord.created_at, 'isoformat') else str(ord.created_at),
        }
        for ord in orders
    ]

    return {
        "account_id": account.id,
        "starting_cash": round(starting_cash, 2),
        "cash_balance": round(account.cash_balance, 2),
        "total_stock_value": round(total_market_value_holdings, 2),
        "portfolio_value": round(portfolio_value, 2),
        "total_portfolio_value": round(portfolio_value, 2),
        "total_unrealized_pnl": round(total_unrealized_pnl, 2),
        "total_realized_pnl": round(account.realized_pnl, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "total_profit_loss_pct": round(total_return_percentage, 2),
        "total_return_percentage": round(total_return_percentage, 2),
        "positions": positions_list,
        "holdings": positions_list,
        "recent_orders": recent_orders_list,
    }


def reset_simulation_account(db: Session, user_id: int) -> Dict[str, Any]:
    """Reset account back to $10,000 cash balance and clear all positions & orders."""
    account = get_or_create_account(db, user_id)
    try:
        with db.begin_nested():
            db.query(SimulatedPosition).filter(SimulatedPosition.account_id == account.id).delete()
            db.query(SimulatedOrder).filter(SimulatedOrder.account_id == account.id).delete()
            account.starting_cash = INITIAL_STARTING_CASH
            account.cash_balance = INITIAL_STARTING_CASH
            account.realized_pnl = 0.0
        db.commit()
        db.refresh(account)
        logger.info("Successfully reset simulation account for user_id=%s", user_id)
        return {
            "success": True,
            "message": "Simulation account successfully reset to $10,000.00 cash.",
            "cash_balance": INITIAL_STARTING_CASH
        }
    except Exception as exc:
        db.rollback()
        logger.error("Reset failed for user_id=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset simulation account."
        )
