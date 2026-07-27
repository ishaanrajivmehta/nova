#!/usr/bin/env python3
"""
run_goldenset.py — the regression that guards the scorer.

Run this after ANY change to the gazetteer, synonyms, wordlists, weights or matching logic.
It scores a fixed set of CV/JD pairs and fails if a score leaves its expected band.

Why it exists: the predecessor engine ran for weeks with a corrupted gazetteer — `learn.py` had
auto-promoted grammar fragments ("the data", "ability to", "stakeholders.") into hard_skills at
full weight, distorting JD-match by up to 22 points on a single pair, and nobody noticed because
nothing re-measured a known-good answer. A first attempt at cleaning it then over-corrected and
stripped real skills ("machine learning", "computer vision"). Both classes of error are caught
here in under a second.

Bands are deliberately WIDE. This is a drift alarm, not a spec: it should fire when the ruler
moves, and stay quiet when a term is legitimately added.

  python3 run_goldenset.py            # run, print a table, exit non-zero on failure
  python3 run_goldenset.py --update   # re-baseline (only after reviewing WHY a score moved)
"""
from __future__ import annotations
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))
import cv_score as C  # noqa: E402

CASES_DIR = os.path.join(HERE, "cases")
BASELINE = os.path.join(HERE, "baseline.json")

# Each case: expected jd_match band, and what the case is actually testing.
CASES = [
    {"id": "marketing-strong", "title": "Digital Marketing Manager", "band": [92, 100],
     "tests": "Near-perfect domain match outside data/AI. Guards marketing coverage + GA4/GTM synonyms."},
    {"id": "finance-partial", "title": "FP&A Analyst", "band": [30, 48],
     "tests": "Genuine partial fit. Verified 2026-07-27: 9 real overlaps matched (month-end close, "
              "variance analysis, NetSuite, Power BI, CIMA), 13 real FP&A gaps correctly missed "
              "(three statement modeling, DCF, rolling forecast, Anaplan). Guards both directions."},
    {"id": "engineering-weak", "title": "Structural Engineer", "band": [0, 12],
     "tests": "Adjacent-but-wrong lane (mechanical CV vs structural JD). Verified 2026-07-27: the two "
              "share NO named requirement, so 0.0 is correct. Any material rise here means the matcher "
              "has started rewarding generic overlap — the exact failure the fragment bug caused."},
    {"id": "healthcare-strong", "title": "Senior Clinical Research Associate", "band": [92, 100],
     "tests": "Regulated-domain vocabulary (GCP, TMF, SDV, EDC). Guards clinical coverage."},
]

def load(case_id, kind):
    p = os.path.join(CASES_DIR, f"{case_id}.{kind}.txt")
    with open(p, encoding="utf-8") as f:
        return f.read()

def run_one(case):
    cv, jd = load(case["id"], "cv"), load(case["id"], "jd")
    bullets = [l.lstrip("- ").strip() for l in cv.splitlines() if l.strip().startswith("- ")]
    rep = C.score(cv, jd_text=jd, title=case["title"], bullets=bullets)
    d = rep["jd_match_detail"]
    return {
        "id": case["id"],
        "jd_match": rep["jd_match"],
        "jd_match_stemmed": d.get("jd_match_stemmed"),
        "quality": rep["quality"],
        "n_requirements": d["n_requirements"],
        "real_gaps": [g["term"] for g in d.get("real_gaps", [])][:6],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="re-baseline after reviewing the diff")
    a = ap.parse_args()

    version = C.scorer_version()
    prev = json.load(open(BASELINE)) if os.path.exists(BASELINE) else {}
    prev_r = {r["id"]: r for r in prev.get("results", [])}

    results, failures = [], []
    print(f"scorer_version: {version}")
    if prev.get("scorer_version") and prev["scorer_version"] != version:
        print(f"  (baseline was taken on {prev['scorer_version']} — data files have changed)")
    print(f"\n{'case':22s} {'band':>10s} {'jd_match':>9s} {'stem':>6s} {'was':>7s} {'reqs':>5s}  verdict")
    print("-" * 78)
    for case in CASES:
        r = run_one(case)
        results.append(r)
        lo, hi = case["band"]
        ok = lo <= r["jd_match"] <= hi
        was = prev_r.get(case["id"], {}).get("jd_match")
        drift = ""
        if was is not None and abs(was - r["jd_match"]) >= 3:
            drift = f" DRIFT {r['jd_match'] - was:+.1f}"
        if not ok:
            failures.append(f"{case['id']}: {r['jd_match']} outside [{lo}, {hi}] — {case['tests']}")
        print(f"{case['id']:22s} {f'{lo}-{hi}':>10s} {r['jd_match']:9.1f} "
              f"{(r['jd_match_stemmed'] or 0):6.1f} {(was if was is not None else float('nan')):7.1f} "
              f"{r['n_requirements']:5d}  {'PASS' if ok else 'FAIL'}{drift}")

    if a.update:
        json.dump({"scorer_version": version, "results": results},
                  open(BASELINE, "w"), indent=2)
        print(f"\n[baseline updated] {BASELINE}")
        return 0

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        print("\nDo NOT re-baseline until you can explain the move. A score that jumps after a "
              "gazetteer edit usually means a term was added that should not carry hard-skill weight.")
        return 1
    print("all cases within band")
    return 0

if __name__ == "__main__":
    sys.exit(main())
