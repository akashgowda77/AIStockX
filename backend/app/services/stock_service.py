from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests
from urllib.error import HTTPError

from ..config import settings
from ..utils.cache import ttl_cache

# =============================================================================
# Logger
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# Company Name to Ticker Mapping
# =============================================================================

_COMPANY_NAME_MAP = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    "amd": "AMD",
    "intel": "INTC",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "oracle": "ORCL",
    "ibm": "IBM",
    "cisco": "CSCO",
    "qualcomm": "QCOM",
    "broadcom": "AVGO",
    "texas instruments": "TXN",
    "ti": "TXN",
    "micron": "MU",
    "advanced micro devices": "AMD",
    "berkshire hathaway": "BRK-B",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "walmart": "WMT",
    "disney": "DIS",
    "coca cola": "KO",
    "coca-cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    "nike": "NKE",
    "starbucks": "SBUX",
    "mcdonalds": "MCD",
    "mcdonald's": "MCD",
    "ford": "F",
    "general motors": "GM",
    "gm": "GM",
    "uber": "UBER",
    "lyft": "LYFT",
    "palantir": "PLTR",
    "coinbase": "COIN",
    "robinhood": "HOOD",
    "zoom": "ZM",
    "spotify": "SPOT",
    "airbnb": "ABNB",
    "booking": "BKNG",
    "paypal": "PYPL",
    "shopify": "SHOP",
    "square": "SQ",
    "block": "SQ",
    "twitter": "TWTR",
    "x": "TWTR",
    "snap": "SNAP",
    "snapchat": "SNAP",
    "pinterest": "PINS",
    "linkedin": "MSFT",
    "youtube": "GOOGL",
    "tiktok": "BDNCE",
    "bytedance": "BDNCE",
    "tencent": "TCEHY",
    "alibaba": "BABA",
    "baidu": "BIDU",
    "jd.com": "JD",
    "jd": "JD",
    "shopee": "SE",
    "sea limited": "SE",
    "samsung": "SSNLF",
    "sony": "SONY",
    "toyota": "TM",
    "honda": "HMC",
    "nestle": "NSRGF",
    "novartis": "NVS",
    "roche": "RHHBY",
    "pfizer": "PFE",
    "johnson & johnson": "JNJ",
    "jnj": "JNJ",
    "merck": "MRK",
    "abbvie": "ABBV",
    "moderna": "MRNA",
    "biontech": "BNTX",
    "gilead": "GILD",
    "regeneron": "REGN",
}

# =============================================================================
# Helper Functions
# =============================================================================


def validate_symbol(symbol: str) -> str:
    """
    Validate and normalize a stock symbol.

    Examples:
        AAPL
        MSFT
        IBM
        TSLA
    """

    if symbol is None or not symbol.strip():
        raise ValueError("Stock symbol is required.")

    symbol = symbol.strip().upper()

    if not re.fullmatch(r"[A-Z0-9.\-]{1,20}", symbol):
        raise ValueError(f"Invalid stock symbol: {symbol}")

    return symbol


