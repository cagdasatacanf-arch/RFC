"""Quality assurance engine for generated reports."""

from __future__ import annotations

import re

from src.research.citations import validate_citations


HYPE_WORDS = [
    "massive", "incredible", "game-changing", "revolutionary",
    "unprecedented", "explosive", "skyrocket", "moonshot",
    "disruptive", "phenomenal", "extraordinary", "jaw-dropping",
]

FIRST_PERSON_PATTERNS = [
    r"\bI\b", r"\bwe\b", r"\bour\b", r"\bmy\b", r"\bus\b",
]


def run_qa_checks(report: dict) -> dict:
    """Run all QA checks on a report.

    Returns a dict with check results organized by category.
    """
    sections = report.get("sections", [])
    citations = report.get("citations", [])

    # Combine all section content
    full_content = "\n\n".join(
        s.get("content", "") for s in sections if s.get("status") == "generated"
    )

    results = {
        "structure": _check_structure(sections, report),
        "citations": _check_citations(full_content, citations),
        "content": _check_content(full_content, sections),
        "tone": _check_tone(full_content),
        "overall_pass": True,
        "warnings": [],
        "errors": [],
    }

    # Aggregate pass/fail
    for category in ("structure", "citations", "content", "tone"):
        checks = results[category]
        for check_name, check_result in checks.items():
            if isinstance(check_result, dict):
                if not check_result.get("pass", True):
                    results["overall_pass"] = False
                    level = check_result.get("level", "warning")
                    msg = f"[{category}.{check_name}] {check_result.get('message', 'Failed')}"
                    if level == "error":
                        results["errors"].append(msg)
                    else:
                        results["warnings"].append(msg)

    return results


def _check_structure(sections: list[dict], report: dict) -> dict:
    """Check structural requirements."""
    checks = {}

    # All 11 sections present
    section_ids = {s.get("section_id") for s in sections}
    expected = set(range(1, 12))
    missing = expected - section_ids
    checks["all_11_sections_present"] = {
        "pass": len(missing) == 0,
        "message": f"Missing sections: {sorted(missing)}" if missing else "All 11 sections present",
        "level": "error",
    }

    # Section word counts in range
    word_issues = []
    for s in sections:
        wc = s.get("word_count", 0)
        sid = s.get("section_id", "?")
        if s.get("status") != "generated":
            word_issues.append(f"Section {sid}: not generated")
    checks["section_generation_status"] = {
        "pass": len(word_issues) == 0,
        "message": "; ".join(word_issues) if word_issues else "All sections generated",
        "level": "error" if word_issues else "info",
    }

    # Total word count
    total = report.get("word_count", 0)
    checks["total_word_count"] = {
        "pass": 8000 <= total <= 10000,
        "message": f"Total: {total:,} words (target: 8,000–10,000)",
        "level": "warning",
        "value": total,
    }

    # Tables present
    full_content = "\n".join(s.get("content", "") for s in sections)
    table_count = len(re.findall(r"^\|.+\|$", full_content, re.MULTILINE))
    # Rough estimate: count header rows as tables
    table_sections = table_count // 2  # header + separator = 1 table
    checks["tables_present"] = {
        "pass": 2 <= table_sections <= 10,
        "message": f"~{table_sections} tables found (target: 2–4 minimum)",
        "level": "warning",
        "value": table_sections,
    }

    return checks


def _check_citations(full_content: str, citations: list[dict]) -> dict:
    """Check citation requirements."""
    validation = validate_citations(full_content, citations)

    checks = {}

    checks["total_count"] = {
        "pass": 25 <= validation["total_citations"] <= 40,
        "message": f"{validation['total_citations']} citations (target: 25–40)",
        "level": "warning",
        "value": validation["total_citations"],
    }

    checks["no_orphaned"] = {
        "pass": len(validation["orphaned"]) == 0,
        "message": (
            f"Orphaned citation IDs in text: {validation['orphaned']}"
            if validation["orphaned"]
            else "No orphaned citations"
        ),
        "level": "error",
    }

    checks["no_uncited"] = {
        "pass": len(validation["uncited"]) == 0,
        "message": (
            f"Uncited references: {validation['uncited']}"
            if validation["uncited"]
            else "All references cited"
        ),
        "level": "warning",
    }

    checks["sequential_numbering"] = {
        "pass": validation["sequential"],
        "message": "Sequential" if validation["sequential"] else "Non-sequential numbering",
        "level": "warning",
    }

    return checks


