"""HTML export engine (Phase 3 - stub)."""

from __future__ import annotations

from pathlib import Path


def export_html(report: dict, company_profile: dict, output_dir: Path | None = None) -> Path:
    """Export a report to HTML format.

    Phase 3 implementation. Currently raises NotImplementedError.
    """
    raise NotImplementedError(
        "HTML export is planned for Phase 3. "
        "Use markdown export for now: irf report export <ticker> --format md"
    )
