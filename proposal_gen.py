"""GovAId Proposal Generator — Gemini-powered RFP response drafting.

Phase 2 of the Gemini XPRIZE build plan. Takes a SAM.gov opportunity description
and generates a compliance-ready proposal draft using Google Gemini.

Usage:
    python proposal_gen.py --opportunity '{
        "title": "AI-Powered Something",
        "agency": "DOD",
        "description": "Seeking commercial AI solutions for...",
        "naics": "541715"
    }' --company '{
        "name": "Example LLC",
        "capabilities": ["AI infrastructure", "context engines"],
        "past_performance": "MIT-licensed open source tools"
    }'

Requires: GOOGLE_API_KEY env var (Gemini API key)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# ----- Gemini API -----

GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def call_gemini(prompt: str, api_key: str) -> str:
    """Call Gemini API and return the generated text."""
    body = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 4096,
        }
    }).encode()

    url = f"{GEMINI_API}?key={api_key}"
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:500]
        return f"API ERROR {e.code}: {error_body}"
    except Exception as e:
        return f"ERROR: {e}"


# ----- Proposal Generation -----

PROPOSAL_PROMPT = """You are a federal procurement AI assistant. Generate a professional,
compliance-ready proposal draft for the small business described below, responding
to the government opportunity provided.

## Government Opportunity
Title: {opp_title}
Agency: {opp_agency}
NAICS: {opp_naics}
Description: {opp_description}

## Small Business
Name: {company_name}
Capabilities: {capabilities}
Past Performance: {past_performance}

## Instructions
Generate a proposal with these sections. Be specific and professional. Do not
invent facts — use ONLY the information provided about the company. If the
opportunity description lacks detail, acknowledge that and suggest what
additional research the business should do.

### 1. Executive Summary (2-3 sentences)
Why this business is the right choice for this opportunity.

### 2. Technical Approach (2-3 paragraphs)
How the business will deliver. Be specific about the technology and methodology.

### 3. Past Performance (1-2 paragraphs)
Relevant experience and why it matters for this opportunity.

### 4. Compliance Checklist
Key FAR/DFARS requirements that may apply and how the business will address them.

### 5. Next Steps
What the business should do to submit a complete proposal — forms needed,
registrations required (SAM.gov, etc.), and timeline considerations.

### 6. Risk Assessment
Identify 2-3 key risks and mitigation strategies.

Format with clear section headers. Use professional, direct language.
Do not use enthusiastic language like "excited" or "thrilled."
"""


def generate_proposal(opportunity: dict, company: dict, api_key: str) -> str:
    """Generate a full proposal draft."""
    prompt = PROPOSAL_PROMPT.format(
        opp_title=opportunity.get("title", "Untitled Opportunity"),
        opp_agency=opportunity.get("agency", "Unknown Agency"),
        opp_naics=opportunity.get("naics", "Not specified"),
        opp_description=opportunity.get("description", "No description provided."),
        company_name=company.get("name", "Small Business"),
        capabilities=", ".join(company.get("capabilities", ["Not specified"])),
        past_performance=company.get("past_performance", "Not specified"),
    )

    return call_gemini(prompt, api_key)


# ----- Main -----

def main():
    parser = argparse.ArgumentParser(description="GovAId Proposal Generator")
    parser.add_argument("--opportunity", type=str, required=True,
                        help="JSON string with opportunity details")
    parser.add_argument("--company", type=str, required=True,
                        help="JSON string with company profile")
    parser.add_argument("--api-key", type=str, default="",
                        help="Gemini API key (or set GOOGLE_API_KEY)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("ERROR: No Gemini API key. Set GOOGLE_API_KEY or use --api-key.",
              file=sys.stderr)
        sys.exit(1)

    try:
        opportunity = json.loads(args.opportunity)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid opportunity JSON: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        company = json.loads(args.company)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid company JSON: {e}", file=sys.stderr)
        sys.exit(1)

    print("=" * 72)
    print(f"  PROPOSAL DRAFT — {opportunity.get('title', 'Untitled')}")
    print(f"  Prepared for: {company.get('name', 'Small Business')}")
    print(f"  Agency: {opportunity.get('agency', 'Unknown')}")
    print(f"  Generated: {__import__('datetime').datetime.now().isoformat()}")
    print("=" * 72)
    print()

    proposal = generate_proposal(opportunity, company, api_key)
    print(proposal)

    print()
    print("---")
    print("DISCLAIMER: This is an AI-generated draft. Review for accuracy, completeness,")
    print("and compliance before submission. Verify all FAR/DFARS requirements with a")
    print("government contracting professional.")


if __name__ == "__main__":
    main()
