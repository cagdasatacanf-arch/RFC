# Investment Report Framework Creator (IRF)

A CLI tool for creating, managing, and deploying sector-specific investment analysis frameworks based on a proven 11-section institutional report structure.

## Quick Start

```bash
# Install
pip install -e .

# Initialize database and load built-in frameworks
irf init

# List available frameworks
irf framework list

# View a framework's structure
irf framework view semiconductor_fabless

# Create a new report
irf report new NVDA --framework semiconductor_fabless --quarter "Q4 FY2026"

# Generate the report (requires ANTHROPIC_API_KEY)
irf report generate NVDA

# Run quality checks
irf report qa NVDA
```

## Configuration

```bash
# Set your Anthropic API key
irf config set api_key sk-ant-...

# Or use environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# View current config
irf config show
```

## Built-in Frameworks

| Framework | Sector | Example Companies |
|-----------|--------|-------------------|
| `semiconductor_fabless` | Semiconductor (Fabless) | NVDA, AMD, AVGO, MRVL |
| `defense_aerospace` | Defense & Aerospace | KOG, RHM, SAAB, LMT, RTX |

## Framework Management

```bash
irf framework list                              # List all frameworks
irf framework view <id>                         # View framework details
irf framework create <id>                       # Create new framework
irf framework clone <source> <target>           # Clone a framework
irf framework export <id> --format json         # Export to JSON
irf framework import ./my_framework.json        # Import from file
irf framework delete <id>                       # Delete a framework
```

## Report Generation

```bash
irf report new <TICKER> --framework <id>        # Create company profile
irf report generate <TICKER>                    # Generate full report
irf report generate <TICKER> --section 4        # Generate single section
irf report qa <TICKER>                          # Quality assurance checks
irf report view <TICKER>                        # View report
irf report export <TICKER> --format md          # Export report
irf report status <TICKER>                      # Check status
```

## Research Tools

```bash
irf research financials <TICKER>                # Fetch financial data
irf research peers <TICKER>                     # Peer comparison
irf research citations <TICKER>                 # Citation library
```

## Optional Dependencies

```bash
pip install -e ".[api]"       # Anthropic API (for report generation)
pip install -e ".[finance]"   # yfinance (for financial data fetching)
pip install -e ".[all]"       # All optional deps
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Architecture

The system is built around a **base 11-section framework** (Kongsberg methodology) that sector-specific frameworks extend through section overrides:

1. Executive Summary
2. Macroeconomic & Geopolitical Backdrop
3. Strategic Positioning
4. Operational Analysis - Primary
5. Operational Analysis - Secondary
6. Associated Companies & Ecosystem
7. Financial Performance Deep Dive
8. Masterclass
9. Peer Valuation & Comparative Analysis
10. Risks & Challenges
11. Conclusion & Monitoring Framework
