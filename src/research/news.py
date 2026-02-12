"""News and article scanning module.

Phase 1: Placeholder for future web search integration.
Phase 2 will add automated web search via Claude API tool use.
"""

from __future__ import annotations


def get_recent_news(ticker: str, days: int = 90) -> list[dict]:
    """Fetch recent news for a company.

    Phase 1: Returns empty list (manual input).
    Phase 2: Will integrate web search.
    """
    # Placeholder for future implementation
    return []


def format_news_summary(articles: list[dict]) -> str:
    """Format news articles as a summary string."""
    if not articles:
        return "No recent news available. Consider adding manually."

    lines = []
    for article in articles:
        date = article.get("date", "Unknown date")
        title = article.get("title", "Untitled")
        source = article.get("source", "Unknown")
        lines.append(f"- [{date}] {title} ({source})")
    return "\n".join(lines)
