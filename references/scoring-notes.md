# Reading the score

`scripts/cv_score.py` returns three things and a version stamp. Read all four.

```
python3 scripts/cv_score.py --cv cv.pdf --jd jd.txt --title "Data Analyst" --out report.json
```

## The numbers

- **`jd_match` (0–100)** — importance-weighted coverage of the JD's requirements. Hard skills and tools
  weigh ~3x a soft skill; the job title weighs most; frequency in the JD raises weight. This is the
  number of record. It is **literal**: it mirrors what a keyword-matching ATS sees.
- **`jd_match_stemmed`** — the same coverage under light morphological normalisation. This is closer to
  what a human reader or a modern semantic ATS sees.
- **`quality` (0–100)** — a weighted checklist over Impact (0.34), Brevity/Style (0.22),
  Leadership/Growth (0.16) and ATS formatting (0.28). JD-agnostic: it measures whether the CV is *well
  written*, not whether it fits.
- **`ats_parse_ok`** — a hard gate run on the rendered PDF. Text extractable, page count sane, fill
  sensible. If this fails, nothing else matters.
- **`scorer_version`** — a hash of the gazetteer, synonyms and wordlists. **Record it with every score.**

## `suffix_mismatches` vs `real_gaps` — the important distinction

A missing keyword is one of two very different things, and treating them the same is how CVs get
stuffed.

- **`suffix_mismatches`** — the requirement *is* covered, in a different word form. The JD says
  "mentoring", the CV says "mentored". **Fix by rewording**, if the JD's form reads naturally in the
  sentence. Never add evidence for these; the evidence is already there.
- **`real_gaps`** — the requirement is genuinely absent. These are the only entries that need new
  content, and what you may do about them is entirely governed by the mode (`references/modes.md`).

Chasing suffix mismatches as if they were gaps is what produces CVs that read like they were written by
a keyword tool. They were.

## Known behaviour, and why

**The literal/stemmed split is deliberate.** Real keyword-matching ATS (Taleo and its generation) do not
stem — "project manager" genuinely does not match "project management". So `jd_match` stays literal.
Modern semantic ATS and every human reader do generalise, which is what `jd_match_stemmed` estimates. A
large gap between the two numbers means the CV says the right things in the wrong words: cheap to fix,
and worth fixing.

**Always pass `bullets=`.** Heuristic bullet segmentation over PDF text splits wrapped lines and misses
Word's private-use-area bullet glyphs (``), so it over-counts bullets and under-reads impact. On a
measured example: 36 phantom bullets versus 22 real ones, and a quality score of 78.9 versus 84.4 — same
CV, purely a measurement artefact. `extract_cv.py` produces the real list; hand it to `score()`.

**Score the text, gate on the PDF.** Run `jd_match` and `quality` against extracted structure; run
`ats_parse_ok` against the rendered file. That is what each is good at.

## Requirements: supply them, don't rely on extraction

`cv_score` can auto-extract requirements from JD text using the gazetteer, but that is the *fallback*.
It is strictly better to read the JD yourself and pass an explicit requirement list:

```json
[{"term": "terraform", "surface": "Terraform", "type": "hard_skill", "freq": 4, "importance": 1.0},
 {"term": "kubernetes", "surface": "Kubernetes", "type": "hard_skill", "freq": 2}]
```

Types: `job_title` (2.4) · `hard_skill` / `tool` (1.0) · `education` (0.6) · `domain` (0.5) ·
`soft_skill` (0.3) · `other` (0.2). Use `importance` to mark what the posting calls essential versus
desirable — that distinction is usually explicit in the text and the gazetteer cannot see it.

## Report a band, not a point

Scores are not precise to a decimal. Deliver them as a range with the ceiling named:

> **94 ±3.** Honest ceiling ≈ 96 — the remaining weight is Kafka and dbt, both genuine gaps.

This is not hedging. It stops a number that is accurate to roughly ±3 from being treated as a target
accurate to 0.1, which is exactly how score-chasing starts.

## Before you trust any of it

Run the golden set:

```
python3 goldenset/run_goldenset.py
```

Four CV/JD pairs across marketing, finance, engineering and clinical research, with verified bands. Run
it after **any** change to the gazetteer, synonyms, wordlists or matching logic. The predecessor engine
ran for weeks with a corrupted gazetteer distorting scores by up to 22 points because nothing
re-measured a known-good answer.
