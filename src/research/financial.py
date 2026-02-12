"""Financial data fetching module."""

from __future__ import annotations


def fetch_company_info(ticker: str) -> dict:
    """Fetch basic company information using yfinance.

    Returns a dict with company metadata and basic financials.
    Falls back gracefully if yfinance is unavailable.
    """
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed. Run: pip install yfinance"}

    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
    except Exception as e:
        return {"error": f"Failed to fetch data for {ticker}: {e}"}

    return {
        "metadata": {
            "name": info.get("longName") or info.get("shortName", ticker),
            "ticker": ticker.upper(),
            "exchange": info.get("exchange", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "website": info.get("website", ""),
            "currency": info.get("currency", "USD"),
        },
        "financials": {
            "market_cap": info.get("marketCap"),
            "revenue": info.get("totalRevenue"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "profit_margin": info.get("profitMargins"),
            "eps_trailing": info.get("trailingEps"),
            "eps_forward": info.get("forwardEps"),
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "ev_revenue": info.get("enterpriseToRevenue"),
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "fcf": info.get("freeCashflow"),
            "total_cash": info.get("totalCash"),
            "total_debt": info.get("totalDebt"),
        },
        "price": {
            "current": info.get("currentPrice") or info.get("regularMarketPrice"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
        },
    }


def fetch_financials_table(ticker: str) -> dict:
    """Fetch income statement, balance sheet, and cash flow data."""
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not installed"}

    try:
        stock = yf.Ticker(ticker)
        result = {}

        income = stock.quarterly_income_stmt
        if income is not None and not income.empty:
            result["income_statement"] = {
                str(col.date()): {
                    str(idx): _safe_number(income.at[idx, col])
                    for idx in income.index
                }
                for col in income.columns[:4]  # Last 4 quarters
            }

        bs = stock.quarterly_balance_sheet
        if bs is not None and not bs.empty:
            result["balance_sheet"] = {
                str(col.date()): {
                    str(idx): _safe_number(bs.at[idx, col])
                    for idx in bs.index
                }
                for col in bs.columns[:4]
            }

        cf = stock.quarterly_cashflow
        if cf is not None and not cf.empty:
            result["cash_flow"] = {
                str(col.date()): {
                    str(idx): _safe_number(cf.at[idx, col])
                    for idx in cf.index
                }
                for col in cf.columns[:4]
            }

        return result

    except Exception as e:
        return {"error": f"Failed to fetch financials for {ticker}: {e}"}


def _safe_number(val) -> float | None:
    """Convert a value to float, returning None for NaN/None."""
    if val is None:
        return None
    try:
        import math
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None
