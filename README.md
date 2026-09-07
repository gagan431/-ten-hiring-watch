# TEN International Hiring Watch — EU27

MVP scaffold implementing **Part VI (Automation Architecture, Phase 1)** of
[`docs/OPERATING_MODEL.md`](docs/OPERATING_MODEL.md). It automates *discovery* only.
Every classification decision (A/B/C/D, access mechanism, editorial note) stays
human — that boundary is enforced in code, not just policy: the pipeline never writes
to any field marked `HUMAN` in `ten_watch/schema.py`.

## What this actually does

```
config/companies.yaml
        │
        ▼
ten_watch/scrapers/{greenhouse,lever,ashby}.py   ← hits public, no-auth ATS JSON APIs
        │
        ▼
ten_watch/pipeline/keyword_flag.py                ← flags sponsor/visa/relocation language,
        │                                            extracts an evidence snippet
        ▼
ten_watch/pipeline/dedupe.py                       ← collapses exact repeats
        │
        ▼
review/queue-YYYY-MM-DD.csv                        ← HUMAN fields blank, ready for review
        │
        │   (a person fills in tier / access_mechanism / editorial_note / etc.,
        │    per Gates 1-8 in the operating model doc, then saves as
        │    review/queue-YYYY-MM-DD-classified.csv)
        ▼
ten_watch/site/build_site.py                       ← renders classified rows only
        │
        ▼
site/output/index.md + site/output/vacancies/*.md  ← evergreen pages for Part IV distribution
```

## What's verified vs. what isn't

- **Parsing/flagging/dedupe logic:** tested end-to-end (`tests/test_pipeline.py`, 9/9
  passing) against fixtures in `tests/fixtures/` that mirror the real, documented public
  API shapes for Greenhouse, Lever, and Ashby as of this build.
- **Live API calls:** this build's environment could not reach `boards-api.greenhouse.io`,
  `api.lever.co`, or `api.ashbyhq.com` directly (sandboxed network), so the scrapers are
  written against confirmed public documentation/examples but have **not** been smoke-tested
  against a live endpoint from this environment. Run `python -m ten_watch.pipeline.build_review_queue`
  from a normal machine or inside the GitHub Action (which does have open network) as the
  first real-world test, and check the log output for 404s/empty lists before trusting a
  full run.
- **`config/companies.yaml`:** the two demo entries (`stripe`, `monzo` on Greenhouse) are
  real company slugs used only to prove the pipeline runs against a live shape once network
  is available. The EU27 companies from Issue #0 (QuantCo, Clera, GenPeach AI, Qonto, etc.)
  are listed as commented-out placeholders with **no token filled in** — their actual ATS
  platform/slug was not confirmed in this build. Don't guess a token; confirm it from the
  company's careers page before adding it live.
- **SmartRecruiters / Workday:** not implemented. SmartRecruiters has a public, paginated
  API (`api.smartrecruiters.com/v1/companies/{company}/postings`) but the job-detail response
  shape needs confirming against current docs before writing a parser. Workday has no single
  standard public endpoint — each tenant exposes its own `wday/cxs/{tenant}/{site}/jobs`
  path, which makes it a per-employer integration, not a generic scraper. Treat both as
  Phase 2 stretch goals, consistent with the operating model's own Tier 1 ranking.
- **Freshness re-check (`ten_watch/pipeline/freshness.py`):** the HTTP-200 check is
  implemented but not wired into the weekly workflow yet — add a call to `is_still_live()`
  before re-publishing any carried-over A-tier role, per Part II.7.

## Setup

```bash
pip install -r requirements.txt
python -m pytest tests/ -v          # confirm the pipeline logic still passes
python -m ten_watch.pipeline.build_review_queue   # first live run (needs open network)
```

## Human review workflow

The weekly GitHub Action (`.github/workflows/discover.yml`) runs the pipeline and opens
a PR containing the new `review/queue-*.csv`. Review and fill in the classification
fields **directly in that PR** (GitHub's own review flow doubles as the editorial gate),
save the file as `review/queue-*-classified.csv`, and merge. Merging (or a manual
dispatch) triggers `.github/workflows/publish-site.yml`, which builds the evergreen
pages and deploys them to GitHub Pages.

## Adding a company

1. Find its careers page and confirm which ATS it uses (Greenhouse/Lever/Ashby all have
   a distinctive URL pattern — `boards.greenhouse.io/{token}`, `jobs.lever.co/{token}`,
   `jobs.ashbyhq.com/{token}`).
2. Add an entry to `config/companies.yaml` with `ats`, `token`, and `country`.
3. Run the pipeline once manually and check the logs — a 404 means the token or ATS
   guess was wrong, not that the company has zero openings.

## Repo layout

```
ten_watch/
  schema.py             — VacancyRecord: AUTOMATED vs HUMAN field split
  scrapers/              — Greenhouse, Lever, Ashby (public JSON APIs, no auth)
  pipeline/               — keyword_flag, dedupe, freshness, build_review_queue (orchestrator)
  site/                   — build_site.py, renders classified CSVs to markdown
config/companies.yaml    — discovery target list
review/                  — pipeline output (queue-*.csv) and human-classified output
glossary/                — access-mechanism glossary (Gate 8 reference)
docs/OPERATING_MODEL.md  — the full v2 operating model this repo implements
tests/                   — pipeline tests against fixture data matching real API shapes
.github/workflows/       — weekly discovery PR + site publish
```

## Explicitly out of scope for this MVP

Per the operating model's "do not build" list: no generic job crawler, no AI
sponsorship-probability scoring, no auto-apply, no candidate accounts, and — the one
that matters most for this codebase specifically — **no automated A/B/C/D
classification**. If a future contributor is tempted to have a script fill in `tier`,
that's the one line not to cross; it's the entire product.