def _safe_float(value: Any) -> float | None:
    """
    Convert a value to float safely.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    """
    Convert a value to int safely.
    """

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _normalize_company_name(name: str) -> str:
    """
    Normalize a company name for lookup in the internal map.
    """
    return name.strip().lower()


def _finnhub_request(endpoint: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Make a request to Finnhub API with error handling.
    """
    api_key = settings.finnhub_api_key
    
    if api_key == "change_me" or not api_key:
        raise ValueError("Finnhub API key not configured.")
    
    base_url = "https://finnhub.io/api/v1"
    url = f"{base_url}/{endpoint}"
    
    request_params = params or {}
    request_params["token"] = api_key
    
    try:
        response = requests.get(url, params=request_params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error("Finnhub API timeout for endpoint: %s", endpoint)
        raise ValueError("API request timeout. Please try again.")
    except requests.exceptions.ConnectionError:
        logger.error("Finnhub API connection error for endpoint: %s", endpoint)
        raise ValueError("Unable to connect to data provider. Please try again.")
    except requests.exceptions.HTTPError as exc:
        logger.error("Finnhub API HTTP error for endpoint %s: %s", endpoint, exc)
        if exc.response.status_code == 429:
            raise ValueError("Rate limit exceeded. Please try again later.")
        raise ValueError("API request failed. Please try again.")
    except Exception as exc:
        logger.error("Finnhub API unexpected error for endpoint %s: %s", endpoint, exc)
        raise ValueError("Unexpected error occurred. Please try again.")


# =============================================================================
# Stock Search
# =============================================================================

@ttl_cache(ttl_seconds=300)
def search_stock(query: str) -> Dict[str, Any]:
    """
    Search stock information using Finnhub Symbol Lookup endpoint.

    Supports ticker search and company name search.
    """

    symbol = validate_symbol(query)

    logger.info("Searching stock: %s", symbol)

    try:
        # Use Finnhub Symbol Lookup endpoint
        data = _finnhub_request("search", {"q": symbol})
        
        # Check if we got results
        if data and data.get("count", 0) > 0:
            # Find the best match
            results = data.get("result", [])
            for result in results:
                if result.get("symbol", "").upper() == symbol:
                    return {
                        "symbol": result.get("symbol", symbol),
                        "name": result.get("description", symbol),
                        "exchange": result.get("exchange", "NASDAQ"),
                        "currency": "USD",
                    }
            
            # If no exact match, return first result
            first_result = results[0]
            return {
                "symbol": first_result.get("symbol", symbol),
                "name": first_result.get("description", symbol),
                "exchange": first_result.get("exchange", "NASDAQ"),
                "currency": "USD",
            }
        
        # If no results from Finnhub, return basic info
        return {
            "symbol": symbol,
            "name": symbol,
            "exchange": None,
            "currency": "USD",
        }
        
    except ValueError:
        raise
    except Exception as exc:
        logger.error("Failed to search stock %s: %s", symbol, exc)
        raise ValueError(f"Search failed for '{symbol}'.") from exc


# =============================================================================
# Company Information
# =============================================================================

@ttl_cache(ttl_seconds=172800)  # 48 hours
def get_company_info(symbol: str) -> Dict[str, Any]:
    """
    Fetch company overview using Finnhub Company Profile endpoint.

    Cached for 48 hours because company information changes infrequently.
    """

    symbol = validate_symbol(symbol)

    logger.info("Fetching company overview: %s", symbol)

    try:
        # Use Finnhub Company Profile endpoint
        data = _finnhub_request("stock/profile2", {"symbol": symbol})
        
        logger.info("Finnhub profile2 response for %s: %s", symbol, data)
        
        # Check if we got valid data - Finnhub returns empty dict or dict with empty values for invalid symbols
        if not data or data.get("ticker") is None:
            raise ValueError(f"No company info available for '{symbol}'.")
        
        return {
            "symbol": symbol,
            "name": data.get("name") or symbol,
            "sector": data.get("finnhubIndustry"),
            "industry": data.get("finnhubIndustry"),
            "website": data.get("weburl"),
            "country": data.get("country"),
            "currency": data.get("currency") or "USD",
            "exchange": data.get("exchange"),
            "market_cap": _safe_int(data.get("marketCapitalization")),
            "description": None,  # Finnhub doesn't provide description in profile2
            "pe_ratio": None,  # Not available in profile2
            "eps": None,  # Not available in profile2
            "dividend_yield": None,  # Not available in profile2
            "book_value": None,  # Not available in profile2
            "52_week_high": None,  # Not available in profile2
            "52_week_low": None,  # Not available in profile2
        }
        
    except ValueError:
        raise
    except Exception as exc:
        logger.error("Failed to fetch company info for %s: %s", symbol, exc)
        raise ValueError(f"No company info available for '{symbol}'.") from exc


# =============================================================================
# Historical Market Data
# =============================================================================

@ttl_cache(ttl_seconds=86400)  # 24 hours
def get_historical_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> List[Dict[str, Any]]:
    """
    Fetch historical OHLCV data using Alpha Vantage TIME_SERIES_DAILY endpoint.

    Returns
    -------
    List[Dict]
        [
            {
                "date": "...",
                "open": ...,
                "high": ...,
                "low": ...,
                "close": ...,
                "volume": ...
            }
        ]
    """

    symbol = validate_symbol(symbol)

    logger.info(
        "Downloading historical data | Symbol=%s | Period=%s | Interval=%s",
        symbol,
        period,
        interval,
    )

    try:
        # Use Alpha Vantage TIME_SERIES_DAILY endpoint
        api_key = settings.alpha_vantage_api_key
        
        if not api_key or api_key == "change_me":
            raise ValueError("Alpha Vantage API key not configured.")
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": api_key,
            "outputsize": "full" if period in ["2y", "5y"] else "compact",
        }
        
        logger.info("Fetching from Alpha Vantage: %s", url)
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Error Message" in data:
            raise ValueError(f"Invalid symbol: {symbol}")
        
        if "Note" in data:
            raise ValueError("API call frequency limit reached. Please try again later.")
        
        # Extract time series data
        time_series_key = "Time Series (Daily)"
        if time_series_key not in data:
            raise ValueError(f"No historical data found for '{symbol}'.")
        
        time_series = data[time_series_key]
        
        # Convert to list of records
        records: List[Dict[str, Any]] = []
        
        for date_str, values in time_series.items():
            records.append({
                "date": date_str,
                "open": _safe_float(values.get("1. open")),
                "high": _safe_float(values.get("2. high")),
                "low": _safe_float(values.get("3. low")),
                "close": _safe_float(values.get("4. close")),
                "volume": _safe_int(values.get("5. volume")),
            })
        
        # Sort by date (newest first from API, we want oldest first)
        records.sort(key=lambda x: x["date"])
        
        # Limit records based on period
        if period == "1d":
            records = records[-1:]
        elif period == "5d":
            records = records[-5:]
        elif period == "1mo":
            records = records[-30:]
        elif period == "3mo":
            records = records[-90:]
        elif period == "6mo":
            records = records[-180:]
        elif period == "1y":
            records = records[-365:]
        elif period == "2y":
            records = records[-730:]
        elif period == "5y":
            records = records[-1825:]
        
        logger.info(
            "Downloaded %d historical records for %s",
            len(records),
            symbol,
        )

        return records

    except ValueError:
        raise
    except Exception as exc:
        import traceback

        print("=" * 80)
        print("HISTORICAL DATA ERROR")
        traceback.print_exc()
        print("=" * 80)

        raise


