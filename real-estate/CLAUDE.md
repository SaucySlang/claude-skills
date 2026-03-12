# Real Estate Skills - Claude Code Guidance

This guide covers the 9 production-ready real estate investing and wholesaling skills and their Python automation tools.

## Real Estate Skills Overview

**Available Skills:**
1. **probate-hunter/** - Probate lead sourcing, scoring, and outreach management (3 Python tools)
2. **cash-buyer-builder/** - Cash buyer list building, profiling, and matching (3 Python tools)
3. **comps-finder/** - Comparable sales analysis and ARV calculation (3 Python tools)
4. **deal-analyzer/** - Deal underwriting, MAO calculation, ROI analysis (3 Python tools)
5. **skip-tracer/** - Owner contact discovery, verification, and outreach sequencing (3 Python tools)
6. **offer-writer/** - Purchase offer generation, LOI drafting, term structuring (3 Python tools)
7. **seller-pitch/** - Seller appointment scripts, objection handling, rapport frameworks (3 Python tools)
8. **assignment-contract/** - Assignment contract generation, fee calculation, closing coordination (3 Python tools)
9. **deal-pipeline/** - Pipeline tracking, conversion metrics, deal velocity analysis (3 Python tools)

**Total Tools:** 27 Python automation tools, 27+ knowledge bases, 45+ templates

## Domain Focus

This skill suite targets **real estate wholesalers, investors, and acquisition teams** who need systematic workflows for:
- Off-market lead generation (probate, pre-foreclosure, absentee owners)
- Seller outreach and appointment setting
- Deal analysis and offer structuring
- Buyer list management and deal matching
- Contract assignment and closing coordination

## Python Automation Tools

### Core Analysis Tools

All tools follow the same CLI pattern:
```bash
python scripts/<tool_name>.py <data_file.json> [--format json|text] [--help]
```

### Quality Standards

All tools must:
- Use standard library only (no external dependencies)
- Support both JSON and human-readable output via `--format` flag
- Provide clear error messages for invalid input
- Return appropriate exit codes
- Process files locally (no API calls)
- Include argparse CLI with `--help` support

## Related Skills

- **Business Growth:** Revenue operations, sales engineering -> `../business-growth/`
- **Marketing:** Lead gen campaigns, content -> `../marketing-skill/`
- **Finance:** Financial analysis, valuations -> `../finance/`

---

**Last Updated:** March 2026
**Skills Deployed:** 9/9 real estate skills production-ready
**Total Tools:** 27 Python automation tools
