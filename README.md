# TEN International Hiring Watch — EU27

MVP scaffold implementing **Part VI (Automation Architecture, Phase 1)** of
[`docs/OPERATING_MODEL.md`](docs/OPERATING_MODEL.md). It automates *discovery* only.
Every classification decision (A/B/C/D, access mechanism, editorial note) stays
human — the pipeline never writes to a field marked `HUMAN` in `ten_watch/schema.py`
(see that file's docstring for exactly how strong a guarantee that is and isn't).

## Revision note

This version fixes the original five P0 issues and adds a final publication-boundary
hardening pass: Gate 1 now fails closed unless freshness explicitly records
`is_open=True`; `source_quality` and `evidence_confidence` are strict enums; human
editorial approval (`publish_decision=yes`) is mandatory for Gates 3/4/7; Jinja HTML
autoescaping is enabled; the public glossary link resolves to a safe terminology page
while the detailed immigration-law glossary remains under specialist review; and
canonical URLs are environment-driven instead of using a placeholder domain.

## What this actually does

```
config/companies.yaml
        │
        ▼
ten_watch/scrapers/{greenhouse,lever,ashby}.py     ← hits public, no-auth ATS JSON APIs
        │
        ▼
ten_watch/pipeline/geography.py                     ← infers each vacancy's OWN country from
        │                                              its own location text; drops non-EU27,
        │                                              flags unresolved locations for a human
        ▼
ten_watch/pipeline/keyword_flag.py                  ← flags sponsor/visa/relocation language,
        │                                              extracts an evidence snippet
        ▼
ten_watch/pipeline/dedupe.py                        ← collapses exact repeats
        │
        ▼
review/queue-YYYY-MM-DD.csv                         ← HUMAN fields blank, ready for review
        │
        │   (a person fills in tier / access_mechanism / editorial_note /
        │    publish_decision / etc.,
        │    per Gates 1-8 in docs/OPERATING_MODEL.md, saves as
        │    review/queue-YYYY-MM-DD-classified.csv)
        ▼
ten_watch/pipeline/recheck_freshness.py             ← ATS-aware re-check (is the job ID still
        │                                              on the board? — stronger than HTTP 200,
        │                                              which closed postings often still return)
        ▼
ten_watch/site/build_site.py                        ← validates every row against Gates 1-8,
        │                                              FAILS THE BUILD (exit 1) if any row is
        │                                              incomplete or stale — never publishes a
        │                                              silent placeholder
        ▼
site/output/index.html + site/output/vacancies/{slug}/index.html
+ site/output/access-mechanisms/index.html            ← real escaped HTML with <title>, meta
                                                        description, canonical, og:* tags; the
                                                        public terminology page avoids publishing
                                                        the unreviewed legal-detail glossary
```

## What's verified vs. what isn't

- **Parsing/flagging/dedupe/geography/gate-validation/render-safety logic:** 37/37 tests passing
  (`tests/`), including a permanent regression test
  (`test_orchestrator_rejects_non_eu_jobs_from_a_global_company_board`) that
  reproduces the exact global-board bug from the review and proves it's fixed, and
  a manual end-to-end run proving the gate validator genuinely fails the build
  (exit code 1) for an incomplete A-tier row or a role a freshness recheck marked
  closed.
- **Live API calls:** this build's environment could not reach `boards-api.greenhouse.io`,
  `api.lever.co`, or `api.ashbyhq.com` directly (sandboxed network), so the scrapers
  are written against confirmed public documentation and tested against fixtures
  that mirror the real schemas — not yet smoke-tested against a live endpoint from
  this environment. Run the pipeline from a normal machine or inside the GitHub
  Action (which has open network) as the first real-world test.
- **`config/companies.yaml`:** the two demo entries (`Stripe`, `Monzo`) are real
  company slugs used to prove the pipeline runs against a live shape once network
  is available — Stripe specifically because it has both a US and an Ireland
  presence, a good real test that EU27 filtering works on a real board, not just
  the fixture. The EU27 companies from Issue #0 are commented-out placeholders
  with no token filled in; their ATS platform/slug was not confirmed in this
  build — don't guess a token, confirm it from the company's careers page.
- **SmartRecruiters / Workday:** still not implemented — Workday has no single
  standard public endpoint (each tenant exposes its own), so it's a per-employer
  integration rather than a generic scraper. Phase 2, per the operating model's
  own Tier 1 ranking.
