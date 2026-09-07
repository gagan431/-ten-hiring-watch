"""
Site builder — Part IV: "one evergreen page per issue... a static, indexable page per
vacancy with its evidence quote and tier, so search traffic can land on individual
verified roles even between newsletter sends."

Input: a review CSV that a HUMAN has already filled in (tier, access_mechanism,
profession, editorial_note, etc. are no longer blank). This script does not classify
anything — it only renders whatever a person already decided.

Output: site/output/
  index.md                 — the issue in the canonical v2 structure (Part II.9),
                              Reality Check lead first
  vacancies/{hash}.md       — one evergreen page per classified vacancy

Run: python -m ten_watch.site.build_site review/queue-2026-09-07-classified.csv
"""

import csv
import sys
from pathlib import Path

TIER_LABELS = {
    "A": "🟢 STRONG INTERNATIONAL-ACCESS OPPORTUNITIES",
    "B": "🟡 WORTH INVESTIGATING",
    "C": "🟠 VERIFY BEFORE INVESTING TIME",
    "D": "🔴 RESTRICTIONS TO NOTICE",
}

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "site" / "output"


def load_classified(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    # only rows a human actually classified belong in the site — anything with a
    # blank tier was left in the review queue unresolved and should not publish.
    return [r for r in rows if r.get("tier") in TIER_LABELS]


def vacancy_page(row: dict) -> str:
    lines = [
        f"# {row['role']} — {row['company']}",
        "",
        f"**Country:** {row.get('country','')}  ",
        f"**City:** {row.get('city','')}  ",
        f"**Tier:** {TIER_LABELS.get(row['tier'], row['tier'])}  ",
        f"**Access mechanism:** {row.get('access_mechanism') or 'Unspecified — verify directly'}  ",
        f"**Source:** {row.get('source_ats','')} (P-quality: {row.get('source_quality','')})  ",
        f"**Evidence confidence:** {row.get('evidence_confidence','')}  ",
        f"**Re-verified:** {row.get('re_verification_date','')}  ",
        "",
        "## Evidence",
        f"> {row.get('evidence_snippet','')}",
        "",
    ]
    if row.get("editorial_note"):
        lines += ["## TEN note", row["editorial_note"], ""]
    lines += [f"[Original vacancy]({row.get('original_vacancy_url','')})", ""]
    return "\n".join(lines)


def build_index(rows: list[dict], issue_date: str) -> str:
    d_and_sharp_b = [r for r in rows if r["tier"] == "D"][:2]
    lines = [
        "# TEN International Hiring Watch — EU27",
        f"Issue | {issue_date}",
        "",
        "## 🔍 This Week's Reality Check",
        "",
    ]
    for r in d_and_sharp_b:
        lines.append(f"- **{r['company']} — {r['role']}**: {r.get('evidence_snippet','')}")
    lines.append("")

    for tier in ["A", "B", "C", "D"]:
        tier_rows = [r for r in rows if r["tier"] == tier]
        if not tier_rows:
            continue
        lines.append(f"## {TIER_LABELS[tier]}")
        lines.append("")
        for r in tier_rows:
            slug = r["dedupe_hash"]
            lines.append(f"- [{r['company']} — {r['role']}](vacancies/{slug}.md) ({r.get('country','')})")
        lines.append("")

    lines += [
        "## About This Watch",
        "Evidence methodology: original ATS/employer evidence only, A/B/C/D confidence "
        "tiers, no sponsorship-probability scoring. Every source in this issue is an "
        "English-language ATS or careers page — a known bias, not a neutral sample. "
        "See the [access-mechanism glossary](../glossary/access_mechanisms.md).",
        "",
    ]
    return "\n".join(lines)


def build(csv_path: str, issue_date: str = ""):
    csv_path = Path(csv_path)
    rows = load_classified(csv_path)
    if not rows:
        print(f"No classified (tier-filled) rows found in {csv_path} — nothing to build.")
        return

    issue_date = issue_date or csv_path.stem.replace("queue-", "").replace("-classified", "")

    vac_dir = OUTPUT_DIR / "vacancies"
    vac_dir.mkdir(parents=True, exist_ok=True)
    for r in rows:
        (vac_dir / f"{r['dedupe_hash']}.md").write_text(vacancy_page(r), encoding="utf-8")

    (OUTPUT_DIR / "index.md").write_text(build_index(rows, issue_date), encoding="utf-8")
    print(f"Built {len(rows)} vacancy pages + index.md into {OUTPUT_DIR}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ten_watch.site.build_site <classified_review.csv>")
        sys.exit(1)
    build(sys.argv[1])
