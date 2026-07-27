---
name: score
description: Score any CV against any job description and explain the result. Use when the user wants to check, test, rate, evaluate, benchmark or measure how well a CV or resume matches a job posting, or asks "would this CV get through the ATS", "how good is my CV for this role", "what keywords am I missing". Read-only — reports match, quality, ATS parse and a ranked gap list without changing the CV.
---

# score

Measure a CV against a posting and explain what the number means. Read-only: nothing is rewritten.

Read `$NOVA_ROOT/references/scoring-notes.md` before interpreting anything.

## Locating the scripts

nova's scripts ship with the plugin, not in the user's project. Resolve the plugin root once per
session, then use absolute paths:

```bash
source "${CLAUDE_PLUGIN_ROOT:-.}/scripts/nova_root.sh"   # sets $NOVA_ROOT
bash "$NOVA_ROOT/scripts/bootstrap.sh"                   # idempotent dependency check
```

Everything below assumes `$NOVA_ROOT` is set. Reference files live at `$NOVA_ROOT/references/`.

## Inputs

- **CV file** — pdf, docx, md or txt
- **Job description** — pasted text, a file, or a URL

## Run

```bash
bash "$NOVA_ROOT/scripts/bootstrap.sh"                                    # once per session
python3 "$NOVA_ROOT/scripts/extract_cv.py" --cv "<cv>" --out /tmp/ev.json
```

Read the JD yourself and build an explicit requirement list — the gazetteer fallback is coarser than
you are. Mark essential vs desirable; postings usually say which.

Then score, passing the **real** bullets from extraction (this is not optional — heuristic segmentation
under-reads impact by several points on any Word-exported PDF):

```python
import cv_score, json
ev = json.load(open("/tmp/ev.json"))
rep = cv_score.score_pdf("<cv>", requirements=reqs, title="<posted title>", bullets=ev["bullets"])
```

For a non-PDF CV use `cv_score.score(text, ...)`; the ATS parse gate only applies to a rendered file.

## Report

Lead with the answer, then the detail.

**1 · The headline** — a band, with the tier and the ceiling:

> **72 ±3** · Stretch. Honest ceiling ≈ 78 without new evidence.

**2 · Suffix mismatches vs real gaps** — the most useful thing in the report, and the distinction most
tools get wrong:

> *Reword these — you already have them:* "mentoring" (CV says "mentored"), "analyse" (CV says
> "analysed").
> *Genuine gaps, ranked by weight:* Terraform (essential, mentioned 4×), Kubernetes (essential),
> dbt (desirable).

**3 · Quality**, with the sub-scores — impact, brevity/style, leadership/growth, ATS formatting — and
what specifically is dragging each one. "Impact is 5.2 because 17 of 22 bullets carry no number" is
actionable; "impact is 5.2" is not.

**4 · ATS parse gate** — pass or fail, and if fail, exactly what broke it.

**5 · What would move it most** — two or three concrete changes, ranked by weight recovered. Be honest
about which need new evidence and which are pure rewording.

Always print `scorer_version` alongside the score. A score without its ruler cannot be compared to
anything later.

## Interpreting

- **≥95** target zone for a tailored application. **~100** reads as keyword stuffing to a human and to
  modern semantic ATS — treat it as a warning, not a win.
- **85–95** strong. **65–85** worth applying with a good cover letter. **40–65** stretch. **<40** the
  posting is asking for a different background.
- **A wide `jd_match` → `jd_match_stemmed` gap** means the CV says the right things in the wrong words.
  Cheapest possible fix.
- **A low `quality` with a high `jd_match`** means keyword-fitted but badly written. It will pass a
  parser and lose the human.

Do not offer to rewrite the CV unless asked — that is `craft`. If the user wants both, use
`craft-and-score`.
