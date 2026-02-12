"""Prompt template management for AI-powered section generation."""

SYSTEM_PROMPT = """You are an institutional-grade investment analyst writing a detailed research report.

Your writing must follow these standards:
- Institutional tone: professional, evidence-based, balanced
- No first person (never "I", "we", "our")
- No hype language (avoid "massive", "incredible", "game-changing", "revolutionary")
- Specific metrics: use actual numbers, percentages, dollar amounts
- Named entities: reference specific companies, products, customers by name
- Citations: embed [N] references inline where claims are supported by sources
- Tables: use markdown tables for financial data and peer comparisons
- Forward-looking statements must reference the source (management guidance, analyst estimates)

Structure each section with clear headers and logical flow."""


def build_section_prompt(
    section: dict,
    company_profile: dict,
    research_data: dict | None = None,
    citations: list[dict] | None = None,
    full_framework: dict | None = None,
) -> str:
    """Build a prompt for generating a specific report section.

    Args:
        section: The effective section definition (from build_effective_section).
        company_profile: The company profile dict.
        research_data: Additional research data (financials, news, etc.).
        citations: Available citations for this section.
        full_framework: The full effective framework for context.

    Returns:
        The complete prompt string for the Claude API.
    """
    meta = company_profile.get("metadata", {})
    fin = company_profile.get("financials", {})
    val = company_profile.get("valuation", {})
    ops = company_profile.get("operational", {})

    section_name = section.get("name", f"Section {section['id']}")
    word_min = section.get("word_count", {}).get("min", 400)
    word_max = section.get("word_count", {}).get("max", 600)
    cit_min = section.get("citation_target", {}).get("min", 2)
    cit_max = section.get("citation_target", {}).get("max", 5)

    prompt_parts = [
        f"# Section {section['id']}: {section_name}",
        "",
        f"**Company:** {meta.get('name', '?')} ({meta.get('ticker', '?')})",
        f"**Report Date:** {meta.get('report_date', '?')}",
        f"**Reference Quarter:** {meta.get('reference_quarter', '?')}",
        "",
        f"**Word Count Target:** {word_min}–{word_max} words",
        f"**Citation Target:** {cit_min}–{cit_max} inline citations [N]",
        "",
    ]

    # Required elements
    if "required_elements" in section:
        prompt_parts.append("**Required Elements (must include all):**")
        for elem in section["required_elements"]:
            prompt_parts.append(f"- {elem.replace('_', ' ').title()}")
        prompt_parts.append("")

    # Subsections
    if "subsections" in section:
        prompt_parts.append("**Subsections to cover:**")
        for sub in section["subsections"]:
            prompt_parts.append(f"- {sub.replace('_', ' ').title()}")
        prompt_parts.append("")

    # Sector-specific extras
    for key in ("operational_kpis", "metrics", "teaching_topics",
                "risk_categories", "valuation_multiples", "key_drivers"):
        if key in section:
            prompt_parts.append(f"**{key.replace('_', ' ').title()}:**")
            for item in section[key]:
                prompt_parts.append(f"- {item.replace('_', ' ').title()}")
            prompt_parts.append("")

    # Product analysis template
    if "product_analysis_template" in section:
        pat = section["product_analysis_template"]
        prompt_parts.append("**Per-Product Analysis Template:**")
        for field in pat.get("per_product", []):
            prompt_parts.append(f"- {field.replace('_', ' ').title()}")
        prompt_parts.append("")

    # Peer groups
    if "peer_groups" in section:
        prompt_parts.append("**Peer Groups:**")
        for group, tickers in section["peer_groups"].items():
            prompt_parts.append(f"- {group.replace('_', ' ').title()}: {', '.join(tickers)}")
        prompt_parts.append("")

    # Margin analysis
    if "margin_analysis" in section:
        ma = section["margin_analysis"]
        for sub_key in ("gross_margin_drivers", "gross_margin_headwinds",
                        "margin_drivers", "margin_headwinds"):
            if sub_key in ma:
                prompt_parts.append(f"**{sub_key.replace('_', ' ').title()}:**")
                for item in ma[sub_key]:
                    prompt_parts.append(f"- {item.replace('_', ' ').title()}")
                prompt_parts.append("")

    # Company data context
    prompt_parts.append("---")
    prompt_parts.append("## Company Data Available")
    prompt_parts.append("")
    prompt_parts.append(f"Revenue (current): {_fmt(fin.get('revenue', {}).get('current'))}")
    prompt_parts.append(f"Gross Margin: {_fmt(fin.get('gross_margin', {}).get('current'))}")
    prompt_parts.append(f"Operating Margin: {_fmt(fin.get('operating_margin', {}).get('current'))}")
    prompt_parts.append(f"FCF: {_fmt(fin.get('fcf'))}")
    prompt_parts.append(f"EPS (GAAP): {_fmt(fin.get('eps', {}).get('gaap'))}")
    prompt_parts.append(f"Market Cap: {_fmt(val.get('market_cap'))}")
    prompt_parts.append(f"EV/Sales: {_fmt(val.get('ev_sales'))}")
    prompt_parts.append(f"Fwd P/E: {_fmt(val.get('pe_forward'))}")
    prompt_parts.append("")

    if ops.get("products"):
        prompt_parts.append(f"Products: {', '.join(ops['products'])}")
    if ops.get("customers"):
        prompt_parts.append(f"Key Customers: {', '.join(ops['customers'])}")
    prompt_parts.append("")

    # Additional research data
    if research_data:
        prompt_parts.append("---")
        prompt_parts.append("## Additional Research Data")
        prompt_parts.append("")
        for key, value in research_data.items():
            if isinstance(value, str):
                prompt_parts.append(f"**{key}:** {value}")
            elif isinstance(value, list):
                prompt_parts.append(f"**{key}:**")
                for item in value:
                    prompt_parts.append(f"- {item}")
            prompt_parts.append("")

    # Available citations
    if citations:
        prompt_parts.append("---")
        prompt_parts.append("## Available Citations")
        prompt_parts.append("Use [N] format to cite these sources inline:")
        prompt_parts.append("")
        for c in citations:
            cid = c.get("id", "?")
            title = c.get("title", "Unknown")
            subject = c.get("subject", "")
            prompt_parts.append(f"[{cid}] {title} — {subject}")
        prompt_parts.append("")

    # Final instruction
    prompt_parts.extend([
        "---",
        "",
        f"Write Section {section['id']}: {section_name}.",
        f"Target {word_min}–{word_max} words.",
        "Use markdown formatting with appropriate headers (## and ###).",
        "Include inline citations [N] where you reference data or claims.",
        "If financial tables are required, use markdown table format.",
        "Maintain institutional analyst tone throughout.",
    ])

    # Section-specific instructions
    if section["id"] == 8:
        purpose = section.get("purpose", "Teach readers how to analyze this company type")
        prompt_parts.append(f"\nMasterclass purpose: {purpose}")
        prompt_parts.append("This section should educate the reader, not just analyze the company.")

    return "\n".join(prompt_parts)


def _fmt(val) -> str:
    if val is None:
        return "Not available"
    if isinstance(val, (int, float)):
        if abs(val) >= 1e9:
            return f"${val / 1e9:.1f}B"
        if abs(val) >= 1e6:
            return f"${val / 1e6:.1f}M"
        if isinstance(val, float) and val < 1:
            return f"{val * 100:.1f}%"
        return f"{val:,.2f}"
    return str(val)
