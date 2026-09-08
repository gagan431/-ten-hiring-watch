"""
Keyword flagging for discovery.

This module deliberately looks for immigration/work-authorisation phrases rather than
raw tokens such as ``visa`` or ``sponsor``. Raw tokens produced too many live false
positives (Visa the card network, executive sponsors, sponsorship activations, etc.).

It NEVER decides A/B/C/D. It only identifies postings worth human review and extracts
context around the first signal.
"""

# Phrase-level signals only. Keep these narrow enough to indicate candidate access,
# not generic business uses of words such as "sponsor" or "visa".
ACCESS_PHRASES = [
    "visa sponsorship",
    "visa sponsor",
    "work permit sponsorship",
    "work permit support",
    "immigration support",
    "immigration assistance",
    "work authorization",
    "work authorisation",
    "right to work",
    "require sponsorship",
    "requires sponsorship",
    "requiring sponsorship",
    "need sponsorship",
    "needs sponsorship",
    "relocation assistance",
    "relocation support",
    "relocate to",
    "eligible to work",
    "eu blue card",
    "blue card",
    "without sponsorship",
    "cannot provide sponsorship",
    "can't provide sponsorship",
    "unable to sponsor",
    "no visa sponsorship",
    "must have the right to work",
    "existing right to work",
    "responsible for obtaining",
    "eu citizenship required",
    "eea citizenship required",
]


def flag_keywords(text: str) -> list[str]:
    """Return the sorted list of access phrases found in ``text`` (case-insensitive)."""
    if not text:
        return []
    lowered = text.lower()
    return sorted({phrase for phrase in ACCESS_PHRASES if phrase in lowered})


def extract_snippet(text: str, keyword: str, window: int = 160) -> str:
    """Return ~``window`` chars of context around the first occurrence of ``keyword``."""
    if not text or not keyword:
        return ""
    lowered = text.lower()
    idx = lowered.find(keyword.lower())
    if idx == -1:
        return ""
    start = max(0, idx - window // 2)
    end = min(len(text), idx + len(keyword) + window // 2)
    snippet = text[start:end].strip()
    return " ".join(snippet.split())


def flag_job(job: dict) -> dict:
    """Attach matched access phrases + evidence snippet to one scraper job dict."""
    text = job.get("description_text", "")
    matched = flag_keywords(text)
    job["matched_keywords"] = matched
    job["evidence_snippet"] = extract_snippet(text, matched[0]) if matched else ""
    return job
