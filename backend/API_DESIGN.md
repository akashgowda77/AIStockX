# AIStockX — API Design (Backend)

This document describes the backend API contract for **Phase 3 (Stock Intelligence Module)** and beyond.

> Note: Do **not** implement these APIs yet (implementation starts in the next phases). This file is the specification only.

---

## Base Notes
- All endpoints are under the API prefix: `/api/v1` (unless otherwise stated in implementation).
- Authentication: most endpoints will require a valid **JWT Bearer token** from `/auth/login`.
- Error style (recommended):
  - `400` invalid request
  - `401` unauthorized
  - `404` resource not found
  - `500` internal server error

---

## Authentication

### POST `/auth/register`
Registers a new user.

**Request body**
- `username` (string, required)
- `email` (string, required, email format)
- `password` (string, required, min length enforced)

**Response**
- `201` JSON user summary

---

### POST `/auth/login`
Logs in using username or email.

**Request body**
- `username_or_email` (string, required)
- `password` (string, required)

**Response**
- `200` JSON:
  - `access_token` (string)
  - `token_type` (string, e.g., `bearer`)

---

### GET `/auth/me`
Returns the currently authenticated user.

**Auth**: `Authorization: Bearer <token>`

**Response**
- `200` JSON `UserResponse`:
  - `id`
  - `username`
  - `email`
  - `created_at`

---

## Stocks

### GET `/stocks/search?query=<text>`
Search stocks by company name or symbol.

**Query params**
- `query` (string, required)

**Response**
- `200` JSON list of matches:
  - `symbol`
  - `name`
  - (optional) `exchange`, `currency`

---

### GET `/stocks/history/{symbol}`
Returns historical market data for the symbol.

**Path params**
- `symbol` (string)

**Query params (recommended defaults)**
- period (string, optional, default: 1y)




- `interval` (string, optional, default `1d`)