def _check_content(full_content: str, sections: list[dict]) -> dict:
    """Check content quality requirements."""
    checks = {}

    # Check for specific metrics (numbers, percentages, dollar amounts)
    numbers = re.findall(r"\$[\d,.]+[BMK]?|\d+\.?\d*%|\d{1,3}(?:,\d{3})+", full_content)
    checks["specific_metrics_present"] = {
        "pass": len(numbers) >= 10,
        "message": f"{len(numbers)} specific metrics found (target: 10+)",
        "level": "warning",
        "value": len(numbers),
    }

    # Check for peer comparison table (section 9)
    section_9 = next((s for s in sections if s.get("section_id") == 9), None)
    if section_9:
        has_table = bool(re.search(r"^\|.+\|$", section_9.get("content", ""), re.MULTILINE))
        checks["peer_comparison_table"] = {
            "pass": has_table,
            "message": "Peer table present" if has_table else "Missing peer comparison table",
            "level": "warning",
        }

    # Check for financial table (section 7)
    section_7 = next((s for s in sections if s.get("section_id") == 7), None)
    if section_7:
        has_table = bool(re.search(r"^\|.+\|$", section_7.get("content", ""), re.MULTILINE))
        checks["financial_table"] = {
            "pass": has_table,
            "message": "Financial table present" if has_table else "Missing financial table",
            "level": "warning",
        }

    # Check for risk probability/impact (section 10)
    section_10 = next((s for s in sections if s.get("section_id") == 10), None)
    if section_10:
        content = section_10.get("content", "").lower()
        has_risk_framework = (
            "probability" in content or "likelihood" in content or "impact" in content
        )
        checks["risk_probability_impact"] = {
            "pass": has_risk_framework,
            "message": (
                "Risk framework present"
                if has_risk_framework
                else "Missing probability/impact assessment"
            ),
            "level": "warning",
        }

    return checks


def _check_tone(full_content: str) -> dict:
    """Check tone and style requirements."""
    checks = {}

    # No hype language
    found_hype = []
    content_lower = full_content.lower()
    for word in HYPE_WORDS:
        if word in content_lower:
            found_hype.append(word)
    checks["no_hype_language"] = {
        "pass": len(found_hype) == 0,
        "message": (
            f"Hype words found: {', '.join(found_hype)}"
            if found_hype
            else "No hype language detected"
        ),
        "level": "warning",
    }

    # No first person
    found_first_person = False
    for pattern in FIRST_PERSON_PATTERNS:
        # Check with word boundaries, case-insensitive for "we", "our", etc.
        # but case-sensitive for "I" to avoid false positives
        if pattern == r"\bI\b":
            if re.search(pattern, full_content):
                found_first_person = True
                break
        elif re.search(pattern, full_content, re.IGNORECASE):
            found_first_person = True
            break
    checks["no_first_person"] = {
        "pass": not found_first_person,
        "message": (
            "First person language detected"
            if found_first_person
            else "No first person language"
        ),
        "level": "warning",
    }

    return checks


def format_qa_report(qa_results: dict) -> str:
    """Format QA results as a human-readable report."""
    lines = ["## Quality Assurance Report", ""]

    status = "PASS" if qa_results["overall_pass"] else "NEEDS REVIEW"
    lines.append(f"**Overall Status:** {status}")
    lines.append("")

    for category in ("structure", "citations", "content", "tone"):
        checks = qa_results.get(category, {})
        lines.append(f"### {category.title()}")
        for check_name, result in checks.items():
            if isinstance(result, dict):
                icon = "PASS" if result.get("pass", True) else "WARN"
                if not result.get("pass") and result.get("level") == "error":
                    icon = "FAIL"
                lines.append(f"  [{icon}] {check_name}: {result.get('message', '')}")
        lines.append("")

    if qa_results.get("errors"):
        lines.append("### Errors")
        for err in qa_results["errors"]:
            lines.append(f"  - {err}")
        lines.append("")

    if qa_results.get("warnings"):
        lines.append("### Warnings")
        for warn in qa_results["warnings"]:
            lines.append(f"  - {warn}")

    return "\n".join(lines)
