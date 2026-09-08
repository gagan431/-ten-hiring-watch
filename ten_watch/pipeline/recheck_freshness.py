"""
Re-verification pass — Part II.7, now actually wired into the workflow (previously
freshness.py existed but nothing called it, flagged directly in review).

Run this against a classified CSV before it's carried into a new issue, and before
publish. It stamps a fresh re_verification_date on every row and sets is_open, which
build_site.py's Gate 1 check then enforces — a row marked is_open=False fails the
publish build rather than shipping stale.

Run: python -m ten_watch.pipeline.recheck_freshness review/queue-2026-09-07-classified.csv
"""

import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ten_watch.pipeline.freshness import check_liveness
from ten_watch.schema import REVIEW_CSV_COLUMNS


def recheck(csv_path: Path) -> Path:
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    today = date.today().isoformat()
    dropped = []
    for row in rows:
        if not row.get("tier"):
            continue  # not yet reviewed — nothing to re-verify
        live = check_liveness(row)
        row["is_open"] = str(live)
        row["re_verification_date"] = today
        if not live:
            dropped.append(f"{row.get('company')} — {row.get('role')} ({row.get('tier')}-tier)")

    out_path = csv_path.with_name(csv_path.stem + "-rechecked.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    if dropped:
        print("No longer live — will fail Gate 1 at publish time unless pulled or updated:")
        for d in dropped:
            print(f"  - {d}")
    print(f"Wrote {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ten_watch.pipeline.recheck_freshness <classified.csv>")
        sys.exit(1)
    recheck(Path(sys.argv[1]))