**Response**
- `200` JSON list ordered by time (ascending):
  - `date`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`

---

### GET `/stocks/company/{symbol}`
Returns company profile.

**Path params**
- `symbol`

**Response**
- `200` JSON:
  - `symbol`
  - `name`
  - `sector` (if available)
  - `industry` (if available)
  - `description` (if available)
  - `website` (if available)

---

### GET `/stocks/quote/{symbol}`
Returns the latest quote.

**Path params**
- `symbol`

**Response**
- `200` JSON:
  - `symbol`
  - `price`
  - `previous_close` (if available)
  - `change` (if available)
  - `percent_change` (if available)

---

### GET `/stocks/trending`
Returns most active / trending stocks.

**Query params (recommended defaults)**
- `limit` (int, optional, default `10`)

**Response**
- `200` JSON list:
  - `symbol`
  - `name` (optional)
  - `activity_score` (optional)

---

## Technical Indicators

### GET `/indicators/{symbol}`
Computes technical indicators from historical prices.

**Path params**
- `symbol`

**Query params (recommended)**
- `period` (string, optional, default `6mo`)
- `interval` (string, optional, default `1d`)
- `window` parameters are fixed by implementation defaults (SMA/EMA/BB length, RSI length, MACD params)

**Response**
- `200` JSON containing the indicator series:
  - `dates`: list of ISO date strings
  - `sma`: list of SMA values
  - `ema`: list of EMA values
  - `rsi`: list of RSI values
  - `macd`: list of MACD values
  - `macd_signal`: list of MACD signal values (if computed)
  - `bollinger_bands`:
    - `upper`: list
    - `middle`: list
    - `lower`: list

---

## Prediction

> Implementation uses **yfinance** historical closing prices and generates forecasts.

### POST `/prediction/linear`
Predict future prices using Linear Regression.

**Auth**: recommended (JWT)

**Request body**
- `symbol` (string, required)
- `horizon_days` (int, optional, default `5`)
- `period` (string, optional, default `2y`)

**Response**
- `200` JSON:
  - `symbol`
  - `model`: `linear_regression`
  - `forecast`: list of predicted prices for next horizon
  - `metrics`:
    - `rmse`
    - `mae`
    - `mape`
    - `r2`

---

### POST `/prediction/lstm`
Predict future prices using LSTM.

**Auth**: recommended (JWT)

**Request body**
- `symbol` (string, required)
- `horizon_days` (int, optional, default `5`)
- `period` (string, optional, default `2y`)

**Response**
- `200` JSON:
  - `symbol`
  - `model`: `lstm`
  - `forecast`: list of predicted prices for next horizon
  - `metrics`:
    - `rmse`
    - `mae`
    - `mape`
    - `r2`

---

### GET `/prediction/compare/{symbol}`
Compares both models and returns recommended model.

**Path params**
- `symbol`

**Query params (recommended)**
- `horizon_days` (int, optional, default `5`)
- `period` (string, optional, default `2y`)

**Response**
- `200` JSON:
  - `symbol`
  - `comparison`:
    - `linear_regression`:
      - `forecast`
      - `metrics`: `rmse/mae/mape/r2`
    - `lstm`:
      - `forecast`
      - `metrics`: `rmse/mae/mape/r2`
  - `recommended_model` (string): recommended model based on **lowest RMSE**
  - `recommended_forecast` (list)

---

## Portfolio

> Portfolio stores user holdings in the database.

### GET `/portfolio`
Returns all holdings for the authenticated user.

**Auth**: `Authorization: Bearer <token>`

**Response**
- `200` JSON list of holdings:
  - `id`
  - `symbol`
  - `shares`
  - `avg_buy_price` (if tracked)
  - `current_price`
  - `current_value`
  - `profit_loss`

---

### POST `/portfolio`
Adds stock to portfolio.

**Auth** required

**Request body**
- `symbol` (string, required)
- `shares` (number, required)
- `avg_buy_price` (number, optional; if omitted it can be inferred from current quote)

**Response**
- `201` JSON updated/created holding

---

### PUT `/portfolio/{id}`
Updates a holding.

**Auth** required

**Path params**
- `id` (int)

**Request body**
- `shares` (number, optional)
- `avg_buy_price` (number, optional)

**Response**
- `200` JSON updated holding

---

### DELETE `/portfolio/{id}`
Removes a holding.

**Auth** required

**Path params**
- `id` (int)

**Response**
- `204` no content (recommended) or `200` JSON confirmation

---

## Watchlist

### GET `/watchlist`
Returns watchlist items for the authenticated user.

**Auth** required

**Response**
- `200` JSON list:
  - `id`
  - `symbol`
  - (optional) `added_at`

---

### POST `/watchlist`
Adds a symbol to watchlist.

**Auth** required

**Request body**
- `symbol` (string, required)

**Response**
- `201` JSON created watch item

---

### DELETE `/watchlist/{id}`
Removes from watchlist.

**Auth** required

**Path params**
- `id` (int)

**Response**
- `204` no content (recommended) or `200` JSON confirmation

---

## News

> News uses Finnhub API (default) and TextBlob sentiment.

### GET `/news/{symbol}`
Fetches recent headlines + sentiment classification.

**Path params**
- `symbol` (string)

**Query params (recommended)**
- `limit` (int, optional, default `10`)

**Response**
- `200` JSON:
  - `symbol`
  - `headlines`:
    - list of:
      - `headline`
      - `source` (if available)
      - `published_at` (if available)
      - `sentiment` (`positive|neutral|negative`)
      - `sentiment_score` (float)
  - `summary`:
    - `positive` (int)
    - `neutral` (int)
    - `negative` (int)
  - `overall_sentiment_score` (float)

---

## Dashboard

### GET `/dashboard`
Returns combined summary for the authenticated user.

**Auth** required

**Response**
- `200` JSON object:
  - `portfolio_summary`:
    - `portfolio_value`
    - `today_gain`
  - `prediction_summary`:
    - `best_model_accuracy` (example)
    - `recommended_model`
  - `news_sentiment`:
    - `positive/neutral/negative` breakdown
  - `watchlist`:
    - list of symbols
  - `market_overview`:
    - `most_active_stocks`
  - `recent_news`:
    - top headlines
  - `model_performance`:
    - metrics for linear vs lstm

---

## Recommended Implementation Structure (high-level)
- Routers: `routers/*`
- Services: `services/*`
- ML: `ml/*`
- Indicators: `services/indicator_service.py`
- News: `services/news_service.py`

No code changes should be made based on this document until the implementation phases begin.

