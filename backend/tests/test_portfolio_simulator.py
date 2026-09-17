"""
Automated Test Suite for Virtual Portfolio & Paper Trading Simulator
Testing all 15 required specification scenarios.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.portfolio import SimulationAccount, SimulatedPosition, SimulatedOrder
from app.services import portfolio_service


# Setup in-memory SQLite DB for fast isolated unit testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create a clean database before each test run."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test user
    test_user = User(
        id=1,
        username="testtrader",
        email="testtrader@example.com",
        password_hash="hashedpassword123",
        is_active=True
    )
    db.add(test_user)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def get_test_db():
    db = TestingSessionLocal()
    try:
        return db
    finally:
        pass


# 1. Test Account Creation
def test_1_account_creation():
    db = get_test_db()
    account = portfolio_service.get_or_create_account(db, user_id=1)
    assert account is not None
    assert account.user_id == 1
    db.close()


# 2. Test Initial $10,000 Balance
def test_2_initial_10000_balance():
    db = get_test_db()
    account = portfolio_service.get_or_create_account(db, user_id=1)
    assert account.starting_cash == 10000.0
    assert account.cash_balance == 10000.0
    assert account.realized_pnl == 0.0
    db.close()


# 3. Test Successful BUY
def test_3_successful_buy():
    db = get_test_db()
    result = portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=10.0)
    assert result["success"] is True
    assert result["side"] == "BUY"
    assert result["quantity"] == 10.0
    assert result["cash_balance"] < 10000.0

    account = portfolio_service.get_or_create_account(db, user_id=1)
    position = db.query(SimulatedPosition).filter(SimulatedPosition.account_id == account.id, SimulatedPosition.symbol == "AAPL").first()
    assert position is not None
    assert position.quantity == 10.0
    db.close()


# 4. Test BUY with Insufficient Funds
def test_4_buy_insufficient_funds():
    db = get_test_db()
    with pytest.raises(HTTPException) as exc_info:
        portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=100000.0)
    assert exc_info.value.status_code == 400
    assert "Insufficient virtual cash" in exc_info.value.detail
    db.close()


# 5. Test Successful SELL
def test_5_successful_sell():
    db = get_test_db()
    # Buy 10 shares first
    portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=10.0)
    
    # Sell 5 shares
    result = portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="SELL", quantity=5.0)
    assert result["success"] is True
    assert result["side"] == "SELL"

    account = portfolio_service.get_or_create_account(db, user_id=1)
    position = db.query(SimulatedPosition).filter(SimulatedPosition.account_id == account.id, SimulatedPosition.symbol == "AAPL").first()
    assert position is not None
    assert position.quantity == 5.0
    db.close()


# 6. Test SELL without Sufficient Shares
def test_6_sell_insufficient_shares():
    db = get_test_db()
    with pytest.raises(HTTPException) as exc_info:
        portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="SELL", quantity=5.0)
    assert exc_info.value.status_code == 400
    assert "Insufficient shares to sell" in exc_info.value.detail
    db.close()


# 7. Test Average Buy Price Calculation
def test_7_average_buy_price_calculation():
    db = get_test_db()
    # Buy 10 shares
    portfolio_service.execute_order(db, user_id=1, symbol="INFY", side="BUY", quantity=10.0)
    account = portfolio_service.get_or_create_account(db, user_id=1)
    pos1 = db.query(SimulatedPosition).filter(SimulatedPosition.account_id == account.id, SimulatedPosition.symbol == "INFY").first()
    price1 = pos1.average_buy_price

    # Buy another 10 shares
    portfolio_service.execute_order(db, user_id=1, symbol="INFY", side="BUY", quantity=10.0)
    db.refresh(pos1)
    assert pos1.quantity == 20.0
    # Average buy price should reflect weighted average
    assert abs(pos1.average_buy_price - price1) < 0.01
    db.close()


# 8. Test Realized P&L
def test_8_realized_pnl():
    db = get_test_db()
    portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=10.0)
    portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="SELL", quantity=5.0)
    
    summary = portfolio_service.get_portfolio_summary(db, user_id=1)
    assert "total_realized_pnl" in summary
    assert isinstance(summary["total_realized_pnl"], float)
    db.close()


# 9. Test Unrealized P&L
def test_9_unrealized_pnl():
    db = get_test_db()
    portfolio_service.execute_order(db, user_id=1, symbol="MSFT", side="BUY", quantity=5.0)
    summary = portfolio_service.get_portfolio_summary(db, user_id=1)
    assert "total_unrealized_pnl" in summary
    assert isinstance(summary["total_unrealized_pnl"], float)
    db.close()


# 10. Test Portfolio Value Formula
def test_10_portfolio_value_formula():
    db = get_test_db()
    summary_before = portfolio_service.get_portfolio_summary(db, user_id=1)
    assert summary_before["portfolio_value"] == 10000.0

    portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=5.0)
    summary_after = portfolio_service.get_portfolio_summary(db, user_id=1)
    
    expected_val = summary_after["cash_balance"] + summary_after["total_stock_value"]
    assert abs(summary_after["portfolio_value"] - expected_val) < 0.05
    db.close()


# 11. Test Authentication / Account Scoping
def test_11_account_isolation():
    db = get_test_db()
    user2 = User(id=2, username="user2", email="user2@test.com", password_hash="pass", is_active=True)
    db.add(user2)
    db.commit()

    # User 1 buys AAPL
    portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=10.0)

    # User 2 summary should have 0 holdings
    summary2 = portfolio_service.get_portfolio_summary(db, user_id=2)
    assert len(summary2["positions"]) == 0
    assert summary2["cash_balance"] == 10000.0
    db.close()


# 12. Test Transaction Rollback
def test_12_transaction_rollback():
    db = get_test_db()
    account_before = portfolio_service.get_or_create_account(db, user_id=1)
    cash_before = account_before.cash_balance

    with pytest.raises(HTTPException):
        # Invalid buy quantity will trigger failure
        portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=-10.0)

    account_after = portfolio_service.get_or_create_account(db, user_id=1)
    assert account_after.cash_balance == cash_before
    db.close()


# 13. Test Reset Functionality
def test_13_reset_functionality():
    db = get_test_db()
    portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=10.0)
    portfolio_service.execute_order(db, user_id=1, symbol="TSLA", side="BUY", quantity=5.0)

    reset_res = portfolio_service.reset_simulation_account(db, user_id=1)
    assert reset_res["success"] is True
    assert reset_res["cash_balance"] == 10000.0

    summary = portfolio_service.get_portfolio_summary(db, user_id=1)
    assert summary["cash_balance"] == 10000.0
    assert len(summary["positions"]) == 0
    assert len(summary["recent_orders"]) == 0
    db.close()


# 14. Test Invalid Quantity
def test_14_invalid_quantity():
    db = get_test_db()
    with pytest.raises(HTTPException) as exc_info:
        portfolio_service.execute_order(db, user_id=1, symbol="AAPL", side="BUY", quantity=0.0)
    assert exc_info.value.status_code == 400
    assert "Quantity must be greater than zero" in exc_info.value.detail
    db.close()


# 15. Test Invalid Stock Symbol
def test_15_invalid_stock_symbol():
    db = get_test_db()
    with pytest.raises(HTTPException) as exc_info:
        portfolio_service.execute_order(db, user_id=1, symbol="INVALID_XYZ_1234567890", side="BUY", quantity=10.0)
    assert exc_info.value.status_code == 400
    db.close()
