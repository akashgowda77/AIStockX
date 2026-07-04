# 📈 AIStockX

> **An AI-Powered Stock Market Analysis & Prediction Platform**

AIStockX is a full-stack machine learning application that enables investors and learners to analyze stocks using technical indicators, real-time market data, and multiple AI prediction models.

The platform combines **financial analytics**, **technical analysis**, and **machine learning** to forecast stock prices while comparing model performance through an intelligent AI scoring system.

---

## 🚀 Features

### 📊 Stock Analysis

- Search stocks by ticker symbol
- Company profile and overview
- Live market quote
- Historical price data
- Alpha Vantage API integration

---

### 📈 Technical Indicators

AIStockX automatically computes multiple technical indicators including:

- Moving Average (SMA)
- Exponential Moving Average (EMA)
- RSI (Relative Strength Index)
- MACD
- Bollinger Bands
- ATR
- OBV
- Stochastic Oscillator

---

### 🤖 AI Prediction Models

Currently supported models:

- ✅ Linear Regression
- ✅ Long Short-Term Memory (LSTM)

Each model provides:

- Next-day closing price prediction
- Prediction confidence
- Error estimation
- Performance metrics

---

### 🏆 Intelligent Model Comparison

One of the core highlights of AIStockX.

Features include:

- AI Score (0–100)
- Leaderboard ranking
- Metric-wise winner detection
- Strengths & Weaknesses analysis
- Prediction comparison
- Radar chart visualization
- Error metrics comparison
- AI recommendation engine
- Model metadata

Instead of simply displaying metrics, AIStockX recommends the most suitable prediction model using a weighted scoring algorithm.

---

### 📉 Model Evaluation

Evaluate trained models using:

- Prediction Accuracy
- RMSE
- MAE
- MAPE
- Direction Accuracy
- R² Score
- Confidence Score

---

### 🔐 Authentication

- User Registration
- Login
- JWT Authentication
- Protected APIs
- Password hashing using bcrypt

---

## 🖥️ Dashboard

The dashboard provides:

- Clean modern interface
- Company information
- Market statistics
- Technical analysis
- Prediction results
- Model comparison
- Interactive charts

---

# 🧠 AI Scoring System

AIStockX introduces an intelligent scoring mechanism to compare prediction models.

Instead of comparing only one metric, the platform combines multiple evaluation metrics into a weighted AI Score.

| Metric              | Weight |
| ------------------- | ------ |
| Prediction Accuracy | 30%    |
| RMSE                | 20%    |
| MAE                 | 15%    |
| MAPE                | 10%    |
| Direction Accuracy  | 10%    |
| R² Score            | 10%    |
| Confidence Score    | 5%     |

This produces a realistic score that helps recommend the best-performing model.

---

# 🛠 Tech Stack

## Frontend

- HTML5
- CSS3
- JavaScript (ES6)
- Chart.js
- Font Awesome

---

## Backend

- FastAPI
- Python
- SQLAlchemy
- JWT Authentication
- Passlib
- Pydantic

---

## Machine Learning

- Scikit-Learn
- TensorFlow / Keras
- NumPy
- Pandas

---

## APIs

- Alpha Vantage API

---

## Database

- SQLite

---

# 📂 Project Structure

```
AIStockX/

│

├── backend/

│ ├── app/

│ │ ├── ml/

│ │ ├── routers/

│ │ ├── services/

│ │ ├── models/

│ │ ├── database/

│ │ ├── auth/

│ │ └── main.py

│

├── frontend/

│ ├── css/

│ ├── js/

│ ├── dashboard.html

│ ├── stock.html

│ ├── prediction.html

│ └── comparison.html

│

├── requirements.txt

└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/<your-username>/AIStockX.git

cd AIStockX
```

---

## Backend Setup

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file inside the backend directory.

```
ALPHA_VANTAGE_API_KEY=YOUR_API_KEY

SECRET_KEY=YOUR_SECRET_KEY
```

---

## Run Backend

```bash
uvicorn app.main:app --reload
```

Backend:

```
http://127.0.0.1:8000
```

Swagger Documentation:

```
http://127.0.0.1:8000/docs
```

---

## Run Frontend

Simply open

```
frontend/dashboard.html
```

using Live Server or any static web server.

---

# 📊 Supported ML Metrics

- Prediction Accuracy
- RMSE
- MAE
- MAPE
- Direction Accuracy
- Confidence Score
- R² Score

---

# 📈 Future Improvements

- Random Forest
- XGBoost
- Prophet
- ARIMA
- Transformer Models
- Portfolio Optimization
- Sentiment Analysis
- News-based Prediction
- Candlestick Pattern Recognition
- Watchlist
- Email Alerts
- Paper Trading
- Docker Deployment

---

# 🎯 Learning Outcomes

This project demonstrates practical experience with:

- Machine Learning
- Time Series Forecasting
- Deep Learning (LSTM)
- REST API Development
- FastAPI
- Frontend Development
- Authentication
- Data Engineering
- Financial Analytics
- Technical Indicators
- Data Visualization
- Software Architecture

---

# 🤝 Contributing

Contributions, suggestions, and feature requests are welcome.

Fork the repository, create a feature branch, and submit a Pull Request.

---

# 📜 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Akash Gowda S**

Computer Science Engineering Student

⭐ If you found this project useful, consider giving it a star!
