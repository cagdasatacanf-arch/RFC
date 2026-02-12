"""Base 11-section investment analysis framework definition.

This is the immutable template from which all sector frameworks inherit.
Based on the Kongsberg methodology.
"""

from __future__ import annotations

BASE_SECTIONS = [
    {
        "id": 1,
        "name": "Executive Summary",
        "word_count": {"min": 400, "max": 500},
        "required_elements": [
            "headline_thesis",
            "key_catalysts",
            "headline_metrics",
            "valuation_context",
            "mispricing_argument",
            "investor_takeaway",
        ],
        "citation_target": {"min": 3, "max": 5},
    },
    {
        "id": 2,
        "name": "Macroeconomic & Geopolitical Backdrop",
        "word_count": {"min": 400, "max": 600},
        "subsections": [
            "industry_tailwinds",
            "market_cycle_position",
            "geopolitical_regulatory_context",
        ],
        "citation_target": {"min": 4, "max": 6},
    },
    {
        "id": 3,
        "name": "Strategic Positioning",
        "word_count": {"min": 400, "max": 600},
        "variants": ["restructuring", "business_overview", "m_and_a"],
        "citation_target": {"min": 3, "max": 5},
    },
    {
        "id": 4,
        "name": "Operational Analysis - Primary",
        "word_count": {"min": 800, "max": 1200},
        "required_elements": [
            "segment_overview",
            "product_portfolio",
            "operational_kpis",
            "outlook",
        ],
        "citation_target": {"min": 8, "max": 12},
    },
    {
        "id": 5,
        "name": "Operational Analysis - Secondary",
        "word_count": {"min": 400, "max": 600},
        "citation_target": {"min": 3, "max": 5},
    },
    {
        "id": 6,
        "name": "Associated Companies & Ecosystem",
        "word_count": {"min": 300, "max": 400},
        "citation_target": {"min": 2, "max": 4},
    },
    {
        "id": 7,
        "name": "Financial Performance Deep Dive",
        "word_count": {"min": 600, "max": 800},
        "required_elements": [
            "pnl_snapshot_table",
            "revenue_analysis",
            "margin_analysis",
            "backlog_or_forward_metrics",
            "balance_sheet_cash_flow",
        ],
        "citation_target": {"min": 6, "max": 10},
    },
    {
        "id": 8,
        "name": "Masterclass",
        "word_count": {"min": 800, "max": 1000},
        "purpose": "Teach readers how to analyze this company type",
        "citation_target": {"min": 4, "max": 6},
    },
    {
        "id": 9,
        "name": "Peer Valuation & Comparative Analysis",
        "word_count": {"min": 500, "max": 700},
        "required_elements": [
            "peer_comparison_table",
            "valuation_discussion",
            "fair_value_estimate",
        ],
        "citation_target": {"min": 5, "max": 7},
    },
    {
        "id": 10,
        "name": "Risks & Challenges",
        "word_count": {"min": 400, "max": 600},
        "required_elements": [
            "risk_1_with_probability_impact",
            "risk_2_with_probability_impact",
            "risk_3_with_probability_impact",
        ],
        "citation_target": {"min": 3, "max": 5},
    },
    {
        "id": 11,
        "name": "Conclusion & Monitoring Framework",
        "word_count": {"min": 300, "max": 400},
        "required_elements": [
            "thesis_restatement",
            "monitoring_points",
            "actionable_recommendations",
        ],
        "citation_target": {"min": 2, "max": 3},
    },
]


def get_base_section(section_id: int) -> dict | None:
    """Get a base section by its ID (1-11)."""
    for section in BASE_SECTIONS:
        if section["id"] == section_id:
            return section.copy()
    return None


def get_total_word_target() -> dict:
    """Get the aggregate word count target."""
    total_min = sum(s["word_count"]["min"] for s in BASE_SECTIONS)
    total_max = sum(s["word_count"]["max"] for s in BASE_SECTIONS)
    return {"min": total_min, "max": total_max}


def get_total_citation_target() -> dict:
    """Get the aggregate citation target."""
    total_min = sum(s["citation_target"]["min"] for s in BASE_SECTIONS)
    total_max = sum(s["citation_target"]["max"] for s in BASE_SECTIONS)
    return {"min": total_min, "max": total_max}


def build_effective_section(section_id: int, overrides: dict | None = None) -> dict:
    """Build an effective section definition by merging base with overrides."""
    base = get_base_section(section_id)
    if base is None:
        raise ValueError(f"Invalid section ID: {section_id}")
    if overrides is None:
        return base
    # Apply name override
    if "name_override" in overrides:
        base["name"] = overrides["name_override"]
    # Merge required_elements (replace if provided)
    if "required_elements" in overrides:
        base["required_elements"] = overrides["required_elements"]
    # Merge subsections
    if "subsections" in overrides:
        base["subsections"] = overrides["subsections"]
    # Add any extra keys from overrides
    for key, value in overrides.items():
        if key not in ("name_override",):
            base[key] = value
    return base


def build_effective_framework(sector_config: dict) -> dict:
    """Build a complete framework by merging sector overrides onto the base."""
    overrides = sector_config.get("section_overrides", {})
    sections = []
    for base_section in BASE_SECTIONS:
        sid = base_section["id"]
        section_overrides = overrides.get(sid) or overrides.get(str(sid))
        sections.append(build_effective_section(sid, section_overrides))
    return {
        "sector_id": sector_config.get("sector_id", "unknown"),
        "display_name": sector_config.get("display_name", "Unknown"),
        "description": sector_config.get("description", ""),
        "sections": sections,
        "data_requirements": sector_config.get("data_requirements", {}),
    }
