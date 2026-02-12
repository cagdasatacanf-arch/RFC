"""Markdown output engine."""

from __future__ import annotations

from pathlib import Path

from src.config import OUTPUT_DIR
from src.generator.assembler import render_report_markdown


def export_markdown(
    report: dict,
    company_profile: dict,
    output_dir: Path | None = None,
) -> Path:
    """Export a report to markdown format.

    Returns the path to the written file.
    """
    base_dir = output_dir or OUTPUT_DIR
    ticker = company_profile.get("metadata", {}).get("ticker", "UNKNOWN")
    report_date = report.get("report_date", "unknown")

    # Create company output directory
    company_dir = base_dir / ticker
    company_dir.mkdir(parents=True, exist_ok=True)

    # Render markdown
    content = render_report_markdown(report, company_profile)

    # Write file
    filename = f"{report_date}_report.md"
    output_path = company_dir / filename
    output_path.write_text(content, encoding="utf-8")

    return output_path
