"""Framework CRUD operations and management."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import FRAMEWORKS_DIR
from src.db import (
    delete_framework,
    get_framework,
    list_frameworks,
    save_framework,
)
from src.frameworks.base import build_effective_framework
from src.frameworks.validator import validate_framework


class FrameworkManager:
    """Manages sector-specific investment analysis frameworks."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path

    def list(self) -> list[dict]:
        """List all available frameworks."""
        return list_frameworks(self.db_path)

    def get(self, framework_id: str) -> dict | None:
        """Get a framework by ID."""
        result = get_framework(framework_id, self.db_path)
        if result:
            return result["config"]
        return None

    def get_effective(self, framework_id: str) -> dict | None:
        """Get the fully resolved framework with base sections merged."""
        config = self.get(framework_id)
        if config is None:
            return None
        return build_effective_framework(config)

    def create(self, framework: dict) -> tuple[str, list[str]]:
        """Create a new framework. Returns (id, errors)."""
        errors = validate_framework(framework)
        if errors:
            return "", errors
        fid = save_framework(framework, self.db_path)
        return fid, []

    def update(self, framework_id: str, updates: dict) -> list[str]:
        """Update an existing framework. Returns errors if any."""
        existing = self.get(framework_id)
        if existing is None:
            return [f"Framework not found: {framework_id}"]
        existing.update(updates)
        errors = validate_framework(existing)
        if errors:
            return errors
        existing["id"] = framework_id
        save_framework(existing, self.db_path)
        return []

    def delete(self, framework_id: str) -> bool:
        """Delete a framework."""
        return delete_framework(framework_id, self.db_path)

    def clone(self, source_id: str, target_id: str) -> tuple[str, list[str]]:
        """Clone an existing framework with a new ID."""
        source = self.get(source_id)
        if source is None:
            return "", [f"Source framework not found: {source_id}"]
        source["sector_id"] = target_id
        source["id"] = target_id
        source["display_name"] = f"Copy of {source.get('display_name', source_id)}"
        return self.create(source)

    def export_to_file(self, framework_id: str, output_path: Path, fmt: str = "json") -> bool:
        """Export a framework to a file."""
        config = self.get(framework_id)
        if config is None:
            return False
        if fmt == "json":
            with open(output_path, "w") as f:
                json.dump(config, f, indent=2)
        elif fmt == "md":
            effective = build_effective_framework(config)
            md = self._framework_to_markdown(effective)
            with open(output_path, "w") as f:
                f.write(md)
        return True

    def import_from_file(self, file_path: Path) -> tuple[str, list[str]]:
        """Import a framework from a JSON file."""
        with open(file_path) as f:
            framework = json.load(f)
        return self.create(framework)

    def load_builtin_frameworks(self) -> int:
        """Load all built-in JSON frameworks from data/frameworks/. Returns count loaded."""
        loaded = 0
        if not FRAMEWORKS_DIR.exists():
            return loaded
        for json_file in FRAMEWORKS_DIR.glob("*.json"):
            with open(json_file) as f:
                framework = json.load(f)
            save_framework(framework, self.db_path)
            loaded += 1
        return loaded

    @staticmethod
    def _framework_to_markdown(effective: dict) -> str:
        """Convert an effective framework to markdown documentation."""
        lines = [
            f"# {effective['display_name']}",
            "",
            effective.get("description", ""),
            "",
            "## Sections",
            "",
        ]
        for section in effective.get("sections", []):
            wc = section.get("word_count", {})
            ct = section.get("citation_target", {})
            lines.append(
                f"### Section {section['id']}: {section['name']}"
            )
            lines.append(
                f"- Word count: {wc.get('min', '?')}–{wc.get('max', '?')}"
            )
            lines.append(
                f"- Citations: {ct.get('min', '?')}–{ct.get('max', '?')}"
            )
            if "required_elements" in section:
                lines.append("- Required elements:")
                for elem in section["required_elements"]:
                    lines.append(f"  - {elem}")
            if "subsections" in section:
                lines.append("- Subsections:")
                for sub in section["subsections"]:
                    lines.append(f"  - {sub}")
            lines.append("")
        return "\n".join(lines)
