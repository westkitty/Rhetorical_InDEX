#!/usr/bin/env python3
"""Verify QA matrix summaries against their own rows.

Review finding O-01: `INSTRUMENT_ALPHA_TRACEABILITY.md` declared totals that did
not match the rows beneath them. Hand-counted totals drift the moment a row is
added, so they are now machine-checked.

Rules enforced:
  * every requirement row carries exactly ONE primary status
    (PASS / FAIL / UNVERIFIED / N/A) — dual statuses such as
    "UNVERIFIED (runtime); PASS (present)" are rejected, because structural
    presence must never be counted as an executed PASS (finding N-02);
  * the declared summary equals the counted rows.

Usage:
    python3 tools/check_traceability.py          # human output, exit 1 on drift
    python3 tools/check_traceability.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

VALID = ("PASS", "FAIL", "UNVERIFIED", "N/A")
_ROW = re.compile(r"^\|\s*(?P<id>[A-Z]+-\d+)\s*\|(?P<rest>.*)\|\s*$")
_SUMMARY_ROW = re.compile(r"^\|\s*(?P<status>PASS|FAIL|UNVERIFIED|N/A)\s*\|\s*(?P<count>\d+)\s*\|\s*$")

# Status position varies by table (traceability puts it last; the parity matrix
# puts it before Evidence), so the parser locates the cell that IS a bare status
# rather than trusting a column index. Exactly one such cell must exist per row —
# which is also what enforces the one-primary-status rule from finding N-02.
DOCUMENTS = (
    "INSTRUMENT_ALPHA_TRACEABILITY.md",
    "tests/prototype-parity/PARITY_MATRIX.md",
)


def _cells(rest: str) -> list[str]:
    return [c.strip() for c in rest.split("|")]


def parse_document(path: Path) -> tuple[dict[str, int], list[str]]:
    counts = {status: 0 for status in VALID}
    problems: list[str] = []

    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        match = _ROW.match(line)
        if not match:
            continue
        cells = [c for c in _cells(match.group("rest")) if c]
        bare = [c for c in cells if c in VALID]
        decorated = [
            c for c in cells
            if c not in VALID and any(re.search(rf"\b{re.escape(v)}\b", c) for v in VALID)
        ]

        if len(bare) > 1:
            problems.append(
                f"{path.name}:{lineno}: row {match.group('id')} declares multiple statuses "
                f"{bare} — exactly one primary status is required"
            )
            continue
        if not bare:
            detail = f" (found decorated status text {decorated!r})" if decorated else ""
            problems.append(
                f"{path.name}:{lineno}: row {match.group('id')} has no bare status cell{detail}; "
                "record structural presence in the evidence column instead"
            )
            continue
        if decorated:
            problems.append(
                f"{path.name}:{lineno}: row {match.group('id')} mixes a primary status with "
                f"additional status text {decorated!r} — one primary status per row"
            )
            continue
        counts[bare[0]] += 1

    return counts, problems


def parse_summary(path: Path) -> dict[str, int]:
    declared: dict[str, int] = {}
    for line in path.read_text().splitlines():
        match = _SUMMARY_ROW.match(line)
        if match:
            declared[match.group("status")] = int(match.group("count"))
    return declared


def check(path: Path) -> dict[str, Any]:
    counted, problems = parse_document(path)
    declared = parse_summary(path)
    mismatches = []
    for status in VALID:
        actual = counted[status]
        stated = declared.get(status)
        if stated is None:
            if actual:
                mismatches.append(f"{status}: {actual} rows but no summary line")
        elif stated != actual:
            mismatches.append(f"{status}: summary says {stated}, rows say {actual}")
    return {
        "document": str(path.relative_to(ROOT)),
        "counted": counted,
        "declared": declared,
        "total": sum(counted.values()),
        "problems": problems,
        "mismatches": mismatches,
        "ok": not problems and not mismatches,
    }


def run() -> list[dict[str, Any]]:
    return [check(ROOT / name) for name in DOCUMENTS]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = run()
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            state = "OK" if result["ok"] else "DRIFT"
            print(f"[{state}] {result['document']}  total rows={result['total']}")
            print(f"        counted : {result['counted']}")
            print(f"        declared: {result['declared']}")
            for problem in result["problems"]:
                print(f"        ! {problem}")
            for mismatch in result["mismatches"]:
                print(f"        ! {mismatch}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
