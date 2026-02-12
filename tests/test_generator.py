"""Tests for the report generator components."""

import json

from src.frameworks.base import build_effective_framework
from src.generator.assembler import assemble_report, render_report_markdown
from src.generator.profiler import create_company_profile
from src.generator.prompts import build_section_prompt


def _sample_profile():
    return {
        "id": "test123",
        "metadata": {
            "name": "Test Corp",
            "ticker": "TEST",
            "exchange": "NYSE",
            "sector_framework": "semiconductor_fabless",
            "report_date": "2026-02-12",
            "reference_quarter": "Q4 FY2026",
            "currency": "USD",
        },
        "financials": {
            "revenue": {"current": 39_300_000_000, "prior_year": None, "yoy_pct": None},
            "gross_margin": {"current": 0.73, "prior_year": None},
            "operating_margin": {"current": 0.55, "prior_year": None},
            "r_and_d_pct": None,
            "eps": {"gaap": 2.50, "non_gaap": 3.10},
            "fcf": 15_000_000_000,
            "segment_breakdown": {},
        },
        "operational": {
            "primary_segment": "Data Center",
            "products": ["H100", "H200", "B100"],
            "customers": ["Microsoft", "Google", "Amazon"],
            "design_wins": [],
            "foundry": "TSMC",
        },
        "valuation": {
            "market_cap": 2_000_000_000_000,
            "ev_sales": 50.0,
            "pe_forward": 45.0,
            "p_fcf": None,
            "peers": ["AMD", "AVGO"],
        },
        "catalysts": [],
        "risks": [],
        "sources": [],
    }


def _sample_framework():
    return {
        "sector_id": "semiconductor_fabless",
        "display_name": "Semiconductor - Fabless",
        "section_overrides": {
            1: {"required_elements": ["business_model_snapshot", "headline_thesis"]},
        },
    }


class TestPromptBuilder:
    def test_build_section_prompt(self):
        framework = build_effective_framework(_sample_framework())
        section = framework["sections"][0]
        profile = _sample_profile()

        prompt = build_section_prompt(section, profile)
        assert "Section 1" in prompt
        assert "Executive Summary" in prompt
        assert "TEST" in prompt
        assert "400" in prompt  # word min
        assert "500" in prompt  # word max

    def test_prompt_includes_company_data(self):
        framework = build_effective_framework(_sample_framework())
        section = framework["sections"][0]
        profile = _sample_profile()

        prompt = build_section_prompt(section, profile)
        assert "$39.3B" in prompt  # Revenue
        assert "73.0%" in prompt  # Gross margin

    def test_prompt_includes_citations(self):
        framework = build_effective_framework(_sample_framework())
        section = framework["sections"][0]
        profile = _sample_profile()
        citations = [{"id": 1, "title": "Q4 Earnings", "subject": "Revenue data"}]

        prompt = build_section_prompt(section, profile, citations=citations)
        assert "[1] Q4 Earnings" in prompt


class TestAssembler:
    def test_assemble_report(self):
        sections = [
            {
                "section_id": i,
                "name": f"Section {i}",
                "content": f"Content for section {i}. " * 50,
                "word_count": 300,
                "status": "generated",
                "error": None,
            }
            for i in range(1, 12)
        ]
        profile = _sample_profile()
        framework = build_effective_framework(_sample_framework())

        report = assemble_report(sections, profile, framework)
        assert report["status"] == "complete"
        assert report["word_count"] == 3300
        assert len(report["sections"]) == 11

    def test_assemble_with_errors(self):
        sections = [
            {
                "section_id": 1,
                "name": "Section 1",
                "content": "",
                "word_count": 0,
                "status": "error",
                "error": "API error",
            }
        ]
        profile = _sample_profile()
        framework = build_effective_framework(_sample_framework())

        report = assemble_report(sections, profile, framework)
        assert report["status"] == "draft"

    def test_render_markdown(self):
        sections = [
            {
                "section_id": i,
                "name": f"Section {i}",
                "content": f"Content for section {i}.",
                "word_count": 50,
                "status": "generated",
            }
            for i in range(1, 12)
        ]
        profile = _sample_profile()
        framework = build_effective_framework(_sample_framework())
        report = assemble_report(sections, profile, framework)

        md = render_report_markdown(report, profile)
        assert "Test Corp" in md
        assert "TEST" in md
        assert "Table of Contents" in md
        assert "Section 1" in md
        assert "Section 11" in md


class TestProfiler:
    def test_create_profile_no_fetch(self):
        profile = create_company_profile(
            ticker="TEST",
            name="Test Corp",
            exchange="NYSE",
            sector_framework="semiconductor_fabless",
            auto_fetch=False,
        )
        assert profile["metadata"]["ticker"] == "TEST"
        assert profile["metadata"]["name"] == "Test Corp"
        assert profile["id"] is not None
