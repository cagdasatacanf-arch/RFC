"""Tests for framework management."""

import json
import tempfile
from pathlib import Path

import pytest

from src.db import init_db
from src.frameworks.base import (
    BASE_SECTIONS,
    build_effective_framework,
    build_effective_section,
    get_base_section,
    get_total_citation_target,
    get_total_word_target,
)
from src.frameworks.manager import FrameworkManager
from src.frameworks.validator import validate_framework


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database."""
    path = tmp_path / "test.db"
    init_db(path)
    return path


@pytest.fixture
def manager(db_path):
    """Create a FrameworkManager with test database."""
    return FrameworkManager(db_path=db_path)


# ── Base Framework Tests ──

class TestBaseFramework:
    def test_has_11_sections(self):
        assert len(BASE_SECTIONS) == 11

    def test_section_ids_sequential(self):
        ids = [s["id"] for s in BASE_SECTIONS]
        assert ids == list(range(1, 12))

    def test_all_sections_have_word_counts(self):
        for s in BASE_SECTIONS:
            assert "word_count" in s
            assert s["word_count"]["min"] > 0
            assert s["word_count"]["max"] >= s["word_count"]["min"]

    def test_all_sections_have_citation_targets(self):
        for s in BASE_SECTIONS:
            assert "citation_target" in s
            assert s["citation_target"]["min"] >= 0

    def test_get_base_section(self):
        section = get_base_section(1)
        assert section is not None
        assert section["name"] == "Executive Summary"

    def test_get_base_section_invalid(self):
        assert get_base_section(99) is None

    def test_total_word_target(self):
        totals = get_total_word_target()
        assert totals["min"] >= 5000
        assert totals["max"] >= totals["min"]

    def test_total_citation_target(self):
        totals = get_total_citation_target()
        assert totals["min"] >= 20
        assert totals["max"] >= totals["min"]

    def test_build_effective_section_no_overrides(self):
        section = build_effective_section(1)
        assert section["name"] == "Executive Summary"

    def test_build_effective_section_with_name_override(self):
        section = build_effective_section(3, {"name_override": "Custom Name"})
        assert section["name"] == "Custom Name"

    def test_build_effective_section_invalid_id(self):
        with pytest.raises(ValueError):
            build_effective_section(99)


# ── Framework Validation Tests ──

class TestFrameworkValidator:
    def test_valid_framework(self):
        fw = {"sector_id": "test_sector", "display_name": "Test Sector"}
        errors = validate_framework(fw)
        assert errors == []

    def test_missing_sector_id(self):
        fw = {"display_name": "Test"}
        errors = validate_framework(fw)
        assert any("sector_id" in e for e in errors)

    def test_missing_display_name(self):
        fw = {"sector_id": "test"}
        errors = validate_framework(fw)
        assert any("display_name" in e for e in errors)

    def test_invalid_section_override_id(self):
        fw = {
            "sector_id": "test",
            "display_name": "Test",
            "section_overrides": {99: {}},
        }
        errors = validate_framework(fw)
        assert any("Invalid section ID" in e for e in errors)


# ── Framework Manager Tests ──

class TestFrameworkManager:
    def test_create_and_get(self, manager):
        fw = {
            "sector_id": "test_sector",
            "display_name": "Test Sector",
            "description": "A test framework",
        }
        fid, errors = manager.create(fw)
        assert errors == []
        assert fid == "test_sector"

        retrieved = manager.get(fid)
        assert retrieved is not None
        assert retrieved["display_name"] == "Test Sector"

    def test_list(self, manager):
        fw1 = {"sector_id": "s1", "display_name": "Sector 1"}
        fw2 = {"sector_id": "s2", "display_name": "Sector 2"}
        manager.create(fw1)
        manager.create(fw2)

        frameworks = manager.list()
        assert len(frameworks) == 2

    def test_delete(self, manager):
        fw = {"sector_id": "to_delete", "display_name": "Delete Me"}
        manager.create(fw)
        assert manager.delete("to_delete")
        assert manager.get("to_delete") is None

    def test_clone(self, manager):
        fw = {
            "sector_id": "original",
            "display_name": "Original",
            "section_overrides": {"1": {"required_elements": ["test"]}},
        }
        manager.create(fw)

        fid, errors = manager.clone("original", "cloned")
        assert errors == []
        cloned = manager.get("cloned")
        assert cloned is not None
        assert "1" in cloned.get("section_overrides", {})

    def test_get_effective(self, manager):
        fw = {
            "sector_id": "eff_test",
            "display_name": "Effective Test",
            "section_overrides": {
                "3": {"name_override": "Custom Section 3"},
            },
        }
        manager.create(fw)
        effective = manager.get_effective("eff_test")
        assert effective is not None
        section_3 = next(s for s in effective["sections"] if s["id"] == 3)
        assert section_3["name"] == "Custom Section 3"

    def test_export_import(self, manager, tmp_path):
        fw = {"sector_id": "export_test", "display_name": "Export Test"}
        manager.create(fw)

        export_path = tmp_path / "exported.json"
        assert manager.export_to_file("export_test", export_path, "json")

        # Delete and re-import
        manager.delete("export_test")
        fid, errors = manager.import_from_file(export_path)
        assert errors == []
        assert manager.get(fid) is not None


# ── Effective Framework Build Tests ──

class TestEffectiveFramework:
    def test_build_with_semiconductor_overrides(self):
        fw = {
            "sector_id": "semi",
            "display_name": "Semi Test",
            "section_overrides": {
                1: {"required_elements": ["business_model_snapshot", "headline_thesis"]},
                3: {"name_override": "Strategic Positioning - Fabless Model"},
            },
        }
        effective = build_effective_framework(fw)
        assert len(effective["sections"]) == 11
        assert effective["sections"][0]["required_elements"] == [
            "business_model_snapshot", "headline_thesis"
        ]
        assert effective["sections"][2]["name"] == "Strategic Positioning - Fabless Model"