# =============================================================================
# Current Market Quote
# =============================================================================

@ttl_cache(ttl_seconds=30)  # 30 seconds
def get_current_price(symbol: str) -> Dict[str, Any]:
    """
    Fetch the latest stock quote using Finnhub Quote endpoint.

    Returns
    -------
    Dict[str, Any]
        {
            symbol,
            price,
            previous_close,
            open,
            day_high,
            day_low,
            volume,
            change,
            percent_change,
            currency,
            exchange,
            market_state
        }
    """

    symbol = validate_symbol(symbol)

    logger.info("Fetching latest quote: %s", symbol)

    try:
        # Use Finnhub Quote endpoint
        data = _finnhub_request("quote", {"symbol": symbol})
        
        current_price = _safe_float(data.get("c"))
        previous_close = _safe_float(data.get("pc"))
        open_price = _safe_float(data.get("o"))
        day_high = _safe_float(data.get("h"))
        day_low = _safe_float(data.get("l"))
        volume = None  # Finnhub quote doesn't provide volume
        
        if current_price is None:
            raise ValueError(f"Market price unavailable for '{symbol}'.")
        
        # Calculate change
        change = None
        percent_change = None
        
        if previous_close is not None and previous_close != 0:
            change = current_price - previous_close
            percent_change = (change / previous_close) * 100
        
        return {
            "symbol": symbol,
            "price": current_price,
            "previous_close": previous_close,
            "open": open_price,
            "day_high": day_high,
            "day_low": day_low,
            "volume": volume,
            "change": change,
            "percent_change": percent_change,
            "currency": "USD",
            "exchange": None,
            "market_state": "OPEN" if current_price is not None else "CLOSED",
        }

    except ValueError:
        raise
    except Exception as exc:
        logger.error("Failed to fetch quote for %s: %s", symbol, exc)
        raise ValueError(f"Market price unavailable for '{symbol}'.") from exc