"""
Vacancy record schema — mirrors Part II.3 of the Operating Model v2 doc,
plus the v2 additions (access_mechanism, re_verification_date, language_of_evidence).

Fields split into two groups:
  - AUTOMATED: filled by the discovery/keyword-flagging pipeline, no human judgment required.
  - HUMAN: left blank by the pipeline; a person fills these in during review (Gate 1-8).
    Nothing in this codebase ever writes to the HUMAN fields — that's the whole point.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class VacancyRecord:
    # --- AUTOMATED (pipeline-filled) ---
    company: str
    role: str
    country: str
    source_ats: str                      # greenhouse | lever | ashby | smartrecruiters | manual
    original_vacancy_url: str
    city: Optional[str] = None
    date_posted: Optional[str] = None
    raw_id: Optional[str] = None
    matched_keywords: List[str] = field(default_factory=list)
    evidence_snippet: Optional[str] = None       # auto-extracted text around the first matched keyword
    dedupe_hash: Optional[str] = None
    first_verified_date: Optional[str] = None    # date this pipeline run first saw it
    re_verification_date: Optional[str] = None   # date it was last confirmed still live (Part II.7)
    is_open: Optional[bool] = None                # result of the freshness re-check

    # --- HUMAN (left blank on purpose; filled during editorial review) ---
    profession: Optional[str] = None
    seniority: Optional[str] = None
    tier: Optional[str] = None                    # A / B / C / D
    access_mechanism: Optional[str] = None        # see glossary/access_mechanisms.md — Gate 8
    sponsorship_signal: Optional[str] = None
    relocation_signal: Optional[str] = None
    restriction_signal: Optional[str] = None
    salary: Optional[str] = None
    source_quality: Optional[str] = None          # P1 / P2 / P3
    evidence_confidence: Optional[str] = None      # Verified / Indicated / Unclear / Restricted
    editorial_note: Optional[str] = None
    language_of_evidence: Optional[str] = None     # e.g. "en" — and whether the ATS itself is English-only

    def to_dict(self) -> dict:
        return asdict(self)


REVIEW_CSV_COLUMNS = [f.name for f in VacancyRecord.__dataclass_fields__.values()]
