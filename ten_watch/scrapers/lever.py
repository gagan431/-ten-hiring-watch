"""
Lever public postings API.

Endpoint:  GET https://api.lever.co/v0/postings/{company}?mode=json
Auth:      none (read-only, public)
Shape:     a BARE ARRAY (not wrapped in an object) of postings:
           [ {id, text (=title), categories:{location, team, commitment},
              description, descriptionPlain, lists:[{text, content}],
              hostedUrl, applyUrl, createdAt}, ... ]

`company` = the slug in jobs.lever.co/{company}.

Known quirk: a 404 here means "no Lever board found for this slug" — it does NOT
distinguish between "wrong slug" and "this company has no open Lever board at all".
The sponsorship/relocation question is very often inside a `lists` entry (custom
section), not the main description — both are scanned.
"""

import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.lever.co/v0/postings/{company}"


def fetch_lever_jobs(company: str, timeout: int = 20) -> list[dict]:
    url = BASE_URL.format(company=company)
    try:
        resp = requests.get(url, params={"mode": "json"}, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning("Lever request failed for company=%s: %s", company, exc)
        return []

    if resp.status_code == 404:
        logger.warning(
            "Lever 404 for company=%s — wrong slug, or this company isn't on Lever.",
            company,
        )
        return []
    resp.raise_for_status()

    data = resp.json()
    if not isinstance(data, list):
        logger.warning("Unexpected Lever response shape for company=%s", company)
        return []

    out = []
    for job in data:
        categories = job.get("categories", {}) or {}
        lists_text = " ".join(
            (item.get("content") or "") for item in (job.get("lists") or [])
        )
        combined_text = " ".join(
            filter(None, [job.get("descriptionPlain"), job.get("description"), lists_text])
        )
        out.append({
            "source_ats": "lever",
            "company": company,
            "role": job.get("text"),
            "city_raw": categories.get("location"),
            "original_vacancy_url": job.get("hostedUrl") or job.get("applyUrl"),
            "date_posted": job.get("createdAt"),
            "raw_id": str(job.get("id")),
            "description_text": combined_text,
        })
    return out
