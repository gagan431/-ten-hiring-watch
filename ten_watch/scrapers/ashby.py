"""
Ashby public Job Board API.

Endpoint:  GET https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true
Auth:      none (read-only, public)
Shape:     {"jobs": [ {id, title, department, team, location, isRemote,
                        publishedAt, jobUrl, applyUrl, descriptionHtml, compensation}, ... ]}

`board` = the name at the end of jobs.ashbyhq.com/{board}.

Missing fields come back empty rather than absent (e.g. location.country may be ""),
so don't assume a field's presence means it has a non-empty value.
"""

import logging
import re

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{board}"


def _strip_html(raw: str) -> str:
    return re.sub("<[^<]+?>", " ", raw or "")


def fetch_ashby_jobs(board: str, timeout: int = 20) -> list[dict]:
    url = BASE_URL.format(board=board)
    try:
        resp = requests.get(url, params={"includeCompensation": "true"}, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning("Ashby request failed for board=%s: %s", board, exc)
        return []

    if resp.status_code == 404:
        logger.warning("Ashby 404 for board=%s — wrong board name, or not on Ashby.", board)
        return []
    resp.raise_for_status()

    data = resp.json()
    jobs = data.get("jobs", [])

    out = []
    for job in jobs:
        out.append({
            "source_ats": "ashby",
            "company": board,
            "role": job.get("title"),
            "city_raw": job.get("location"),
            "original_vacancy_url": job.get("jobUrl") or job.get("applyUrl"),
            "date_posted": job.get("publishedAt"),
            "raw_id": str(job.get("id")),
            "description_text": _strip_html(job.get("descriptionHtml") or ""),
        })
    return out
