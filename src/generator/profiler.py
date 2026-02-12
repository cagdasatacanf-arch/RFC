"""Company profiler - builds structured company profiles for report generation."""

from __future__ import annotations

from datetime import datetime

from src.db import generate_id, save_company
from src.research.financial import fetch_company_info


def create_company_profile(
    ticker: str,
    name: str | None = None,
    exchange: str | None = None,
    sector_framework: str | None = None,
    reference_quarter: str | None = None,
    auto_fetch: bool = True,
) -> dict:
    """Create a company profile, optionally fetching financial data.

    Returns a complete company profile dict ready for report generation.
    """
    profile = {
        "id": generate_id(),
        "metadata": {
            "name": name or ticker,
            "ticker": ticker.upper(),
            "exchange": exchange or "",
            "sector_framework": sector_framework or "",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "reference_quarter": reference_quarter or "",
            "currency": "USD",
        },
        "financials": {
            "revenue": {"current": None, "prior_year": None, "yoy_pct": None},
            "gross_margin": {"current": None, "prior_year": None},
            "operating_margin": {"current": None, "prior_year": None},
            "r_and_d_pct": None,
            "eps": {"gaap": None, "non_gaap": None},
            "fcf": None,
            "segment_breakdown": {},
        },
        "operational": {
            "primary_segment": None,
            "products": [],
            "customers": [],
            "design_wins": [],
            "foundry": None,
        },
        "valuation": {
            "market_cap": None,
            "ev_sales": None,
            "pe_forward": None,
            "p_fcf": None,
            "peers": [],
        },
        "catalysts": [],
        "risks": [],
        "sources": [],
    }

    if auto_fetch:
        fetched = fetch_company_info(ticker)
        if "error" not in fetched:
            _merge_fetched_data(profile, fetched)

    return profile


def _merge_fetched_data(profile: dict, fetched: dict) -> None:
    """Merge fetched financial data into the profile."""
    meta = fetched.get("metadata", {})
    if meta.get("name"):
        profile["metadata"]["name"] = meta["name"]
    if meta.get("exchange"):
        profile["metadata"]["exchange"] = meta["exchange"]
    if meta.get("currency"):
        profile["metadata"]["currency"] = meta["currency"]

    fin = fetched.get("financials", {})
    if fin.get("revenue"):
        profile["financials"]["revenue"]["current"] = fin["revenue"]
    if fin.get("gross_margin") is not None:
        profile["financials"]["gross_margin"]["current"] = fin["gross_margin"]
    if fin.get("operating_margin") is not None:
        profile["financials"]["operating_margin"]["current"] = fin["operating_margin"]
    if fin.get("fcf") is not None:
        profile["financials"]["fcf"] = fin["fcf"]
    if fin.get("eps_trailing") is not None:
        profile["financials"]["eps"]["gaap"] = fin["eps_trailing"]
    if fin.get("eps_forward") is not None:
        profile["financials"]["eps"]["non_gaap"] = fin["eps_forward"]

    if fin.get("market_cap"):
        profile["valuation"]["market_cap"] = fin["market_cap"]
    if fin.get("pe_forward"):
        profile["valuation"]["pe_forward"] = fin["pe_forward"]
    if fin.get("ev_revenue"):
        profile["valuation"]["ev_sales"] = fin["ev_revenue"]


def save_company_profile(profile: dict) -> str:
    """Save a company profile to the database."""
    return save_company(profile)


def format_profile_summary(profile: dict) -> str:
    """Format a company profile as a human-readable summary."""
    meta = profile.get("metadata", {})
    fin = profile.get("financials", {})
    val = profile.get("valuation", {})

    lines = [
        f"**{meta.get('name', '?')}** ({meta.get('ticker', '?')})",
        f"Exchange: {meta.get('exchange', '?')} | Framework: {meta.get('sector_framework', '?')}",
        f"Report Date: {meta.get('report_date', '?')} | Quarter: {meta.get('reference_quarter', '?')}",
        "",
        "**Financials:**",
        f"  Revenue: {_fmt_currency(fin.get('revenue', {}).get('current'))}",
        f"  Gross Margin: {_fmt_pct(fin.get('gross_margin', {}).get('current'))}",
        f"  Operating Margin: {_fmt_pct(fin.get('operating_margin', {}).get('current'))}",
        f"  FCF: {_fmt_currency(fin.get('fcf'))}",
        "",
        "**Valuation:**",
        f"  Market Cap: {_fmt_currency(val.get('market_cap'))}",
        f"  EV/Sales: {_fmt_ratio(val.get('ev_sales'))}",
        f"  Fwd P/E: {_fmt_ratio(val.get('pe_forward'))}",
    ]
    return "\n".join(lines)


def _fmt_currency(val) -> str:
    if val is None:
        return "—"
    if abs(val) >= 1e9:
        return f"${val / 1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"${val / 1e6:.1f}M"
    return f"${val:,.0f}"


def _fmt_pct(val) -> str:
    if val is None:
        return "—"
    return f"{val * 100:.1f}%"


def _fmt_ratio(val) -> str:
    if val is None:
        return "—"
    return f"{val:.1f}x"
