"""Section writer - generates report sections using Claude API."""

from __future__ import annotations

from src.config import load_config
from src.generator.prompts import SYSTEM_PROMPT, build_section_prompt


def write_section(
    section: dict,
    company_profile: dict,
    research_data: dict | None = None,
    citations: list[dict] | None = None,
    framework: dict | None = None,
) -> dict:
    """Generate a single report section using the Claude API.

    Returns a dict with:
      - section_id: int
      - name: str
      - content: str (markdown)
      - word_count: int
      - status: "generated" | "error"
      - error: str | None
    """
    config = load_config()
    api_key = config.get("api_key", "")
    model = config.get("model", "claude-sonnet-4-20250514")

    if not api_key:
        return {
            "section_id": section["id"],
            "name": section.get("name", f"Section {section['id']}"),
            "content": "",
            "word_count": 0,
            "status": "error",
            "error": "No API key configured. Run: irf config set api_key <your-key>",
        }

    prompt = build_section_prompt(
        section=section,
        company_profile=company_profile,
        research_data=research_data,
        citations=citations,
        full_framework=framework,
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=config.get("max_tokens_per_section", 4096),
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        word_count = len(content.split())

        return {
            "section_id": section["id"],
            "name": section.get("name", f"Section {section['id']}"),
            "content": content,
            "word_count": word_count,
            "status": "generated",
            "error": None,
        }

    except ImportError:
        return {
            "section_id": section["id"],
            "name": section.get("name", f"Section {section['id']}"),
            "content": "",
            "word_count": 0,
            "status": "error",
            "error": "anthropic package not installed. Run: pip install anthropic",
        }
    except Exception as e:
        return {
            "section_id": section["id"],
            "name": section.get("name", f"Section {section['id']}"),
            "content": "",
            "word_count": 0,
            "status": "error",
            "error": str(e),
        }


def write_all_sections(
    effective_framework: dict,
    company_profile: dict,
    research_data: dict | None = None,
    citations: list[dict] | None = None,
    progress_callback=None,
) -> list[dict]:
    """Generate all sections for a report.

    Args:
        effective_framework: The fully resolved framework.
        company_profile: Company profile dict.
        research_data: Additional research data.
        citations: List of citation objects.
        progress_callback: Optional callable(section_id, status, result).

    Returns:
        List of section result dicts.
    """
    sections = effective_framework.get("sections", [])
    results = []

    for section in sections:
        if progress_callback:
            progress_callback(section["id"], "generating", None)

        result = write_section(
            section=section,
            company_profile=company_profile,
            research_data=research_data,
            citations=citations,
            framework=effective_framework,
        )
        results.append(result)

        if progress_callback:
            progress_callback(section["id"], result["status"], result)

    return results
