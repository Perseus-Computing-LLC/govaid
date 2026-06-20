# GovAId

> AI-powered government contracting assistant for small businesses.
> **Gemini XPRIZE 2026 entry.** Built by Perseus Computing LLC.

GovAId helps small businesses find, understand, and win federal contracts. It uses
Google Gemini for proposal generation, Perseus for live context grounding, and Mimir
for persistent memory.

## The Problem

The US government awards $650B/year in contracts — 23% set aside for small business.
But most small businesses can't navigate:

- SAM.gov registration (2-4 weeks, multiple agencies)
- Finding relevant RFPs across dozens of agency portals
- Writing compliant proposals (thousands of pages of FAR/DFARS regulations)
- Tracking deadlines, amendments, and communications

## The Solution

1. **Onboard** — Analyze your NAICS codes, capabilities, past performance
2. **Monitor** — Scan SAM.gov, SBIR.gov, and agency portals for matches
3. **Generate** — Gemini-powered proposal drafts with compliance checks
4. **Track** — Mimir-backed persistent memory for deadlines, status, history
5. **Win** — Higher quality proposals, more submissions, better hit rate

## Architecture

```
Small Business → GovAId Dashboard → Gemini (proposal gen)
                                  → Perseus (live context)
                                  → Mimir (persistent memory)
                                  → SAM.gov API (RFP data)
                                  → SBIR.gov (topic data)
```

## Tech Stack

| Component | Technology |
|---|---|
| AI | Google Gemini (via AI Studio) |
| Context | Perseus (live context engine) |
| Memory | Mimir (persistent memory MCP) |
| Hosting | Google Cloud |
| Frontend | Stitch (design) + React |
| Video | Flow + Pomelli |

## Status

🟡 **Week 1 of 8** — Repo created, architecture defined, SAM.gov scraper next.

## Competition

[Build with Gemini XPRIZE](https://www.geminixprize.com) — $2,000,000 in prizes.
90 days to build a real AI-native business. Deadline: August 17, 2026.

## License

MIT — see [LICENSE](LICENSE).
