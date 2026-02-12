"""CLI entry point for the Investment Report Framework Creator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.config import set_config_value, load_config, PROJECT_ROOT
from src.db import init_db, get_reports_for_company
from src.frameworks.base import build_effective_framework, get_total_word_target, get_total_citation_target
from src.frameworks.manager import FrameworkManager
from src.generator.assembler import assemble_report, render_report_markdown, save_assembled_report
from src.generator.profiler import create_company_profile, format_profile_summary, save_company_profile
from src.generator.qa import run_qa_checks, format_qa_report
from src.generator.writer import write_all_sections
from src.output.markdown import export_markdown
from src.research.citations import create_citation, assign_citation_ids

console = Console()
fm = FrameworkManager()


@click.group()
@click.version_option(version="0.1.0", prog_name="irf")
def main():
    """Investment Report Framework Creator (IRF).

    Create, manage, and deploy sector-specific investment analysis frameworks
    to produce institutional-grade research reports.
    """
    pass


# ── Init ──

@main.command()
def init():
    """Initialize the project database and load built-in frameworks."""
    console.print("[bold]Initializing IRF...[/bold]")
    init_db()
    console.print("  Database initialized.")
    count = fm.load_builtin_frameworks()
    console.print(f"  Loaded {count} built-in framework(s).")
    console.print("[green]Ready! Run 'irf framework list' to see available frameworks.[/green]")


# ── Config ──

@main.group()
def config():
    """Manage configuration settings."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value."""
    set_config_value(key, value)
    display_value = "****" if "key" in key.lower() else value
    console.print(f"Set {key} = {display_value}")


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = load_config()
    table = Table(title="Configuration")
    table.add_column("Key")
    table.add_column("Value")
    for k, v in cfg.items():
        display = "****" if "key" in k.lower() and v else str(v)
        table.add_row(k, display)
    console.print(table)


# ── Framework Commands ──

@main.group()
def framework():
    """Manage sector investment analysis frameworks."""
    pass


@framework.command("list")
def framework_list():
    """List all available sector frameworks."""
    frameworks = fm.list()
    if not frameworks:
        console.print("No frameworks found. Run 'irf init' to load built-in frameworks.")
        return

    table = Table(title="Available Frameworks")
    table.add_column("ID", style="cyan")
    table.add_column("Display Name", style="bold")
    table.add_column("Description")
    table.add_column("Created")

    for f in frameworks:
        table.add_row(
            f["id"],
            f["display_name"],
            (f.get("description") or "")[:60],
            f.get("created_at", "")[:10],
        )
    console.print(table)


