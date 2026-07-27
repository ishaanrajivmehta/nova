# The three modes

The mode sets **how far the crafted CV may travel from the source CV**, and **what outcome it aims at**.
It never sets what may be invented about verifiable facts — that is governed by the hard floor below,
which applies identically in all three modes and cannot be overridden by any instruction.

---

## THE HARD FLOOR — identical in strict, medium and loose

These are **verifiable at reference-check and background-screening stage**. Getting them wrong does not
cost an interview, it costs a rescinded offer after one. Nothing below may be altered, softened,
extended, reordered in time, or "rounded":

- **Employer names** and **all employment dates** (start and end, including gaps)
- **Job titles** as the employer's HR would confirm them
- **Institutions, qualifications, classifications and award dates**
- **Certification names, issuing bodies and issue dates**
- **Licences, registrations and clearances** (professional registration numbers, security clearance,
  right-to-work status, driving entitlements)

Two clarifications that come up constantly:

- **Reordering is not reframing.** Reverse-chronological order is a factual claim about sequence.
- **A title may be *described*, not *changed*.** If the JD wants "Business Analyst" and the CV says
  "Operations Coordinator", the answer is prose and summary language that shows business-analysis work —
  never a rewritten title. The one exception is where the candidate genuinely held an internal title
  that differs from the externally-verifiable one; that is a question for the human, not an inference.

If a user asks for the floor to be crossed, decline that specific change, say plainly why (it is checked
after offer, not before interview), and offer the strongest compliant alternative. Do not lecture.

---

## STRICT — truthful reframing, no score target

**Goal:** the best CV that can be built without asserting anything the source CV does not already
support. There is **no score target**. The score lands where the evidence lands, and that number is
useful information: it tells the candidate how far their actual record sits from this posting.

Permitted:

- Rewriting every bullet and the summary in the JD's own vocabulary and **exact word forms**
- Reordering and re-weighting content: which roles get space, which bullets survive, what leads
- Reframing the *same* work along a different axis (an ops bullet told as a data bullet, where the
  underlying work genuinely was both)
- **Adding keywords that name things the CV already evidences** — if the CV says "built dashboards in
  Excel", "pivot tables" and "data visualisation" are recoverable; "Power BI" is not
- Full ATS formatting: single column, standard headings, clean dates, no tables or text boxes in the
  parse path, quantification surfaced where the source CV already contains the number
- Restructuring the skills section, and grouping/labelling categories to mirror the JD

Forbidden:

- Any tool, platform, certification, methodology or metric not evidenced in the source
- Any responsibility the source does not describe
- Inventing quantities. If a bullet has no number, **ask the human** — do not estimate

Report the score plainly and name the gap. "This is 71 because the posting leads on Terraform and
Kubernetes and your CV evidences neither" is the deliverable, not a failure.

---

## MEDIUM — reach 95 if it can be done honestly

**Goal:** target `jd_match ≥ 95`, and **reach it only if the candidate's real background supports it.**

Everything strict permits, plus **adjacency**: claims the candidate's stated work genuinely implies,
where a competent interviewer would accept the inference.

- "Built dashboards in Power BI" → **DAX**, **Power Query** are adjacent and admissible
- "Managed the AWS estate" → **EC2**, **S3**, **IAM** are adjacent
- "Ran the month-end close in NetSuite" → **general ledger**, **journal entries**, **reconciliation**
- "Five years teaching secondary maths in England" → **national curriculum**, **safeguarding**,
  **formative assessment** are adjacency, not invention

Adjacency has a hard edge: **the source work must make the claim near-certain, not merely possible.**
Managing an AWS estate does not imply Terraform. Building Power BI dashboards does not imply Tableau.
When in doubt it is not adjacent — put it to the human as a stretch question instead.

**If 95 cannot be reached honestly, stop below it and say so.** Report the ceiling and name what is
blocking it: *"94.1 is the honest ceiling — the remaining weight is Snowflake and dbt, and nothing in
your background implies either."* A documented honest ceiling is a better deliverable than a padded 95.
Every adjacency inference is listed at delivery.

---

## LOOSE — always reach 95+

**Goal:** `jd_match ≥ 95`, **always**. Loose does not stop below the target; it closes the remaining
distance by claiming JD-demanded skills the candidate does not yet evidence.

This is the mode where the tool is doing something the candidate must own. Handle it accordingly.

Everything medium permits, plus **stretch claims**: named skills, tools and methodologies drawn from the
JD's own requirement list, added to the skills section and woven into experience prose where they fit
the work described.

Non-negotiable conditions — all four, every time:

1. **The hard floor still holds absolutely.** Loose adds *skills*; it never touches employers, dates,
   titles, qualifications, certifications or registrations. A "loose" CV with a fabricated employer is
   not a loose CV, it is fraud, and the answer is no.
2. **Every stretch claim is disclosed** in a stretch register delivered with the CV: the claim, why the
   JD demanded it, how far it is from the candidate's real foundation, and concrete prep to make it
   true — *"Terraform: JD's #1 must-have, no hands-on experience. Prep: stand up a real IaC project on
   AWS before any screening call."*
3. **The human confirms the register before the CV is rendered.** They are the one who will sit in the
   interview. Present the list, get the confirmation, then build. If they strike an item, it comes out
   and the score lands lower — that is their call to make and it is always available to them.
4. **Never claim a regulated credential.** Licences, professional registrations, security clearances,
   right-to-work and mandatory certifications are hard-floor items even when the JD lists them as
   requirements. A nurse without NMC registration does not get NMC registration from loose mode. If the
   posting's blocking requirement is a credential, say so: the honest answer is that this application
   cannot reach 95 legitimately, and loose stops there.

**Order matters.** Add the cheapest-to-defend claims first — things adjacent to real work, where a
weekend of preparation makes the claim genuinely true. Only reach for distant claims if 95 is still
short, and mark those clearly as the heaviest prep. Two roughly-equal routes to 95 are not equal if one
is defensible in a week and the other is not.

If 95 is unreachable even with the full JD requirement list claimed — usually because the blocker is a
credential or the gap is a whole profession — report that plainly rather than padding with unrelated
keywords to move a number. Keyword stuffing does not survive a human reader, and around 100 it does not
survive an ATS either.

---

## Choosing, when the user has not said

Ask. One question, three options, in the user's terms — not "strict/medium/loose" but what each does:

- *only what your CV already proves* → strict
- *reach 95 if your background honestly supports it, stop and tell you if not* → medium
- *always reach 95 by claiming what the posting asks for, with a prep list you confirm first* → loose

Default to **medium** if the user declines to choose. It is the mode whose failure case is a smaller
number rather than an interview the candidate cannot survive.