- **`ten_watch/pipeline/geography.py`:** a maintained lookup table (country names +
  major EU27 and common non-EU27 city names), not a geocoding API. It resolves the
  Big 5 and rest-of-EU27 well and explicitly recognizes common non-EU locations to
  reject, but an unfamiliar city name will come back "unknown" rather than
  guessed — those rows are kept and flagged for a human to fill in the country,
  never silently dropped. Expand the lookup tables as new cities show up in real runs.

## Setup

```bash
pip install -r requirements.txt
python -m pytest tests/ -v                        # confirm the pipeline logic passes
python -m ten_watch.pipeline.build_review_queue    # first live discovery run (needs open network)
```

## Human review + publish workflow

1. Weekly, `.github/workflows/discover.yml` runs the pipeline and opens a PR with
   the new `review/queue-*.csv` (base branch `main`). Nothing in it is classified.
2. Review and fill in the classification fields **directly in that PR**, save the
   file as `review/queue-*-classified.csv`, merge to `main`.
3. Before publishing, run `python -m ten_watch.pipeline.recheck_freshness
   review/queue-*-classified.csv` — this ATS-checks every reviewed row and stamps
   `is_open` + a fresh `re_verification_date`. `.github/workflows/publish-site.yml`
   does this automatically on merge, then builds the site from the rechecked file.
4. `build_site.py` will refuse to publish (exit 1, listing every failure) unless
   freshness positively recorded `is_open=True`, `source_quality` and
   `evidence_confidence` are valid enums, a human set `publish_decision=yes` for
   Gates 3/4/7, and any A-tier role has a resolved `access_mechanism` (Gate 8).
   Fix the CSV and re-run — nothing ships silently incomplete.
5. Canonical/OG URLs come from `SITE_BASE_URL`. The publish workflow automatically
   derives the repository's GitHub Pages URL; set a repository variable named
   `SITE_BASE_URL` only if TEN later uses a custom domain.

## Repo setup — branch name matters

The publish workflow listens for pushes to **`main`** with a path filter on
`review/*-classified.csv`. Use `main` consistently:

```bash
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## Adding a company

1. Find its careers page and confirm which ATS it uses (`boards.greenhouse.io/{token}`,
   `jobs.lever.co/{token}`, or `jobs.ashbyhq.com/{token}`).
2. Add an entry to `config/companies.yaml` with `ats`, `token`, and (optional,
   informational only) `target_countries`.
3. Run the pipeline once manually and check the logs — a 404 means the token or
   ATS guess was wrong, not that the company has zero openings. The per-company
   log line also reports how many jobs were rejected as non-EU27 vs. kept — a
   company you expected to be Germany-only showing rejects is worth a second look.

## Repo layout

```
ten_watch/
  schema.py                  — VacancyRecord: AUTOMATED vs HUMAN field split (see docstring
                                for exactly what guarantee this is and isn't)
  scrapers/                   — Greenhouse, Lever, Ashby (public JSON APIs, no auth)
  pipeline/
    geography.py               — per-vacancy country inference + EU27 filtering
    keyword_flag.py             — discovery-only keyword flagging, never classifies
    dedupe.py                   — exact-repeat collapsing
    freshness.py                — ATS-aware liveness check (HTTP-200 fallback only)
    recheck_freshness.py        — CLI: re-verifies a classified CSV before publish
    build_review_queue.py       — orchestrator: fetch → geography → flag → dedupe → CSV
  site/
    build_site.py                — Gate 1-8 validator + Jinja2 HTML rendering
config/companies.yaml       — discovery target list
review/                     — pipeline output (queue-*.csv) and human-classified output
glossary/                   — access-mechanism glossary (Gate 8 reference)
docs/OPERATING_MODEL.md     — the full v2 operating model this repo implements
tests/                      — 37 tests: scrapers, geography, gates, render safety, dedupe, slugs, etc.
.github/workflows/          — weekly discovery PR + freshness-recheck-then-publish
```

## Explicitly out of scope for this MVP

Per the operating model's "do not build" list: no generic job crawler, no AI
sponsorship-probability scoring, no auto-apply, no candidate accounts, and — the
one that matters most for this codebase specifically — **no automated A/B/C/D
classification**. The schema separates automated and human fields clearly and the
pipeline never writes to the human ones, but Python doesn't type-enforce that
boundary; if it ever needs to be unbreakable, split `VacancyRecord` into a
`DiscoveredVacancy` / `ReviewedVacancy` pair. Not worth building until review
volume actually demands it.
