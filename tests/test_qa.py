"""Tests for the QA engine."""

from src.generator.qa import run_qa_checks, format_qa_report


def _make_section(section_id, content="", word_count=None, status="generated"):
    if word_count is None:
        word_count = len(content.split())
    return {
        "section_id": section_id,
        "name": f"Section {section_id}",
        "content": content,
        "word_count": word_count,
        "status": status,
    }


class TestQAChecks:
    def test_missing_sections(self):
        sections = [_make_section(i, "Some content here. " * 50) for i in range(1, 10)]
        # Missing sections 10 and 11
        report = {"sections": sections, "citations": [], "word_count": 5000}
        results = run_qa_checks(report)
        assert not results["structure"]["all_11_sections_present"]["pass"]

    def test_all_sections_present(self):
        sections = [_make_section(i, "Some content. " * 50) for i in range(1, 12)]
        report = {"sections": sections, "citations": [], "word_count": 8500}
        results = run_qa_checks(report)
        assert results["structure"]["all_11_sections_present"]["pass"]

    def test_hype_language_detected(self):
        content = "This is a massive opportunity with incredible potential."
        sections = [_make_section(i, content) for i in range(1, 12)]
        report = {"sections": sections, "citations": [], "word_count": 500}
        results = run_qa_checks(report)
        assert not results["tone"]["no_hype_language"]["pass"]

    def test_no_hype_language(self):
        content = "Revenue grew 15% year-over-year driven by Data Center demand."
        sections = [_make_section(i, content) for i in range(1, 12)]
        report = {"sections": sections, "citations": [], "word_count": 500}
        results = run_qa_checks(report)
        assert results["tone"]["no_hype_language"]["pass"]

    def test_first_person_detected(self):
        content = "We believe the company has strong fundamentals."
        sections = [_make_section(i, content) for i in range(1, 12)]
        report = {"sections": sections, "citations": [], "word_count": 500}
        results = run_qa_checks(report)
        assert not results["tone"]["no_first_person"]["pass"]

    def test_format_qa_report(self):
        sections = [_make_section(i, "Content. " * 80) for i in range(1, 12)]
        report = {"sections": sections, "citations": [], "word_count": 8500}
        results = run_qa_checks(report)
        formatted = format_qa_report(results)
        assert "Quality Assurance Report" in formatted
        assert "Structure" in formatted
