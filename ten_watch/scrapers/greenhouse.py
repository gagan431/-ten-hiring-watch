"""
Greenhouse public Job Board API.

Endpoint:  GET https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
Auth:      none (read-only, public)
Shape:     {"meta": {"total": N}, "jobs": [ {id, title, location:{name}, absolute_url,
                                              updated_at, content (HTML, double-escaped), ...} ]}

Board token = the slug in boards.greenhouse.io/{token} — find it on the company's careers page.

Known quirk: `content` comes back HTML-escaped (you'll see &lt;p&gt; instead of <p>),
so it must be run through html.unescape() before any keyword scan or it will silently
miss matches inside escaped tags.
"""

import html
import logging

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


def fetch_greenhouse_jobs(board_token: str, timeout: int = 20) -> list[dict]:
    url = BASE_URL.format(token=board_token)
    try:
        resp = requests.get(url, params={"content": "true"}, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning("Greenhouse request failed for token=%s: %s", board_token, exc)
        return []

    if resp.status_code == 404:
        logger.warning(
            "Greenhouse 404 for token=%s — wrong token, or this company isn't on Greenhouse.",
            board_token,
        )
        return []
    resp.raise_for_status()

    data = resp.json()
    jobs = data.get("jobs", [])
    if not jobs:
        logger.info(
            "Greenhouse token=%s returned 0 jobs — could mean zero current openings, "
            "OR a bad token. Verify manually before treating as 'not hiring'.",
            board_token,
        )

    out = []
    for job in jobs:
        out.append({
            "source_ats": "greenhouse",
            "company": board_token,
            "role": job.get("title"),
            "city_raw": (job.get("location") or {}).get("name"),
            "original_vacancy_url": job.get("absolute_url"),
            "date_posted": job.get("updated_at"),
            "raw_id": str(job.get("id")),
            "description_text": html.unescape(job.get("content") or ""),
        })
    return out
