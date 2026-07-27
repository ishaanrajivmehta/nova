---
name: setup-cvprofile
description: Build a reusable personal CV profile so every future craft is stronger and the system improves over time. Use when the user wants to set up nova, create their CV profile, onboard, configure auto-learn, or asks "make this remember me", "set up my profile", "how do I get better results". Scaffolds a profile folder, ingests a master CV, researches context, and runs an adaptive interview.
---

# setup-cvprofile

Build the vault. A CV is a compressed artifact — it throws away the shapeable angles, the quantities
and the off-CV work that good tailoring needs. This reconstructs enough of that to make every future
`craft` materially better, and sets up the learning loop so it keeps improving.

**Resumable by design.** Save after every phase. A forty-question interrogation in one sitting gets
abandoned; a ten-minute minimum viable vault that grows over time does not.

## Locating the scripts

nova's scripts ship with the plugin, not in the user's project. Resolve the plugin root once per
session, then use absolute paths:

```bash
source "${CLAUDE_PLUGIN_ROOT:-.}/scripts/nova_root.sh"   # sets $NOVA_ROOT
bash "$NOVA_ROOT/scripts/bootstrap.sh"                   # idempotent dependency check
```

Everything below assumes `$NOVA_ROOT` is set. Reference files live at `$NOVA_ROOT/references/`.

## Phase 0 · Scaffold

Ask where it should live (default `~/.nova/profile`), then create:

```
profile/
├── profile.json      # config: default mode, auto-learn, page policy, paths
├── vault.md          # ground truth — frozen facts, bullet banks, provenance
├── craft-bank.md     # armoury — scaffolds, shapeable angles, project pool, cert ranking
├── stretch-log.md    # running stretch register with prep notes
├── corpus/           # every JD seen — the learning substrate
├── applications/     # crafted output, per role
├── data/             # this user's gazetteer overlay (grown by auto-learn)
└── history.jsonl     # every run: scores, scorer_version, decisions, what shipped
```

Tell them plainly: this is theirs, it stays local, nothing is uploaded, and the repo's `.gitignore`
refuses to track it.

## Phase 1 · Ingest the master CV, then make them correct it

Ask for their fullest CV — the master, not a tailored one.

```bash
python3 "$NOVA_ROOT/scripts/extract_cv.py" --cv "<cv>" --out profile/_extracted.json --print
```

**Show the extracted frozen facts back and require confirmation.** Employers, titles, dates,
institutions, qualifications, certifications. An extraction error here becomes permanent and
contaminates everything downstream — and date errors in particular survive for months because nobody
re-reads their own CV.

Write confirmed facts to `vault.md` as the frozen block.

## Phase 2 · Research the context — propose, never assert

For each employer, role and named tool, use web search to build context:

- **Employers** — sector, size, what they actually do. "A £40m logistics firm" frames work differently
  from "a FTSE 100 insurer", and the framing is legitimate colour.
- **Tools and platforms** — canonical names and the surface forms JDs use, seeding their synonym overlay.
- **Role titles** — what that title typically encompasses in their market. This generates *candidate*
  shapeable angles.
- **Qualifications and certifications** — correct formal titles and issuing bodies.

**The hard rule: research proposes questions, it never writes facts.**

> *"Duty Manager roles in retail usually cover rostering, cash reconciliation and escalation handling.
> Did you do any of those?"*

is right. Silently writing "rostering, cash reconciliation, escalation handling" into the vault because
the role usually involves them is **wrong** — that is inventing a work history from a job title, and it
will be found out in an interview. Every researched item enters the vault only after the human confirms
it, tagged with where it came from.

## Phase 3 · The interview — seven sweeps, adaptive, resumable

Ask in waves. Save after each. Offer "skip for now" throughout — auto-learn fills gaps later.

**Minimum viable vault = sweeps 1, 2 and 5** (~10 minutes). Everything else is optional depth.

1. **Frozen-facts lock** — confirm and seal employers, dates, titles, qualifications, certifications,
   registrations. Nothing downstream may alter these.
2. **Per-role angle sweep** — for each role: *"what else did you actually do here that isn't on the
   CV?"*, prompted by the Phase 2 research. This is the single highest-value sweep — it harvests the
   shapeable angles a CV discards, which is what the Mirror Principle needs to distribute.
3. **Off-CV work** — side projects, freelance, volunteering, internal tools, things automated, things
   built for fun. Frequently the most impressive material a person has and almost never on their CV.
4. **Quantification sweep** — every bullet without a number: *"roughly how many, how much, how fast?"*
   XYZ bullets need the Z, and the candidate is the only one who knows it. Never estimate.
5. **Skills, three buckets** — (a) can defend at interview today, (b) partial or in progress, (c) could
   ramp in a weekend. **This maps directly onto strict / medium / loose**, so the mode dial stops being
   a judgement call and becomes a lookup against their own declaration.
6. **Never-include list** — anything that must never appear: a former employer, a title they won't
   claim, personal circumstances, anything they consider private. Respect this absolutely, forever.
7. **Target roles and market** — what they're aiming at, seniority, geography. Tells auto-learn what
   corpus to build.

Write facts to `vault.md`, application-facing material to `craft-bank.md`. Every line carries its date
and source. **Append, never overwrite** — the vault is a record, not a cache.

## Phase 4 · Configure

- **Auto-learn** — on by default. Explain what it does, in tiers (below).
- **Default mode** — strict / medium / loose.
- **Page policy** — one page default, two above ~8 years.
- **Output formats** — docx, PDF, markdown.

## Phase 5 · Prove it works

Ask for a posting they're genuinely interested in. Run `craft-and-score` end to end. This validates the
install, calibrates expectations, and shows them what the profile bought versus a bare CV.

## Auto-learn — tiered, because ungated learning rots

Ungated frequency-based promotion is exactly how the predecessor engine corrupted its own gazetteer:
grammar fragments reached full hard-skill weight and distorted scores for weeks. Three tiers:

- **Tier 1 · automatic, zero risk.** Store each JD in `corpus/`. Log scores, `scorer_version`, which
  bullets and skills were used, which stretches were claimed, and outcomes where known.
- **Tier 2 · automatic behind a real gate.** Vocabulary promotion into `profile/data/` **only** — never
  the shipped base. Must pass `learn.py`'s `structural_reject_reason()`: no function words, no trailing
  punctuation, no role words, no bare generic nouns, ≤4 words, tech-shaped, and present in several
  distinct JDs. Failures park for review.
- **Tier 3 · proposed, never automatic.** Well-scoring new bullets proposed into `craft-bank.md`; facts
  revealed mid-craft ("actually I also did X") proposed into `vault.md`. Both need explicit confirmation,
  batched into a periodic digest rather than nagging every run. **The vault is truth, and truth is never
  written by inference.**

The personal overlay never merges upward into the shipped gazetteer, so one user's corpus skew cannot
affect anyone else.

## Privacy

Everything stays in their profile folder. Nothing is uploaded. The `.gitignore` refuses to track
`profile/`. If they ask what is stored, show them the files — they are plain markdown and JSON, readable
and editable by hand.
