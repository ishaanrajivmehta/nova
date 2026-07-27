# nova

Craft and score CVs against job descriptions, from inside Claude Code or Cowork.

Four commands:

| | what it does |
|---|---|
| `/nova:craft` | tailor a CV to one posting, at a chosen latitude |
| `/nova:score` | measure any CV against any posting, read-only |
| `/nova:craft-and-score` | both, with a before/after and a hard two-round cap |
| `/nova:setup-cvprofile` | build a reusable personal profile that improves with use |

Works on **any** CV, not just yours. PDF, docx, markdown or plain text in; docx, PDF and markdown out.

---

## Install

In Claude Code or Cowork:

```
/plugin marketplace add ishaanrajivmehta/nova
/plugin install nova@nova-cv
```

`nova` is the plugin; `nova-cv` is the marketplace this repo publishes. Restart Claude Code (or run `/reload-plugins`) and the
four commands appear.

**In Cowork**, `/plugin` is not a command. Use **Customize → Plugins → Personal plugins → + → Add
marketplace → Add from a repository**, and paste this repo's URL. You can also install a `.plugin` file
through the same **+** menu if someone sends you one.

Dependencies are checked on first use by `scripts/bootstrap.sh`, which is idempotent and safe to re-run.
Python 3 is required. Node and LibreOffice are needed to render docx and PDF — without them nova still
scores and still writes markdown, but can't produce the final documents. The scorer degrades gracefully
if `rapidfuzz` or `scikit-learn` are missing, though scores get coarser; the bootstrap tells you exactly
what's absent.

**Without installing:** clone the repo and point Claude at it — `git clone`, then ask Claude to read
`skills/craft/SKILL.md` and follow it. The scripts work standalone.

---

## The three modes

The mode sets how far the crafted CV may travel from the source, and what outcome it aims at.

**`strict` — truthful reframing, no score target.** Rewrites bullets and summary in the posting's exact
vocabulary, reorders and re-weights content, reframes the same work along a different axis, applies full
ATS formatting, and adds keywords for things the CV *already evidences*. Nothing is asserted that the
source doesn't support. The score lands where the evidence lands, and that number is the useful output:
it tells you how far your real record sits from this posting.

**`medium` — reach 95 if it can be done honestly.** Everything strict does, plus *adjacency*: claims your
stated work genuinely implies. "Built dashboards in Power BI" implies DAX and Power Query. It does not
imply Tableau. If 95 can't be reached honestly, it stops below and names what's blocking — a documented
honest ceiling rather than a padded number.

**`loose` — always reach 95+.** Closes the remaining distance by claiming skills from the posting's own
requirement list that you don't yet evidence. Every added claim is disclosed in a stretch register with
prep notes, **and you confirm the list before anything is rendered.**

### What no mode will do

There is a hard floor, identical in all three, that no instruction overrides:

- Employer names and all employment dates
- Job titles as HR would confirm them
- Institutions, qualifications, classifications and award dates
- Certification names, issuing bodies and issue dates
- Licences, professional registrations and clearances

These are the things checked *after* an offer, not before an interview. Getting them wrong doesn't cost
you a callback — it costs you the job you already accepted. Loose mode adds *skills*; it never touches
any of the above, and it will not claim a regulated credential under any framing.

**Loose puts claims on your CV you'll need to answer for.** That's the point of the mode and it's a
legitimate thing to want — most people can genuinely do more than their CV proves, and a weekend of
preparation often makes a stretch claim true. But you are the one in the interview. That's why the
register exists, why you confirm it before rendering, and why every claim ships with concrete prep.

---

## What's under it

**`scripts/cv_score.py`** — hybrid JD-match (importance-weighted requirement coverage, hard skills ~3x
soft, frequency-weighted, exact + variant + fuzzy + ontology matching), a quality checklist across
Impact / Brevity / Leadership / ATS-formatting, and an ATS parse gate run on the rendered PDF.

It reports `jd_match` (literal — what a keyword-matching ATS sees) *and* `jd_match_stemmed` (what a human
or semantic ATS sees), and splits every miss into **suffix mismatches** (you have it, wrong word form —
reword) and **real gaps** (genuinely absent). Conflating those two is how CVs end up stuffed.

**`scripts/extract_cv.py`** — turns any CV into a structured evidence scaffold: frozen facts, real
bullets, declared and detected skills, unquantified-bullet flags. Deterministic, and deliberately
inference-free — it reads what's on the page and marks the rest as questions.

**`scripts/data/`** — a 829-term gazetteer across 13 domains (data/AI, software, marketing, sales,
finance, HR, legal, healthcare, education, public sector, operations/supply chain, physical engineering,
design/creative, hospitality/retail) plus 387 canonical terms mapped to 805 surface variants and
acronyms, because real ATS don't expand `GA4` → `Google Analytics 4` for you. Bare single-word variants
that are common English (`sits`, `canvas`, `prevent`, `send`, `resolve`) are deliberately excluded — they
fire on ordinary prose in other domains and manufacture phantom requirements.

**`goldenset/`** — four verified CV/JD pairs with expected score bands, and a runner that fails on drift.

---

## The golden set exists for a reason

The engine nova is built on ran for weeks with a corrupted keyword gazetteer. A learning routine had
been auto-promoting frequent n-grams into the hard-skill list with no validation, so grammar fragments —
`the data`, `ability to`, `stakeholders.`, `analyst london` — were carrying full hard-skill weight. On
one measured CV/JD pair it dropped a genuine 100 to 77.9, because 7 of 26 "requirements" were phantoms.
Nobody noticed, because nothing ever re-measured a known-good answer.

The first attempt to clean it then over-corrected and stripped real skills — `machine learning`,
`computer vision`, `user stories` — which the regression caught immediately.

So: **run the golden set after any change** to the gazetteer, synonyms, wordlists or matching logic.

```bash
python3 goldenset/run_goldenset.py
```

Every score also carries a `scorer_version` — a hash of the data files. Record it. A score without its
ruler can't be compared to anything later, and a learning loop that mutates the ruler between runs makes
your own history unreadable.

---

## The personal profile

`/nova:setup-cvprofile` builds a local vault: your confirmed frozen facts, the shapeable angles behind
each role, off-CV work, quantifications, and skills sorted into *can defend today* / *partial* / *could
ramp in a weekend* — which maps directly onto the three modes.

Auto-learn is on by default and tiered: JDs and scores are logged automatically; vocabulary is promoted
into **your** overlay only, behind the same validation gate; and new facts or bullets are always
*proposed*, never written silently. The vault is a record of what you said, not a cache of what the tool
inferred.

Everything stays local. `.gitignore` refuses to track `profile/`.

---

## Honest limits

- **Thresholds are provisional.** The 95 target was calibrated in a data/AI job market. Achievable
  ceilings differ by field and seniority, which is why scores are reported as bands with the ceiling
  named rather than as a single number.
- **The scorer approximates ATS behaviour; it is not any specific ATS.** Real systems vary widely, and
  the ones that matter most are the least documented.
- **No tool can apply the interview test.** Whether you can talk about a line for two minutes is
  something only you know. That's why the pre-write checkpoint is mandatory and why loose mode requires
  explicit confirmation.

MIT licensed. Issues and PRs welcome — especially domain gazetteer coverage outside the domains above,
and golden-set cases from fields that aren't yet represented.
