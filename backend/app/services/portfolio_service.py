import logging
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.portfolio import Portfolio, PortfolioHolding, PortfolioTransaction
from .stock_service import get_current_price, validate_symbol
from .prediction_engine import PredictionEngine

logger = logging.getLogger(__name__)

INITIAL_WALLET_BALANCE = 10000.0
prediction_engine = PredictionEngine()


def get_or_create_portfolio(db: Session, user_id: int) -> Portfolio:
    """Retrieve user portfolio or create a new one with $10,000 cash balance."""
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=user_id, cash_balance=INITIAL_WALLET_BALANCE)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        logger.info("Initialized new portfolio with $10,000 balance for user_id=%s", user_id)
    return portfolio


def execute_trade(db: Session, user_id: int, symbol: str, action: str, quantity: float) -> Dict[str, Any]:
    """Execute a simulated BUY or SELL trade based on real-time price quotes."""
    symbol = validate_symbol(symbol)
    action = action.upper()
    if action not in ["BUY", "SELL"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be 'BUY' or 'SELL'.")
    if quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be greater than zero.")

    portfolio = get_or_create_portfolio(db, user_id)

    # Fetch live price quote
    try:
        quote = get_current_price(symbol)
        price = quote.get("price")
        if not price or price <= 0:
            raise ValueError("Invalid price quote.")
    except Exception as exc:
        logger.error("Error fetching price for %s: %s", symbol, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to fetch live stock price for '{symbol}'. Check symbol validity."
        )

    total_cost = price * quantity

    if action == "BUY":
        if portfolio.cash_balance < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds. Required: ${total_cost:,.2f}, Available: ${portfolio.cash_balance:,.2f}"
            )
        
        # Deduct cash
        portfolio.cash_balance -= total_cost

        # Update or create holding
        holding = db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio.id,
            PortfolioHolding.symbol == symbol
        ).first()

        if holding:
            new_qty = holding.quantity + quantity
            # Recalculate weighted average buy price
            total_spent = (holding.quantity * holding.average_buy_price) + total_cost
            holding.average_buy_price = total_spent / new_qty
            holding.quantity = new_qty
        else:
            holding = PortfolioHolding(
                portfolio_id=portfolio.id,
                symbol=symbol,
                quantity=quantity,
                average_buy_price=price
            )
            db.add(holding)

    elif action == "SELL":
        holding = db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio.id,
            PortfolioHolding.symbol == symbol
        ).first()

        if not holding or holding.quantity < quantity:
            avail = holding.quantity if holding else 0.0
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient shares of {symbol} to sell. Owned: {avail}, Requested: {quantity}"
            )

        # Add cash proceeds
        portfolio.cash_balance += total_cost
        holding.quantity -= quantity

        # If holding quantity becomes 0, remove holding
        if holding.quantity <= 0.0001:
            db.delete(holding)

    # Record transaction
    transaction = PortfolioTransaction(
        portfolio_id=portfolio.id,
        symbol=symbol,
        transaction_type=action,
        quantity=quantity,
        price_per_share=price,
        total_amount=total_cost,
        timestamp=datetime.utcnow()
    )
    db.add(transaction)
    db.commit()
    db.refresh(portfolio)

    return {
        "success": True,
        "message": f"Successfully {action.lower()}ed {quantity} shares of {symbol} at ${price:,.2f} per share.",
        "transaction_id": transaction.id,
        "cash_balance": portfolio.cash_balance,
        "price_per_share": price,
        "total_amount": total_cost,
    }


def get_portfolio_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """Calculate portfolio performance, current holdings value, and AI recommendations."""
    portfolio = get_or_create_portfolio(db, user_id)
    holdings_list = []
    total_stock_value = 0.0
    total_cost_basis = 0.0

    for holding in portfolio.holdings:
        if holding.quantity <= 0:
            continue

        symbol = holding.symbol
        curr_price = holding.average_buy_price
        ai_rec = "HOLD"
        predicted_return = 0.0

        try:
            quote = get_current_price(symbol)
            if quote and quote.get("price"):
                curr_price = quote["price"]
        except Exception as e:
            logger.warning("Could not fetch current price for %s: %s", symbol, e)

        # Calculate AI recommendation based on prediction engine if available
        try:
            pred_res = prediction_engine.predict(symbol, model_name="linear")
            if pred_res and "data" in pred_res and "prediction" in pred_res["data"]:
                pred_price = pred_res["data"]["prediction"].get("predicted_price", curr_price)
                predicted_return = ((pred_price - curr_price) / curr_price) * 100
                if predicted_return > 2.0:
                    ai_rec = "BUY"
                elif predicted_return < -2.0:
                    ai_rec = "SELL"
                else:
                    ai_rec = "HOLD"
        except Exception:
            ai_rec = "HOLD"

        current_val = holding.quantity * curr_price
        cost_val = holding.quantity * holding.average_buy_price
        profit_loss = current_val - cost_val
        profit_loss_pct = (profit_loss / cost_val * 100) if cost_val > 0 else 0.0

        total_stock_value += current_val
        total_cost_basis += cost_val

        holdings_list.append({
            "id": holding.id,
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "average_buy_price": round(holding.average_buy_price, 2),
            "current_price": round(curr_price, 2),
            "total_value": round(current_val, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_pct": round(profit_loss_pct, 2),
            "ai_recommendation": ai_rec,
            "ai_predicted_return_pct": round(predicted_return, 2),
        })

    total_portfolio_value = portfolio.cash_balance + total_stock_value
    total_profit_loss = total_portfolio_value - INITIAL_WALLET_BALANCE
    total_profit_loss_pct = (total_profit_loss / INITIAL_WALLET_BALANCE) * 100

    return {
        "cash_balance": round(portfolio.cash_balance, 2),
        "total_stock_value": round(total_stock_value, 2),
        "total_portfolio_value": round(total_portfolio_value, 2),
        "total_profit_loss": round(total_profit_loss, 2),
        "total_profit_loss_pct": round(total_profit_loss_pct, 2),
        "initial_balance": INITIAL_WALLET_BALANCE,
        "holdings": holdings_list,
    }


def get_transactions(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Retrieve transaction history log for user."""
    portfolio = get_or_create_portfolio(db, user_id)
    tx_list = []
    for tx in sorted(portfolio.transactions, key=lambda x: x.timestamp, reverse=True):
        tx_list.append({
            "id": tx.id,
            "symbol": tx.symbol,
            "transaction_type": tx.transaction_type,
            "quantity": tx.quantity,
            "price_per_share": round(tx.price_per_share, 2),
            "total_amount": round(tx.total_amount, 2),
            "timestamp": tx.timestamp,
        })
    return tx_list


def reset_portfolio(db: Session, user_id: int) -> Dict[str, Any]:
    """Reset portfolio back to $10,000 cash balance and clear all holdings & transactions."""
    portfolio = get_or_create_portfolio(db, user_id)
    
    # Delete holdings and transactions
    db.query(PortfolioHolding).filter(PortfolioHolding.portfolio_id == portfolio.id).delete()
    db.query(PortfolioTransaction).filter(PortfolioTransaction.portfolio_id == portfolio.id).delete()
    
    portfolio.cash_balance = INITIAL_WALLET_BALANCE
    db.commit()
    db.refresh(portfolio)
    
    logger.info("Portfolio reset to $10,000 for user_id=%s", user_id)
    return {
        "success": True,
        "message": "Portfolio successfully reset to $10,000.00 initial balance.",
        "cash_balance": INITIAL_WALLET_BALANCE
    }
