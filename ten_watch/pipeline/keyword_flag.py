"""
Keyword flagging — Part VI, Phase 1: "auto-flag postings containing keyword hits...
this doesn't classify, it just queues candidates for human review."

This module does exactly one thing: find postings whose text mentions sponsorship/
relocation/work-authorization language, and pull a short snippet around the first hit
so a human reviewer doesn't have to open every posting to know what to look for.

It NEVER decides A/B/C/D. That distinction (a vacancy that *asks about* sponsorship vs
one that *confirms* it) is exactly the judgment call Part II.4 reserves for a person.
"""

KEYWORDS = [
    "sponsor",
    "sponsorship",
    "visa",
    "work permit",
    "right to work",
    "relocation",
    "relocate",
    "immigration",
    "eu blue card",
    "blue card",
    "work authorization",
    "work authorisation",
]


def flag_keywords(text: str) -> list[str]:
    """Return the sorted list of keywords found in `text` (case-insensitive)."""
    if not text:
        return []
    lowered = text.lower()
    return sorted({kw for kw in KEYWORDS if kw in lowered})


def extract_snippet(text: str, keyword: str, window: int = 160) -> str:
    """Return ~`window` chars of context around the first occurrence of `keyword`."""
    if not text or not keyword:
        return ""
    lowered = text.lower()
    idx = lowered.find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window // 2)
    end = min(len(text), idx + len(keyword) + window // 2)
    snippet = text[start:end].strip()
    return " ".join(snippet.split())  # collapse whitespace/newlines


def flag_job(job: dict) -> dict:
    """Given a raw scraper job dict, attach matched_keywords + evidence_snippet."""
    text = job.get("description_text", "")
    matched = flag_keywords(text)
    job["matched_keywords"] = matched
    job["evidence_snippet"] = extract_snippet(text, matched[0]) if matched else ""
    return job
