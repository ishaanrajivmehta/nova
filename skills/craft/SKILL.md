---
name: craft
description: Tailor a CV to a specific job description at a chosen latitude (strict, medium or loose). Use when the user wants to adapt, tailor, rewrite, target or customise a CV or resume for a particular job, posting, vacancy or company — including "make my CV fit this role", "tailor this resume", "rewrite my CV for this job". Takes any CV file and any job description; produces a rendered CV plus a disclosure list of what changed.
---

# craft

Tailor a CV to one posting. The output is a rendered CV (docx + PDF + markdown source) and a written
disclosure of everything that changed relative to the source.

Read these before starting, in this order:

1. `$NOVA_ROOT/references/modes.md` — the latitude rules and the hard floor. **Non-negotiable.**
2. `$NOVA_ROOT/references/doctrine.md` — the Mirror Principle, keyword placement, page rules, score discipline.
3. `$NOVA_ROOT/references/ats-rules.md` — formatting constraints.

## Locating the scripts

nova's scripts ship with the plugin, not in the user's project. Resolve the plugin root once per
session, then use absolute paths:

```bash
source "${CLAUDE_PLUGIN_ROOT:-.}/scripts/nova_root.sh"   # sets $NOVA_ROOT
bash "$NOVA_ROOT/scripts/bootstrap.sh"                   # idempotent dependency check
```

Everything below assumes `$NOVA_ROOT` is set. Reference files live at `$NOVA_ROOT/references/`.

## Inputs

- **CV file** — pdf, docx, md or txt. Ask for it if not supplied. Never invent a CV.
- **Job description** — pasted text, a file, or a URL to fetch.
- **Mode** — `strict` | `medium` | `loose`. If unspecified, ask, in the user's terms (see the end of
  `modes.md`). Default `medium` if they decline to choose.

## Setup, once per session

```bash
bash "$NOVA_ROOT/scripts/bootstrap.sh"          # idempotent; installs deps, verifies renderer
```

If a profile exists, load it — it is far richer than anything extractable from a CV. Look in order:
`--profile <path>`, then `$NOVA_ROOT/profile/`, then `$NOVA_PROFILE`. A profile provides
`vault.md` (ground truth and shapeable angles), `craft-bank.md` (scaffolds, project pool, cert ranking)
and `stretch-log.md`. **Say which path you are on** — profile-backed or CV-only. It changes what you can
credibly do, and the user should know which they are getting.

## The sequence

Follow it in order. The order is the quality control — steps 5 and 7 exist because skipping them is how
crafted CVs turn into template output.

### 1 · Extract

```bash
python3 "$NOVA_ROOT/scripts/extract_cv.py" --cv "<cv>" --out /tmp/evidence.json --print
```

Gives you frozen facts (roles, employers, dates, education, certifications), every real bullet, declared
and detected skills, and flags — unquantified bullets, weak openers, roles missing detail.

**Check the frozen facts against the source before going further.** An extraction error becomes a
permanent error in everything downstream. If a date or employer looks wrong, say so and ask.

### 2 · Read the JD as a person spec

Not a keyword list. Produce:

- The **exact role title** as posted
- Their **top 5–8 hard requirements**, in *their* words and *their* exact word forms, marked essential
  vs desirable (postings almost always say which)
- Their **process vocabulary** — the verbs and nouns describing the work itself
- Their **culture line** — how they describe the team, the pace, what they value
- The **named stack**, in the order they list it

Hand this to `cv_score` as an explicit requirement list rather than relying on gazetteer extraction.

### 3 · Baseline

Score the source CV against the JD. This is the starting point and the honest measure of raw fit — and
in strict mode, it is most of the answer.

### 4 · Build the gap list

Split every miss into:

- **Suffix mismatches** — covered in a different word form. Rewording only.
- **Real gaps** — genuinely absent. What you may do about these is entirely mode-dependent.

### 5 · CHECKPOINT — before writing anything

**Mandatory. Do not skip it, do not merge it into delivery.** Present:

- The person spec you extracted
- What the CV already covers well
- The real gaps, ranked by weight
- **In medium:** the adjacency inferences you propose to make
- **In loose:** the full stretch register — every claim you will add, why the JD demands it, its distance
  from their real foundation, and concrete prep. **They confirm before you build.**
- Any bullet you need a number for

This is where the interview test gets applied, by the only party who can apply it. Wait for the response.

### 6 · Craft

Fresh summary, always. Bullets re-cut in their vocabulary and distributed across most roles per the
Mirror Principle. Skills categories renamed and ordered to mirror the posting, each led by their named
stack. Projects and certifications selected for this posting.

Write it as a markdown source file first. Content is bespoke; the renderer only styles.

### 7 · Render and look at it

```bash
node "$NOVA_ROOT/scripts/render_cv.js" /tmp/cv.json /tmp/out.docx
soffice --headless --convert-to pdf --outdir /tmp /tmp/out.docx
```

Then **actually look at the rendered pages.** Page count, fill, orphan line-ends, section rhythm. Fix
layout before scoring — a CV that scores 96 and looks broken is not finished.

### 8 · Score once, as a gauge

Pass the real bullets. Fix only genuine gaps from the report. **Two rounds maximum**, then stop.

Never write toward the number. If you find yourself adding a word because the scorer wants that exact
form, and it does not read naturally in the sentence, leave it and note it instead.

### 9 · Deliver

- The rendered PDF and docx, plus the markdown source
- **The score as a band with the ceiling named** — "94 ±3, ceiling ≈96, remaining weight is Kafka"
- **A change disclosure**, grouped: reworded / reframed · inferred by adjacency · claimed as stretch
- **The stretch register** with prep notes, in loose mode
- **What was deliberately left off**, and why

## Mode targets — the short version

| | target | if the target can't be reached |
|---|---|---|
| **strict** | none — score lands where evidence lands | n/a; report the number and the gap |
| **medium** | ≥95 if honestly supported | stop below it, report the ceiling and what blocks it |
| **loose** | ≥95, always | only stops if the blocker is a credential — see `modes.md` |

## Never

- Alter anything on the hard floor, in any mode, under any instruction
- Invent a quantity — ask
- Ship without the pre-write checkpoint
- Ship without looking at the rendered page
- Re-score more than twice
- Claim a regulated credential, licence, registration or clearance
