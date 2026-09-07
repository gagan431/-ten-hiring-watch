"""
Freshness / re-verification — Part II.7: "every vacancy carries a re-verification
date... A-tier roles are re-pinged at minimum once per week."

This just checks whether a URL still resolves with a 200. It cannot tell you whether
the posting still ACCEPTS applications (Gate 1, "Live") — some ATSs return 200 for a
closed posting and just hide the Apply button client-side. Treat a 200 here as
necessary, not sufficient; a human still confirms Gate 1 for anything shipping as A-tier.
"""

import logging

import requests

logger = logging.getLogger(__name__)


def is_still_live(url: str, timeout: int = 15) -> bool:
    if not url:
        return False
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True)
        return resp.status_code == 200
    except requests.RequestException as exc:
        logger.warning("Freshness check failed for %s: %s", url, exc)
        return False
