"""GovAId SAM.gov opportunity scraper — finds federal contracts matching a small business profile.

Phase 1: Basic SAM.gov search and keyword filtering.
Phase 2: Full-text parsing of opportunity details.
Phase 3: Gemini-powered relevance scoring (Week 2).

Usage:
    python scraper.py --naics 541715 --keywords "AI,context engine,memory" --days 30
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ----- Config -----
SAM_SEARCH_URL = "https://sam.gov/api/prod/sgs/v1/search"
USER_AGENT = "GovAId/0.1 (perseus@perseus.observer; federal-opportunity-monitor)"


def search_sam(keywords: str, naics: str = "", page: int = 0, size: int = 25) -> dict:
    """Search SAM.gov for active opportunities."""
    params = {
        "page": page,
        "size": size,
        "sort": "-modifiedDate",
        "mode": "search",
        "is_active": "true",
        "q": keywords,
    }
    if naics:
        params["naics"] = naics

    url = f"{SAM_SEARCH_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; GovAId/0.1; +https://github.com/Perseus-Computing-LLC/govaid)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://sam.gov",
        "Referer": "https://sam.gov/",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def filter_relevant(opportunities: list, keywords: list[str]) -> list[dict]:
    """Score and filter opportunities by keyword relevance."""
    scored = []
    for opp in opportunities:
        text = (
            (opp.get("title", "") or "") + " " +
            (opp.get("description", "") or "") + " " +
            (opp.get("agency", "") or "")
        ).lower()

        matches = [kw for kw in keywords if kw.lower() in text]
        score = len(matches) / len(keywords) if keywords else 0

        if score > 0:
            opp["_matched_keywords"] = matches
            opp["_relevance_score"] = score
            scored.append(opp)

    scored.sort(key=lambda x: x["_relevance_score"], reverse=True)
    return scored


def format_report(opportunities: list[dict]) -> str:
    """Format matches as a readable report."""
    if not opportunities:
        return "No matching opportunities found."

    lines = [
        f"=== GovAId SAM.gov Scan — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} ===",
        f"Matches: {len(opportunities)}",
        ""
    ]

    for i, opp in enumerate(opportunities[:20], 1):
        title = (opp.get("title", "") or "Untitled")[:100]
        agency = opp.get("agency", "Unknown")
        opp_type = opp.get("type", "Unknown")
        url = opp.get("uiLink", "")
        keywords = ", ".join(opp.get("_matched_keywords", []))
        score = opp.get("_relevance_score", 0)

        lines.append(f"{i}. [{score:.0%}] {title}")
        lines.append(f"   Agency: {agency} | Type: {opp_type}")
        if url:
            lines.append(f"   URL: https://sam.gov{url}")
        lines.append(f"   Keywords: {keywords}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GovAId SAM.gov scraper")
    parser.add_argument("--naics", default="541715", help="NAICS code")
    parser.add_argument("--keywords", default="artificial intelligence,AI,software,infrastructure",
                        help="Comma-separated keywords")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--page", type=int, default=0, help="Results page")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",")]
    query = " OR ".join(keywords)

    print(f"Searching SAM.gov for: {query}", file=sys.stderr)
    print(f"NAICS: {args.naics}", file=sys.stderr)

    results = search_sam(query, naics=args.naics, page=args.page)

    if "error" in results:
        print(json.dumps(results))
        sys.exit(1)

    embedded = results.get("_embedded", {})
    opportunities = embedded.get("results", [])

    total = results.get("totalElements", len(opportunities))
    print(f"Total results: {total}", file=sys.stderr)

    relevant = filter_relevant(opportunities, keywords)

    if args.json:
        print(json.dumps(relevant, indent=2))
    else:
        print(format_report(relevant))


if __name__ == "__main__":
    main()
