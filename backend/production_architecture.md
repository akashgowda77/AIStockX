# Production Architecture & System Design Specification
## AIStockX Virtual Portfolio & Paper Trading Simulator

---

### 1. Architectural Overview & Data Model Design

The AIStockX Virtual Portfolio Simulator allows authenticated users to simulate real-world financial stock transactions in a controlled paper-trading environment with virtual cash ($10,000 default balance). The domain model is built with strict relational integrity using SQLAlchemy and FastAPI.

```
       +-----------------------+
       |         User          |
       +-----------------------+
                   | 1
                   |
                   | 1
       +-----------------------+
       |   SimulationAccount   |
       +-----------------------+
         | 1                 | 1
         |                   |
         | *                 | *
+-----------------+   +-----------------+
|SimulatedPosition|   | SimulatedOrder  |
+-----------------+   +-----------------+
```

#### Entity Breakdown & Purpose
1. **`SimulationAccount`**:
   - Stores the user's primary virtual wallet ledger state: `starting_cash` ($10,000.00), `cash_balance` (available uninvested funds), and total `realized_pnl` accumulated from closed position trades.
   - Enforces 1-to-1 mapping per registered `user_id`.

2. **`SimulatedPosition`**:
   - Represents currently open stock holdings.
   - Stores `quantity` and weighted `average_buy_price` for each `symbol` (e.g., AAPL, INFY, INTC).
   - Dynamically calculates market value and unrealized profit/loss against live price feeds.

3. **`SimulatedOrder`**:
   - An immutable transaction ledger record capturing every buy/sell trade.
   - Preserves historical audit metadata: `symbol`, `side` (`BUY`/`SELL`), `quantity`, `execution_price`, `total_value`, `status`, and execution timestamp (`created_at`).

---

### 2. Order Ledger & Immutability Principles

Financial compliance and accurate portfolio accounting require strict ledger immutability:
- **Never Update or Delete Orders**: The `SimulatedOrder` table functions as an append-only transaction journal. Once written, an order record is never modified or deleted.
- **Auditability & Traceability**: Every portfolio balance change (cash deduction, cash addition, position size shift) strictly correlates with a corresponding immutable `SimulatedOrder` entry.
- **Reconciliation Engine**: In production, the system can reconstruct current position states and cash balances from scratch by replaying all historical order entries in chronological order.

---

### 3. Transactional Integrity & P&L Mechanics

All order processing takes place inside explicit ACID database transactions to prevent partial updates or inconsistent states.

#### Weighted Average Buy Price Calculation
When buying additional shares of an existing position:
$$\text{Average Buy Price}_{\text{new}} = \frac{(\text{Current Qty} \times \text{Current Avg Price}) + (\text{New Qty} \times \text{Execution Price})}{\text{Current Qty} + \text{New Qty}}$$

#### Realized vs. Unrealized P&L
- **Realized P&L**: Triggered on `SELL` orders. Computed on the exact quantity sold:
  $$\text{Realized Gain} = \text{Quantity}_{\text{sold}} \times (\text{Execution Price} - \text{Average Buy Price})$$
  This gain is permanently added to `SimulationAccount.realized_pnl`.
- **Unrealized P&L**: Calculated on live market demand:
  $$\text{Unrealized P&L} = (\text{Quantity}_{\text{owned}} \times \text{Market Price}_{\text{live}}) - (\text{Quantity}_{\text{owned}} \times \text{Average Buy Price})$$

---

### 4. Concurrency Control & Row-Level Locking

High-throughput trading systems face race conditions (e.g., double-spending cash balance via simultaneous API calls).

#### SQLite vs. PostgreSQL Strategy
- **SQLite (Development/Testing)**: SQLite handles concurrent writes via database-level file locks (`WAL` mode recommended). While safe, it serializes write operations across concurrent requests.
- **PostgreSQL (Production Standard)**:
  - Row-Level Locking: `SELECT ... FOR UPDATE` is executed when fetching `SimulationAccount` and target `SimulatedPosition`.
  - Transaction Isolation: Serializable or Read Committed isolation levels ensure concurrent buy/sell operations block safely at row boundaries until the active transaction commits or rolls back.

```python
# PostgreSQL Row-Level Lock Pattern
account = db.query(SimulationAccount).filter(
    SimulationAccount.user_id == user_id
).with_for_update().first()
```

---

### 5. Price Feed Caching & Rate Limiting (Redis)

Live stock market quotes (yfinance/Alpha Vantage APIs) introduce HTTP latency and external API rate limit risks.

#### Caching Architecture
- **In-Memory Cache Layer (Redis)**: Stock prices are cached with a configurable TTL (e.g., 5 to 15 seconds during market hours).
- **Stale-While-Revalidate**: If the quote provider API fails or hits rate limits, the system gracefully falls back to cached prices or position entry prices without crashing user trades.

---

### 6. Time-Series Performance History & High-Frequency Scaling

To track portfolio performance over time (equity curves and return percentages):
1. **Periodic Snapshot Worker**: A background worker (Celery / APScheduler / Redis Queue) takes periodic snapshots of `portfolio_value`, `cash_balance`, and `unrealized_pnl` (e.g., daily at market close or hourly).
2. **Time-Series Storage**: Snapshot metrics are written to time-series optimized tables (e.g., PostgreSQL TimescaleDB hyper-tables or InfluxDB) for fast charting and analytics rendering.
