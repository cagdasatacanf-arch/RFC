"""Tests for the citation engine."""

from src.research.citations import (
    assign_citation_ids,
    create_citation,
    format_citation_reference,
    format_references_section,
    validate_citations,
)


class TestCitationCreation:
    def test_create_basic_citation(self):
        c = create_citation(
            url="https://example.com",
            title="Test Article",
            publication="Test Pub",
            category="news",
        )
        assert c["url"] == "https://example.com"
        assert c["title"] == "Test Article"
        assert c["id"] is None
        assert c["date_accessed"] is not None

    def test_assign_ids(self):
        citations = [
            create_citation(url=f"https://example.com/{i}", title=f"Article {i}")
            for i in range(5)
        ]
        assigned = assign_citation_ids(citations)
        ids = [c["id"] for c in assigned]
        assert ids == [1, 2, 3, 4, 5]


class TestCitationFormatting:
    def test_format_reference(self):
        c = {
            "id": 1,
            "title": "Q4 Earnings",
            "publication": "Company IR",
            "url": "https://ir.example.com",
            "date_accessed": "2026-02-12",
        }
        ref = format_citation_reference(c)
        assert "[1]" in ref
        assert "Q4 Earnings" in ref
        assert "Company IR" in ref
        assert "Şubat" in ref  # Turkish month

    def test_format_references_section(self):
        citations = [
            {"id": 1, "title": "Source 1", "publication": "Pub 1",
             "url": "https://example.com/1", "date_accessed": "2026-01-15"},
            {"id": 2, "title": "Source 2", "publication": "Pub 2",
             "url": "https://example.com/2", "date_accessed": "2026-02-01"},
        ]
        section = format_references_section(citations)
        assert "## References" in section
        assert "[1]" in section
        assert "[2]" in section


class TestCitationValidation:
    def test_valid_citations(self):
        content = "Revenue was $10B[1], beating estimates[2]. Growth was strong[3]."
        citations = [
            {"id": 1}, {"id": 2}, {"id": 3},
        ]
        result = validate_citations(content, citations)
        assert result["orphaned"] == []
        assert result["uncited"] == []
        assert result["sequential"]

    def test_orphaned_citation(self):
        content = "Data shows growth[1][5]."
        citations = [{"id": 1}]
        result = validate_citations(content, citations)
        assert 5 in result["orphaned"]

    def test_uncited_reference(self):
        content = "Only one citation[1]."
        citations = [{"id": 1}, {"id": 2}, {"id": 3}]
        result = validate_citations(content, citations)
        assert 2 in result["uncited"]
        assert 3 in result["uncited"]

    def test_non_sequential(self):
        content = "Refs [1] and [3]."
        citations = [{"id": 1}, {"id": 3}]
        result = validate_citations(content, citations)
        assert not result["sequential"]
