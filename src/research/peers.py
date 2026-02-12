"""Peer company discovery and comparison."""

from __future__ import annotations


def get_peers_from_framework(framework: dict) -> dict[str, list[str]]:
    """Extract peer groups defined in a sector framework."""
    overrides = framework.get("section_overrides", {})
    section_9 = overrides.get(9) or overrides.get("9") or {}
    return section_9.get("peer_groups", {})


def fetch_peer_data(tickers: list[str]) -> list[dict]:
    """Fetch basic comparison data for a list of peer tickers."""
    try:
        import yfinance as yf
    except ImportError:
        return [{"ticker": t, "error": "yfinance not installed"} for t in tickers]

    peers = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            peers.append({
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName", ticker),
                "market_cap": info.get("marketCap"),
                "pe_forward": info.get("forwardPE"),
                "ev_revenue": info.get("enterpriseToRevenue"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "gross_margin": info.get("grossMargins"),
                "revenue_growth": info.get("revenueGrowth"),
            })
        except Exception as e:
            peers.append({"ticker": ticker, "error": str(e)})
    return peers


def build_peer_comparison_table(peers: list[dict]) -> str:
    """Build a markdown peer comparison table."""
    if not peers:
        return "*No peer data available.*"

    headers = [
        "Ticker", "Name", "Mkt Cap ($B)", "Fwd P/E",
        "EV/Rev", "EV/EBITDA", "Gross Margin", "Rev Growth"
    ]
    rows = []
    for p in peers:
        if "error" in p:
            rows.append([p["ticker"], f"Error: {p['error']}"] + ["—"] * 6)
            continue
        rows.append([
            p.get("ticker", "—"),
            p.get("name", "—")[:25],
            _fmt_billions(p.get("market_cap")),
            _fmt_ratio(p.get("pe_forward")),
            _fmt_ratio(p.get("ev_revenue")),
            _fmt_ratio(p.get("ev_ebitda")),
            _fmt_pct(p.get("gross_margin")),
            _fmt_pct(p.get("revenue_growth")),
        ])

    # Build markdown table
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _fmt_billions(val) -> str:
    if val is None:
        return "—"
    return f"{val / 1e9:.1f}"


def _fmt_ratio(val) -> str:
    if val is None:
        return "—"
    return f"{val:.1f}x"


def _fmt_pct(val) -> str:
    if val is None:
        return "—"
    return f"{val * 100:.1f}%"
