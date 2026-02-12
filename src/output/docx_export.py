"""DOCX export engine (Phase 3 - stub)."""

from __future__ import annotations

from pathlib import Path


def export_docx(report: dict, company_profile: dict, output_dir: Path | None = None) -> Path:
    """Export a report to DOCX format.

    Phase 3 implementation. Currently raises NotImplementedError.
    """
    raise NotImplementedError(
        "DOCX export is planned for Phase 3. "
        "Use markdown export for now: irf report export <ticker> --format md"
    )
