"""
Geography — country inference from raw ATS location strings, and EU27 filtering.

Fixes the bug flagged in review: country was being copied from company CONFIG
("- company: X, country: DE") onto every job that company's board returned,
regardless of where the job actually was. A German company with a global board
(Berlin/London/New York/Singapore) would tag every single one of those as DE.

No geocoding API — this is a maintained lookup, not universal. It covers all
EU27 country names, the Big 5 cities plus the rest of EU27's major cities, and
explicitly recognizes the most common NON-EU locations it needs to reject (UK,
US, Switzerland, Singapore, Canada, India...).

Ambiguity handling: a location string can name more than one place ("Berlin /
Cologne / Karlsruhe / Munich" or "Berlin or London"). infer_countries() returns
every country it found rather than guessing one, so the pipeline can tell the
difference between "clearly EU27" (one EU27 hit, nothing else), "clearly reject"
(only non-EU27 hits), and "ambiguous, needs a human" (mixed, or nothing matched
at all). A false "kept as unknown" costs a reviewer thirty seconds; a false
silent drop costs a candidate a real opportunity — so unresolved locations are
always surfaced, never silently discarded.
"""

import re

EU27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT",
    "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}

_COUNTRY_NAMES = {
    "germany": "DE", "deutschland": "DE",
    "netherlands": "NL", "the netherlands": "NL", "holland": "NL",
    "poland": "PL",
    "ireland": "IE",
    "austria": "AT",
    "france": "FR",
    "spain": "ES",
    "italy": "IT",
    "portugal": "PT",
    "belgium": "BE",
    "sweden": "SE",
    "denmark": "DK",
    "finland": "FI",
    "czechia": "CZ", "czech republic": "CZ",
    "romania": "RO",
    "hungary": "HU",
    "greece": "GR",
    "bulgaria": "BG",
    "croatia": "HR",
    "slovakia": "SK",
    "slovenia": "SI",
    "lithuania": "LT",
    "latvia": "LV",
    "estonia": "EE",
    "luxembourg": "LU",
    "malta": "MT",
    "cyprus": "CY",
    # common non-EU27 names, resolved (and rejected) rather than falling through
    "united kingdom": "GB", "u.k.": "GB", "england": "GB", "scotland": "GB",
    "united states": "US", "usa": "US", "u.s.": "US",
    "switzerland": "CH",
    "canada": "CA",
    "india": "IN",
}

_CITY_NAMES = {
    # Big 5 priority (operating model Part II.1)
    "berlin": "DE", "munich": "DE", "münchen": "DE", "cologne": "DE", "köln": "DE",
    "karlsruhe": "DE", "hamburg": "DE", "frankfurt": "DE", "stuttgart": "DE", "leipzig": "DE",
    "amsterdam": "NL", "rotterdam": "NL", "utrecht": "NL", "the hague": "NL", "eindhoven": "NL",
    "warsaw": "PL", "krakow": "PL", "kraków": "PL", "wroclaw": "PL", "wrocław": "PL",
    "dublin": "IE", "cork": "IE",
    "vienna": "AT", "graz": "AT",
    # rest of EU27
    "paris": "FR", "lyon": "FR",
    "madrid": "ES", "barcelona": "ES",
    "milan": "IT", "rome": "IT",
    "lisbon": "PT", "porto": "PT",
    "brussels": "BE", "antwerp": "BE",
    "stockholm": "SE", "gothenburg": "SE",
    "copenhagen": "DK",
    "helsinki": "FI",
    "prague": "CZ",
    "bucharest": "RO",
    "budapest": "HU",
    "athens": "GR",
    "sofia": "BG",
    "zagreb": "HR",
    "bratislava": "SK",
    "ljubljana": "SI",
    "vilnius": "LT",
    "riga": "LV",
    "tallinn": "EE",
    "valletta": "MT",
    "nicosia": "CY",
    # common non-EU rejects
    "london": "GB", "manchester": "GB",
    "new york": "US", "san francisco": "US", "seattle": "US", "austin": "US",
    "zurich": "CH", "geneva": "CH",
    "singapore": "SG",
    "toronto": "CA", "vancouver": "CA",
    "bangalore": "IN", "bengaluru": "IN",
}


def infer_countries(location_text: str) -> set[str]:
    """Every country code found in `location_text` (country names and/or city names)."""
    if not location_text:
        return set()
    text = location_text.lower()
    found = set()
    for name, code in _COUNTRY_NAMES.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            found.add(code)
    for name, code in _CITY_NAMES.items():
        if re.search(rf"\b{re.escape(name)}\b", text):
            found.add(code)
    return found


def classify_location(location_text: str) -> tuple[str, str]:
    """
    Returns (status, country_value):
      ("eu27", "DE")                 — exactly one country found, and it's EU27
      ("ambiguous_eu27", "DE, GB")   — multiple countries found, at least one EU27
      ("reject", "GB")               — only non-EU27 countries found
      ("unknown", "")                — nothing matched; needs a human to fill in country
    """
    found = infer_countries(location_text)
    if not found:
        return "unknown", ""
    eu27_found = found & EU27
    non_eu27_found = found - EU27
    if eu27_found and not non_eu27_found and len(found) == 1:
        return "eu27", next(iter(eu27_found))
    if eu27_found:
        return "ambiguous_eu27", ", ".join(sorted(found))
    return "reject", ", ".join(sorted(found))
