"""Framework validation logic."""

from __future__ import annotations

from src.frameworks.base import BASE_SECTIONS

REQUIRED_FRAMEWORK_FIELDS = ["sector_id", "display_name"]
VALID_SECTION_IDS = {s["id"] for s in BASE_SECTIONS}


def validate_framework(framework: dict) -> list[str]:
    """Validate a framework configuration.

    Returns a list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    # Check required top-level fields
    for field in REQUIRED_FRAMEWORK_FIELDS:
        if not framework.get(field):
            errors.append(f"Missing required field: {field}")

    # Validate sector_id format
    sector_id = framework.get("sector_id", "")
    if sector_id and not sector_id.replace("_", "").isalnum():
        errors.append(
            f"sector_id must be alphanumeric with underscores, got: {sector_id}"
        )

    # Validate section overrides reference valid section IDs
    overrides = framework.get("section_overrides", {})
    for key in overrides:
        sid = int(key) if isinstance(key, str) and key.isdigit() else key
        if sid not in VALID_SECTION_IDS:
            errors.append(f"Invalid section ID in overrides: {key}")

    # Validate word count overrides
    for key, override in overrides.items():
        if "word_count" in override:
            wc = override["word_count"]
            if wc.get("min", 0) > wc.get("max", float("inf")):
                errors.append(
                    f"Section {key}: word_count min exceeds max"
                )

    return errors


def validate_section_content(section_id: int, content: str, framework: dict) -> list[str]:
    """Validate generated section content against framework requirements.

    Returns a list of warning messages.
    """
    warnings: list[str] = []
    overrides = framework.get("section_overrides", {})
    section_override = overrides.get(section_id) or overrides.get(str(section_id)) or {}

    # Determine word count targets
    base_section = None
    for s in BASE_SECTIONS:
        if s["id"] == section_id:
            base_section = s
            break

    if base_section is None:
        warnings.append(f"Unknown section ID: {section_id}")
        return warnings

    wc = section_override.get("word_count", base_section["word_count"])
    word_count = len(content.split())

    if word_count < wc["min"]:
        warnings.append(
            f"Section {section_id} ({base_section['name']}): "
            f"{word_count} words below minimum {wc['min']}"
        )
    if word_count > wc["max"]:
        warnings.append(
            f"Section {section_id} ({base_section['name']}): "
            f"{word_count} words exceeds maximum {wc['max']}"
        )

    return warnings
