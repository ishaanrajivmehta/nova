---
name: craft-and-score
description: Tailor a CV to a job description and report the before/after score in one pass. Use when the user wants a CV adapted to a posting AND wants to know how well it matches — "tailor my CV and tell me the score", "optimise this resume for this job and check it", "make it fit and show me the match rate". Combines craft and score with a hard two-round scoring cap.
---

# craft-and-score

`craft`, with a measured before and after. One skill because the loop between them needs a cap — left
open, score-chasing turns a crafted CV into keyword soup, and that has actually happened.

Read `$NOVA_ROOT/references/modes.md`, `$NOVA_ROOT/references/doctrine.md` and `$NOVA_ROOT/references/scoring-notes.md` first.

## Locating the scripts

nova's scripts ship with the plugin, not in the user's project. Resolve the plugin root once per
session, then use absolute paths:

```bash
source "${CLAUDE_PLUGIN_ROOT:-.}/scripts/nova_root.sh"   # sets $NOVA_ROOT
bash "$NOVA_ROOT/scripts/bootstrap.sh"                   # idempotent dependency check
```

Everything below assumes `$NOVA_ROOT` is set. Reference files live at `$NOVA_ROOT/references/`.

## Sequence

Follow `$NOVA_ROOT/skills/craft/SKILL.md` exactly, with these additions:

1. **Baseline is reported, not just used.** Score the source CV and show the user that number before
   crafting. It frames everything after it, and in strict mode it is most of the answer.

2. **The craft step does not see the score.** Write the CV from the person spec and the gap list.
   Enforced by sequence, because instruction alone does not hold: craft → render → look → score.

3. **Two scoring rounds. Hard cap.**
   - *Round 1* — score the rendered PDF with real bullets. Fix only entries from `real_gaps` (mode
     permitting) and reword `suffix_mismatches` where the JD's form reads naturally.
   - *Round 2* — re-render, re-score, stop. Whatever it reads, that is the number.
   - There is no round 3. If the target is still short, report the ceiling and what blocks it.

4. **Mode targets** — from `modes.md`:
   - **strict** — no target. Report where the evidence lands.
   - **medium** — ≥95 if honestly reachable; otherwise stop and name the blocker.
   - **loose** — ≥95 always, via the confirmed stretch register. Only stops short if the blocker is a
     regulated credential.

## Deliver

A before/after table, then the CV, then the disclosure:

| | before | after |
|---|---|---|
| jd_match | 61 | **95 ±3** |
| stem-aware | 64 | 97 |
| quality | 71.2 | 88.4 |
| ATS parse | pass | pass |

Then:

- **Where the lift came from**, split honestly: rewording (no new claims) · reframing existing work ·
  adjacency inference · stretch claims. A user seeing "+34" deserves to know how much of it was
  vocabulary and how much was new assertion.
- **The stretch register** with prep notes, in loose mode.
- **What was left off**, and why.
- **The ceiling**, if the target was not reached.
- **`scorer_version`**, so the number can be reproduced later.

## The trap this skill exists to avoid

A rising number feels like progress, so the instinct is one more round. Resist it. Past roughly 95 the
remaining requirements are almost always either genuinely absent — in which case only the mode's rules
can address them — or present in another word form, which is a rewording job worth one point and not
worth distorting a sentence for.

If you catch yourself adding a word purely because the scorer wants that exact form, and it does not
read naturally where you put it: leave it out, and note it in the report instead. A CV that reads like a
person wrote it at 94 beats one that reads like a tool wrote it at 99.
