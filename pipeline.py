#!/usr/bin/env python3
"""
GovAId Pipeline — end-to-end: find SAM.gov opportunities, score them, and generate
Gemini-powered proposal drafts for the best match.

Usage:
    python pipeline.py --naics 541715 --keywords "AI,context,memory" --company company.json --match-index 0

Output: a complete proposal draft for the top-matching opportunity.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent


def run_scraper(naics: str, keywords: str) -> list[dict]:
    """Run the SAM.gov scraper and return scored opportunities."""
    result = subprocess.run(
        [sys.executable, str(REPO_DIR / "scraper.py"),
         "--naics", naics, "--keywords", keywords, "--json"],
        capture_output=True, text=True, timeout=45
    )
    if result.returncode != 0:
        print(f"Scraper error: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Scraper returned invalid JSON", file=sys.stderr)
        return []


def load_company(path: str) -> dict:
    """Load company profile from JSON file."""
    with open(path) as f:
        return json.load(f)


def run_proposal_gen(opportunity: dict, company: dict) -> str:
    """Generate a proposal draft for a specific opportunity."""
    opp_json = json.dumps({
        "title": opportunity.get("title", "Untitled"),
        "agency": opportunity.get("agency", "Unknown"),
        "naics": opportunity.get("naics", "Not specified"),
        "description": _extract_description(opportunity),
    })
    company_json = json.dumps(company)

    result = subprocess.run(
        [sys.executable, str(REPO_DIR / "proposal_gen.py"),
         "--opportunity", opp_json,
         "--company", company_json],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout


def _extract_description(opp: dict) -> str:
    """Extract human-readable description from SAM.gov opportunity."""
    descriptions = opp.get("descriptions", [])
    if descriptions:
        import re
        text = descriptions[0].get("content", "")
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2000]
    return opp.get("title", "No description")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GovAId: end-to-end proposal pipeline")
    parser.add_argument("--naics", default="541715", help="NAICS code")
    parser.add_argument("--keywords", default="artificial intelligence,AI,software", help="Search keywords")
    parser.add_argument("--company", required=True, help="Path to company profile JSON")
    parser.add_argument("--match-index", type=int, default=0, help="Which match to generate for (0 = best)")
    parser.add_argument("--dry-run", action="store_true", help="Show matches only, don't generate")
    args = parser.parse_args()

    # Validate company file
    company = load_company(args.company)
    print(f"Company: {company.get('name', 'Unknown')}", file=sys.stderr)

    # Step 1: Find opportunities
    print(f"Scanning SAM.gov for: {args.keywords}", file=sys.stderr)
    matches = run_scraper(args.naics, args.keywords)

    if not matches:
        print("No matching opportunities found.", file=sys.stderr)
        sys.exit(0)

    print(f"Found {len(matches)} matches", file=sys.stderr)

    # Show match summary
    for i, m in enumerate(matches[:5]):
        score = m.get("_relevance_score", 0)
        title = (m.get("title", "") or "Untitled")[:100]
        kw = ", ".join(m.get("_matched_keywords", []))
        print(f"  [{i}] {score:.0%} {title}", file=sys.stderr)

    if args.dry_run:
        return

    # Step 2: Pick match
    idx = args.match_index
    if idx >= len(matches):
        print(f"Match index {idx} out of range (max {len(matches)-1})", file=sys.stderr)
        sys.exit(1)

    opportunity = matches[idx]
    print(f"\nGenerating proposal for: {opportunity.get('title', 'Untitled')}", file=sys.stderr)

    # Step 3: Generate proposal
    proposal = run_proposal_gen(opportunity, company)
    print(proposal)


if __name__ == "__main__":
    main()
