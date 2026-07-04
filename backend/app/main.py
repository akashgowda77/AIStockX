from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

app = FastAPI(title="AIStockX Backend")

# CORS (frontend -> backend)
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint used by dev tooling and load balancers."""

    return {"status": "ok"}


# Create DB tables on startup (dev convenience)
from .database import Base, engine
from .models.user import User  # noqa: F401


@app.on_event("startup")
def on_startup():
    """Create DB tables.

    Input: none
    Output: None

    Note: For a college project, this avoids Alembic setup during early development.
    """

    Base.metadata.create_all(bind=engine)


from .routers.auth import router as auth_router
from .routers.stocks import router as stocks_router
from .routers.indicators import router as indicators_router
from .routers.prediction import router as prediction_router
from .routers.model_evaluation import router as model_evaluation_router
from .routers.prediction_lstm import router as prediction_lstm_router

# Router registration

app.include_router(auth_router, prefix="/api/auth")
app.include_router(stocks_router)
app.include_router(indicators_router)
app.include_router(prediction_router, prefix="/api")
app.include_router(model_evaluation_router)
app.include_router(prediction_lstm_router)








