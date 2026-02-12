"""Macro and industry data module.

Phase 1: Provides framework-driven macro context templates.
Phase 2: Will add automated macro data fetching.
"""

from __future__ import annotations


def get_macro_context(framework: dict) -> dict:
    """Get macro context prompts based on framework sector.

    Returns a dict of macro areas with descriptions for the AI writer.
    """
    overrides = framework.get("section_overrides", {})
    section_2 = overrides.get(2) or overrides.get("2") or {}

    return {
        "key_drivers": section_2.get("key_drivers", []),
        "subsections": section_2.get("subsections", []),
    }


def format_macro_brief(context: dict) -> str:
    """Format macro context as a briefing for the report writer."""
    lines = ["### Macro Context"]
    if context.get("key_drivers"):
        lines.append("\n**Key Macro Drivers:**")
        for driver in context["key_drivers"]:
            lines.append(f"- {driver.replace('_', ' ').title()}")
    if context.get("subsections"):
        lines.append("\n**Analysis Areas:**")
        for sub in context["subsections"]:
            lines.append(f"- {sub.replace('_', ' ').title()}")
    return "\n".join(lines)
