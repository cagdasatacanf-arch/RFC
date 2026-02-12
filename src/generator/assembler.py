"""Report assembly - combines sections into a complete report."""

from __future__ import annotations

from datetime import datetime

from src.db import generate_id, save_report
from src.research.citations import assign_citation_ids, format_references_section


def assemble_report(
    sections: list[dict],
    company_profile: dict,
    framework: dict,
    citations: list[dict] | None = None,
) -> dict:
    """Assemble generated sections into a complete report.

    Args:
        sections: List of section result dicts from the writer.
        company_profile: The company profile.
        framework: The effective framework used.
        citations: List of citation objects.

    Returns:
        A complete report dict ready for storage and export.
    """
    meta = company_profile.get("metadata", {})
    if citations:
        citations = assign_citation_ids(citations)

    total_words = sum(s.get("word_count", 0) for s in sections)
    all_generated = all(s.get("status") == "generated" for s in sections)

    report = {
        "id": generate_id(),
        "company_id": company_profile.get("id", ""),
        "framework_id": framework.get("sector_id", ""),
        "status": "complete" if all_generated else "draft",
        "report_date": meta.get("report_date", datetime.now().strftime("%Y-%m-%d")),
        "reference_quarter": meta.get("reference_quarter", ""),
        "sections": sections,
        "citations": citations or [],
        "qa_results": None,
        "word_count": total_words,
        "output_paths": {},
    }

    return report


def render_report_markdown(report: dict, company_profile: dict) -> str:
    """Render a report as a complete markdown document."""
    meta = company_profile.get("metadata", {})
    lines = [
        f"# {meta.get('name', '?')} ({meta.get('ticker', '?')}) — Investment Analysis",
        "",
        f"**Report Date:** {report.get('report_date', '?')}",
        f"**Reference Quarter:** {report.get('reference_quarter', '?')}",
        f"**Framework:** {report.get('framework_id', '?')}",
        "",
        "---",
        "",
    ]

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for section in report.get("sections", []):
        sid = section.get("section_id", "?")
        name = section.get("name", f"Section {sid}")
        lines.append(f"{sid}. [{name}](#{_slugify(name)})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Sections
    for section in report.get("sections", []):
        name = section.get("name", f"Section {section.get('section_id', '?')}")
        content = section.get("content", "")
        word_count = section.get("word_count", 0)
        status = section.get("status", "unknown")

        if status == "error":
            error = section.get("error", "Unknown error")
            lines.append(f"## {name}")
            lines.append("")
            lines.append(f"> **Generation Error:** {error}")
            lines.append("")
        elif content:
            # If content already has a header, use it as-is
            if content.strip().startswith("#"):
                lines.append(content)
            else:
                lines.append(f"## {name}")
                lines.append("")
                lines.append(content)
            lines.append("")
            lines.append(f"*[{word_count} words]*")
            lines.append("")
        lines.append("---")
        lines.append("")

    # References
    citations = report.get("citations", [])
    if citations:
        lines.append(format_references_section(citations))
        lines.append("")

    # Footer
    lines.extend([
        "---",
        "",
        f"*Report generated on {report.get('report_date', '?')} "
        f"using the Investment Report Framework Creator.*",
        f"*Total word count: {report.get('word_count', 0):,}*",
    ])

    return "\n".join(lines)


def save_assembled_report(report: dict) -> str:
    """Save an assembled report to the database."""
    return save_report(report)


def _slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    return text.lower().replace(" ", "-").replace("&", "and").replace("/", "-")
