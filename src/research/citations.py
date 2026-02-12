"""Citation builder and manager."""

from __future__ import annotations

from datetime import datetime


CITATION_CATEGORIES = [
    "company_official",
    "financial_data",
    "news",
    "industry",
    "peer",
    "government",
]


def create_citation(
    url: str,
    title: str,
    publication: str | None = None,
    author: str | None = None,
    date_published: str | None = None,
    category: str = "news",
    subject: str = "",
    data_points: list[str] | None = None,
) -> dict:
    """Create a citation object."""
    return {
        "id": None,  # Assigned during report assembly
        "title": title,
        "publication": publication,
        "author": author,
        "date_published": date_published,
        "date_accessed": datetime.now().strftime("%Y-%m-%d"),
        "url": url,
        "category": category,
        "subject": subject,
        "data_points_extracted": data_points or [],
        "sections_cited_in": [],
    }


def assign_citation_ids(citations: list[dict]) -> list[dict]:
    """Assign sequential IDs to a list of citations."""
    for i, citation in enumerate(citations, start=1):
        citation["id"] = i
    return citations


def format_citation_reference(citation: dict) -> str:
    """Format a citation for the References section.

    Uses the format: [N] Title - Publication - erişim tarihi Month DD, YYYY, URL
    """
    cid = citation.get("id", "?")
    title = citation.get("title", "Unknown")
    publication = citation.get("publication", "")
    url = citation.get("url", "")
    accessed = citation.get("date_accessed", "")

    # Format access date in Turkish style
    access_str = ""
    if accessed:
        try:
            dt = datetime.strptime(accessed, "%Y-%m-%d")
            turkish_months = {
                1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
                5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
                9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık",
            }
            month = turkish_months[dt.month]
            access_str = f"erişim tarihi {month} {dt.day}, {dt.year}"
        except ValueError:
            access_str = f"accessed {accessed}"

    parts = [f"[{cid}]", title]
    if publication:
        parts.append(f"- {publication}")
    if access_str:
        parts.append(f"- {access_str}")
    if url:
        parts.append(f"- {url}")

    return " ".join(parts)


def format_references_section(citations: list[dict]) -> str:
    """Format the complete References section."""
    lines = ["## References", ""]
    for citation in sorted(citations, key=lambda c: c.get("id", 0)):
        lines.append(format_citation_reference(citation))
    return "\n".join(lines)


def validate_citations(content: str, citations: list[dict]) -> dict:
    """Validate citation usage in content.

    Returns dict with:
      - orphaned: citation IDs in text but not in reference list
      - uncited: citation IDs in reference list but not in text
      - sequential: whether numbering is sequential
    """
    import re

    # Find all [N] references in the text
    cited_ids = set()
    for match in re.finditer(r"\[(\d+)\]", content):
        cited_ids.add(int(match.group(1)))

    reference_ids = {c["id"] for c in citations if c.get("id") is not None}

    orphaned = cited_ids - reference_ids
    uncited = reference_ids - cited_ids

    # Check sequential numbering
    if reference_ids:
        expected = set(range(1, max(reference_ids) + 1))
        sequential = reference_ids == expected
    else:
        sequential = True

    return {
        "orphaned": sorted(orphaned),
        "uncited": sorted(uncited),
        "sequential": sequential,
        "total_citations": len(reference_ids),
        "total_cited": len(cited_ids),
    }
