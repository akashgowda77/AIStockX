"""
Stocks Router

Endpoints
---------
GET  /api/stocks/search
GET  /api/stocks/company/{symbol}
GET  /api/stocks/history/{symbol}
GET  /api/stocks/quote/{symbol}
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query

from ..services.stock_service import (
    get_company_info,
    get_current_price,
    get_historical_data,
    search_stock,
    validate_symbol,
)

router = APIRouter(
    prefix="/stocks",
    tags=["Stocks"],
)


# -------------------------------------------------------------------
# Common Response
# -------------------------------------------------------------------


def success_response(message: str, data: Any) -> Dict[str, Any]:
    """Standard API success response."""

    return {
        "success": True,
        "message": message,
        "data": data,
    }


# -------------------------------------------------------------------
# Search Stock
# -------------------------------------------------------------------


@router.get("/search")
def search(
    query: str = Query(..., min_length=1),
):
    """
    Search stock information.

    Example:
        /api/stocks/search?query=AAPL
    """

    try:
        validate_symbol(query)
        data = search_stock(query)

        return success_response(
            "Stock search successful",
            data,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# -------------------------------------------------------------------
# Company Information
# -------------------------------------------------------------------


@router.get("/company/{symbol}")
def company(symbol: str):
    """
    Fetch company profile.
    """

    try:
        validate_symbol(symbol)
        data = get_company_info(symbol)

        return success_response(
            "Company information fetched successfully",
            data,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# -------------------------------------------------------------------
# Historical Data
# -------------------------------------------------------------------


@router.get("/history/{symbol}")
def history(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
):
    """
    Fetch historical stock prices.
    """

    try:
        validate_symbol(symbol)

        history_data = get_historical_data(
            symbol=symbol,
            period=period,
            interval=interval,
        )

        return success_response(
            "Historical data fetched successfully",
            {
                "symbol": symbol.upper(),
                "period": period,
                "interval": interval,
                "rows": len(history_data),
                "history": history_data,
            },
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# -------------------------------------------------------------------
# Latest Quote
# -------------------------------------------------------------------


@router.get("/quote/{symbol}")
def quote(symbol: str):
    """
    Fetch latest market quote.
    """

    try:
        validate_symbol(symbol)

        data = get_current_price(symbol)

        return success_response(
            "Latest quote fetched successfully",
            data,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))