from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SimulationAccount(Base):
    """Simulation account containing user virtual cash and realized P&L."""

    __tablename__ = "simulation_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    starting_cash: Mapped[float] = mapped_column(Float, default=10000.0, nullable=False)
    cash_balance: Mapped[float] = mapped_column(Float, default=10000.0, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    positions: Mapped[list["SimulatedPosition"]] = relationship("SimulatedPosition", back_populates="account", cascade="all, delete-orphan")
    orders: Mapped[list["SimulatedOrder"]] = relationship("SimulatedOrder", back_populates="account", cascade="all, delete-orphan")


class SimulatedPosition(Base):
    """Individual stock position owned in a simulation account."""

    __tablename__ = "simulated_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulation_accounts.id"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_buy_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    account: Mapped["SimulationAccount"] = relationship("SimulationAccount", back_populates="positions")


class SimulatedOrder(Base):
    """Simulated order ledger entry (BUY/SELL)."""

    __tablename__ = "simulated_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulation_accounts.id"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # 'BUY' or 'SELL'
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    execution_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    account: Mapped["SimulationAccount"] = relationship("SimulationAccount", back_populates="orders")