@framework.command("view")
@click.argument("framework_id")
def framework_view(framework_id: str):
    """View framework details."""
    config = fm.get(framework_id)
    if config is None:
        console.print(f"[red]Framework not found: {framework_id}[/red]")
        return

    effective = build_effective_framework(config)
    console.print(Panel(
        f"[bold]{effective['display_name']}[/bold]\n"
        f"{effective.get('description', '')}",
        title=f"Framework: {framework_id}",
    ))

    table = Table(title="Sections")
    table.add_column("#", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Words")
    table.add_column("Citations")
    table.add_column("Key Elements")

    for section in effective["sections"]:
        wc = section.get("word_count", {})
        ct = section.get("citation_target", {})
        elements = section.get("required_elements", section.get("subsections", []))
        table.add_row(
            str(section["id"]),
            section["name"],
            f"{wc.get('min', '?')}–{wc.get('max', '?')}",
            f"{ct.get('min', '?')}–{ct.get('max', '?')}",
            ", ".join(elements[:3]) + ("..." if len(elements) > 3 else ""),
        )

    console.print(table)

    totals = get_total_word_target()
    cit_totals = get_total_citation_target()
    console.print(
        f"\n[dim]Total word target: {totals['min']:,}–{totals['max']:,} | "
        f"Total citation target: {cit_totals['min']}–{cit_totals['max']}[/dim]"
    )


@framework.command("create")
@click.argument("sector_id")
@click.option("--name", prompt="Display name", help="Human-readable framework name")
@click.option("--description", prompt="Description", help="Framework description")
def framework_create(sector_id: str, name: str, description: str):
    """Create a new sector framework interactively."""
    fw = {
        "sector_id": sector_id,
        "id": sector_id,
        "name": sector_id,
        "display_name": name,
        "description": description,
        "base_version": "1.0",
        "section_overrides": {},
        "data_requirements": {},
    }
    fid, errors = fm.create(fw)
    if errors:
        for err in errors:
            console.print(f"[red]Error: {err}[/red]")
        return
    console.print(f"[green]Framework created: {fid}[/green]")
    console.print("Use 'irf framework edit' to customize section overrides.")


@framework.command("edit")
@click.argument("framework_id")
def framework_edit(framework_id: str):
    """Edit a framework (opens JSON in $EDITOR or prints for manual editing)."""
    config = fm.get(framework_id)
    if config is None:
        console.print(f"[red]Framework not found: {framework_id}[/red]")
        return

    # Export to temp file for editing
    import tempfile
    import subprocess
    import os

    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", ""))
    if editor:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp:
            json.dump(config, tmp, indent=2)
            tmp_path = tmp.name

        subprocess.run([editor, tmp_path])

        with open(tmp_path) as f:
            updated = json.load(f)
        os.unlink(tmp_path)

        errors = fm.update(framework_id, updated)
        if errors:
            for err in errors:
                console.print(f"[red]Error: {err}[/red]")
        else:
            console.print(f"[green]Framework {framework_id} updated.[/green]")
    else:
        console.print("No $EDITOR set. Current config:")
        console.print_json(json.dumps(config, indent=2))
        console.print("\nTo edit, export and re-import:")
        console.print(f"  irf framework export {framework_id} > framework.json")
        console.print(f"  # edit framework.json")
        console.print(f"  irf framework import framework.json")


@framework.command("clone")
@click.argument("source_id")
@click.argument("target_id")
def framework_clone(source_id: str, target_id: str):
    """Clone an existing framework to create a new one."""
    fid, errors = fm.clone(source_id, target_id)
    if errors:
        for err in errors:
            console.print(f"[red]Error: {err}[/red]")
        return
    console.print(f"[green]Framework cloned: {source_id} -> {fid}[/green]")


@framework.command("delete")
@click.argument("framework_id")
@click.confirmation_option(prompt="Are you sure you want to delete this framework?")
def framework_delete(framework_id: str):
    """Delete a sector framework."""
    if fm.delete(framework_id):
        console.print(f"[green]Framework {framework_id} deleted.[/green]")
    else:
        console.print(f"[red]Framework not found: {framework_id}[/red]")


@framework.command("export")
@click.argument("framework_id")
@click.option("--format", "fmt", type=click.Choice(["json", "md"]), default="json")
@click.option("--output", "-o", "output_path", default=None, help="Output file path")
def framework_export(framework_id: str, fmt: str, output_path: str | None):
    """Export a framework definition to JSON or markdown."""
    if output_path is None:
        output_path = f"{framework_id}.{fmt}"
    path = Path(output_path)
    if fm.export_to_file(framework_id, path, fmt):
        console.print(f"[green]Exported to {path}[/green]")
    else:
        console.print(f"[red]Framework not found: {framework_id}[/red]")


@framework.command("import")
@click.argument("file_path", type=click.Path(exists=True))
def framework_import(file_path: str):
    """Import a framework from a JSON file."""
    fid, errors = fm.import_from_file(Path(file_path))
    if errors:
        for err in errors:
            console.print(f"[red]Error: {err}[/red]")
        return
    console.print(f"[green]Framework imported: {fid}[/green]")


# ── Report Commands ──

@main.group()
def report():
    """Generate and manage investment analysis reports."""
    pass


@report.command("new")
@click.argument("ticker")
@click.option("--framework", "framework_id", required=True, help="Sector framework to use")
@click.option("--quarter", default="", help="Reference quarter (e.g., Q4 FY2026)")
@click.option("--no-fetch", is_flag=True, help="Skip automatic financial data fetching")
def report_new(ticker: str, framework_id: str, quarter: str, no_fetch: bool):
    """Start a new report for a company."""
    ticker = ticker.upper()

    # Validate framework exists
    fw_config = fm.get(framework_id)
    if fw_config is None:
        console.print(f"[red]Framework not found: {framework_id}[/red]")
        console.print("Run 'irf framework list' to see available frameworks.")
        return

    console.print(Panel(
        f"Creating new report for [bold]{ticker}[/bold]\n"
        f"Framework: {fw_config.get('display_name', framework_id)}",
        title="New Report",
    ))

    # Step 1: Company Profile
    with console.status("Building company profile..."):
        profile = create_company_profile(
            ticker=ticker,
            sector_framework=framework_id,
            reference_quarter=quarter,
            auto_fetch=not no_fetch,
        )
        save_company_profile(profile)

    console.print("\n[bold]Company Profile:[/bold]")
    console.print(format_profile_summary(profile))
    console.print(f"\n[dim]Company ID: {profile['id']}[/dim]")
    console.print(f"\n[green]Profile saved. Next: irf report generate {ticker}[/green]")


@report.command("generate")
@click.argument("ticker")
@click.option("--section", "section_id", type=int, default=None, help="Generate a single section")
@click.option("--quick", is_flag=True, help="Quick 2-3K word analysis (not implemented yet)")
def report_generate(ticker: str, section_id: int | None, quick: bool):
    """Generate the report (or a single section) for a company."""
    ticker = ticker.upper()

    from src.db import get_company_by_ticker
    company = get_company_by_ticker(ticker)
    if company is None:
        console.print(f"[red]No profile found for {ticker}. Run: irf report new {ticker} --framework <id>[/red]")
        return

    profile = company["profile"]
    framework_id = profile.get("metadata", {}).get("sector_framework", "")
    fw_config = fm.get(framework_id)
    if fw_config is None:
        console.print(f"[red]Framework not found: {framework_id}[/red]")
        return

    effective = build_effective_framework(fw_config)

    # Filter to single section if requested
    if section_id is not None:
        effective["sections"] = [
            s for s in effective["sections"] if s["id"] == section_id
        ]
        if not effective["sections"]:
            console.print(f"[red]Section {section_id} not found in framework.[/red]")
            return

    console.print(Panel(
        f"Generating report for [bold]{profile['metadata']['name']}[/bold] ({ticker})\n"
        f"Framework: {effective['display_name']}\n"
        f"Sections: {len(effective['sections'])}",
        title="Report Generation",
    ))

    # Generate sections with progress
    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for section in effective["sections"]:
            task = progress.add_task(
                f"[{section['id']}/11] {section['name']}...",
                total=None,
            )
            from src.generator.writer import write_section
            result = write_section(
                section=section,
                company_profile=profile,
                framework=effective,
            )
            results.append(result)

            status_str = (
                f"[green]{result['word_count']} words[/green]"
                if result["status"] == "generated"
                else f"[red]{result.get('error', 'Error')}[/red]"
            )
            progress.update(task, description=f"[{section['id']}/11] {section['name']} - {status_str}")
            progress.update(task, completed=True)

    # Assemble report
    report_obj = assemble_report(
        sections=results,
        company_profile=profile,
        framework=effective,
    )

    # Save
    report_id = save_assembled_report(report_obj)
    console.print(f"\n[bold]Report assembled.[/bold] Total: {report_obj['word_count']:,} words")
    console.print(f"[dim]Report ID: {report_id}[/dim]")

    # Auto-export markdown
    md_path = export_markdown(report_obj, profile)
    report_obj["output_paths"] = {"markdown": str(md_path)}
    save_assembled_report(report_obj)

    console.print(f"[green]Markdown exported: {md_path}[/green]")
    console.print(f"\nNext steps:")
    console.print(f"  irf report qa {ticker}      # Run quality checks")
    console.print(f"  irf report view {ticker}     # View the report")
    console.print(f"  irf report export {ticker}   # Export to other formats")


@report.command("qa")
@click.argument("ticker")
def report_qa(ticker: str):
    """Run quality assurance checks on a generated report."""
    ticker = ticker.upper()
    reports = get_reports_for_company(ticker)
    if not reports:
        console.print(f"[red]No reports found for {ticker}.[/red]")
        return

    latest = reports[0]
    qa_results = run_qa_checks(latest)
    latest["qa_results"] = qa_results
    save_assembled_report(latest)

    console.print(format_qa_report(qa_results))


@report.command("view")
@click.argument("ticker")
def report_view(ticker: str):
    """View the latest generated report for a company."""
    ticker = ticker.upper()
    reports = get_reports_for_company(ticker)
    if not reports:
        console.print(f"[red]No reports found for {ticker}.[/red]")
        return

    latest = reports[0]
    md_path = latest.get("output_paths", {}).get("markdown")
    if md_path and Path(md_path).exists():
        content = Path(md_path).read_text()
        from rich.markdown import Markdown
        console.print(Markdown(content))
    else:
        # Render from stored sections
        from src.db import get_company_by_ticker
        company = get_company_by_ticker(ticker)
        if company:
            md = render_report_markdown(latest, company["profile"])
            from rich.markdown import Markdown
            console.print(Markdown(md))


@report.command("export")
@click.argument("ticker")
@click.option("--format", "fmt", type=click.Choice(["md", "docx", "pdf", "html"]), default="md")
def report_export(ticker: str, fmt: str):
    """Export a report to the specified format."""
    ticker = ticker.upper()
    reports = get_reports_for_company(ticker)
    if not reports:
        console.print(f"[red]No reports found for {ticker}.[/red]")
        return

    latest = reports[0]
    from src.db import get_company_by_ticker
    company = get_company_by_ticker(ticker)
    if company is None:
        console.print(f"[red]Company profile not found for {ticker}.[/red]")
        return

    profile = company["profile"]

    if fmt == "md":
        path = export_markdown(latest, profile)
        console.print(f"[green]Markdown exported: {path}[/green]")
    elif fmt == "docx":
        console.print("[yellow]DOCX export is planned for Phase 3.[/yellow]")
    elif fmt == "pdf":
        console.print("[yellow]PDF export is planned for Phase 3.[/yellow]")
    elif fmt == "html":
        console.print("[yellow]HTML export is planned for Phase 3.[/yellow]")


@report.command("status")
@click.argument("ticker")
def report_status(ticker: str):
    """Check the status of reports for a company."""
    ticker = ticker.upper()
    reports = get_reports_for_company(ticker)
    if not reports:
        console.print(f"[red]No reports found for {ticker}.[/red]")
        return

    table = Table(title=f"Reports for {ticker}")
    table.add_column("ID")
    table.add_column("Date")
    table.add_column("Quarter")
    table.add_column("Status")
    table.add_column("Words")
    table.add_column("Framework")

    for r in reports:
        table.add_row(
            r["id"],
            r.get("report_date", ""),
            r.get("reference_quarter", ""),
            r.get("status", ""),
            f"{r.get('word_count', 0):,}",
            r.get("framework_id", ""),
        )
    console.print(table)


# ── Research Commands ──

@main.group()
def research():
    """Research tools for data gathering."""
    pass


@research.command("financials")
@click.argument("ticker")
def research_financials(ticker: str):
    """Fetch financial data for a company."""
    from src.research.financial import fetch_company_info
    ticker = ticker.upper()

    with console.status(f"Fetching data for {ticker}..."):
        data = fetch_company_info(ticker)

    if "error" in data:
        console.print(f"[red]{data['error']}[/red]")
        return

    console.print_json(json.dumps(data, indent=2, default=str))


@research.command("peers")
@click.argument("ticker")
def research_peers(ticker: str):
    """Find and compare peer companies."""
    ticker = ticker.upper()

    from src.db import get_company_by_ticker
    company = get_company_by_ticker(ticker)
    if company is None:
        console.print(f"[red]No profile for {ticker}. Run: irf report new {ticker} --framework <id>[/red]")
        return

    profile = company["profile"]
    framework_id = profile.get("metadata", {}).get("sector_framework", "")
    fw_config = fm.get(framework_id)
    if fw_config is None:
        console.print(f"[red]Framework not found: {framework_id}[/red]")
        return

    from src.research.peers import get_peers_from_framework, fetch_peer_data, build_peer_comparison_table
    peer_groups = get_peers_from_framework(fw_config)

    if not peer_groups:
        console.print("[yellow]No peer groups defined in this framework.[/yellow]")
        return

    all_tickers = set()
    for tickers in peer_groups.values():
        all_tickers.update(tickers)
    all_tickers.discard(ticker)

    with console.status(f"Fetching peer data for {len(all_tickers)} companies..."):
        peer_data = fetch_peer_data(sorted(all_tickers))

    from rich.markdown import Markdown
    console.print(Markdown(build_peer_comparison_table(peer_data)))


@research.command("citations")
@click.argument("ticker")
def research_citations(ticker: str):
    """Show citation library for a company."""
    ticker = ticker.upper()
    reports = get_reports_for_company(ticker)
    if not reports:
        console.print(f"No reports with citations found for {ticker}.")
        return

    citations = reports[0].get("citations", [])
    if not citations:
        console.print("No citations in the latest report.")
        return

    table = Table(title=f"Citations for {ticker}")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Category")
    table.add_column("URL", max_width=50)

    for c in citations:
        table.add_row(
            str(c.get("id", "?")),
            c.get("title", "")[:40],
            c.get("category", ""),
            c.get("url", "")[:50],
        )
    console.print(table)


if __name__ == "__main__":
    main()
