"""
Freshness / re-verification — Part II.7.

Fixed per review: a plain HTTP GET returning 200 does NOT reliably mean a posting
is still open — many ATS-hosted pages keep returning 200 after a role closes and
just hide the Apply button client-side. Prefer asking the ATS API directly "is this
job ID still in the current board listing?" — that's the same data source the
discovery pipeline already trusts, so re-using it for freshness is consistent rather
than introducing a second, weaker source of truth. HTTP-200 is kept only as a
fallback for ATSs this codebase doesn't have a fetcher for yet.
"""

import logging

import requests

from ten_watch.scrapers.greenhouse import fetch_greenhouse_jobs
from ten_watch.scrapers.lever import fetch_lever_jobs
from ten_watch.scrapers.ashby import fetch_ashby_jobs

logger = logging.getLogger(__name__)

FETCHERS = {
    "greenhouse": fetch_greenhouse_jobs,
    "lever": fetch_lever_jobs,
    "ashby": fetch_ashby_jobs,
}


def ats_still_live(source_ats: str, ats_token: str, raw_id: str) -> bool | None:
    """True/False if the ATS API confirms it either way; None if we can't check
    this ATS at all (unsupported, or missing token/id) — caller should fall back."""
    fetch_fn = FETCHERS.get(source_ats)
    if fetch_fn is None or not ats_token or not raw_id:
        return None
    current_jobs = fetch_fn(ats_token)
    current_ids = {j.get("raw_id") for j in current_jobs}
    return raw_id in current_ids


def http_still_live(url: str, timeout: int = 15) -> bool:
    """Fallback only — see module docstring for why this is weaker than ats_still_live."""
    if not url:
        return False
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        return resp.status_code == 200
    except requests.RequestException as exc:
        logger.warning("HTTP freshness check failed for %s: %s", url, exc)
        return False


def check_liveness(row: dict) -> bool:
    """Single entry point used by the recheck script — tries the ATS-aware check
    first, only falls back to HTTP-200 if that ATS isn't supported here."""
    result = ats_still_live(row.get("source_ats"), row.get("ats_token"), row.get("raw_id"))
    if result is not None:
        return result
    logger.info(
        "No ATS-aware freshness check available for source_ats=%s — falling back to HTTP 200 "
        "(weaker signal, see module docstring).", row.get("source_ats"),
    )
    return http_still_live(row.get("original_vacancy_url"))
