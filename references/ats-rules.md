# ATS formatting rules

What actually breaks a parser, and what doesn't. Applies to every mode — formatting is never a truth
question.

## Structural — these genuinely break parsing

- **Single column.** Multi-column layouts are the most common cause of scrambled parses: a two-column CV
  is frequently read left-to-right across both columns, interleaving unrelated lines.
- **No tables in the parse path.** Many parsers flatten table cells in row order, so a skills table
  becomes a comma-run of fragments. Some drop them entirely.
- **No text boxes, headers or footers.** Contact details in a header are invisible to a large share of
  parsers — that is how a CV arrives with no email address attached.
- **No images, icons, logos or charts.** Skill-rating bars carry zero information to a parser and read
  as decoration to a human.
- **Text-based PDF, never a scan.** If text can't be selected in a viewer, the parser sees nothing.
  `ats_parse_ok` catches this.
- **Standard fonts.** Exotic fonts can export glyphs a parser can't map to characters.

## Sections

Use the headings parsers look for: `Summary` · `Experience` · `Education` · `Skills` · `Projects` ·
`Certifications`. Creative headings — "Where I've Made an Impact", "My Toolkit" — are invisible as
section boundaries, so everything under them gets misfiled.

Order: Summary → Experience → Skills → Education → Projects/Certifications. Experience before skills:
the reader wants to know what you did before what you know. Move Education above Experience only for
current students and recent graduates with no substantial work history.

## Dates

- One format throughout, every section. `Mar 2022 – Present`, not `03/2022` in one role and
  `March 2022` in the next.
- Right-aligned, on the same line as the title.
- **Never hide a gap by dropping months.** Year-only ranges to obscure a gap is a hard-floor violation —
  employment dates are verified. A gap is a conversation; a misrepresented date is a rescinded offer.

## Bullets

- A real bullet character. Word exports Symbol-font bullets as private-use-area glyphs (``) — harmless
  for parsing, but it defeats naive bullet segmentation, so pass `extract_cv.py`'s bullet list to the
  scorer rather than letting it guess.
- Never a manual `>` or `*` as a bullet.
- One line, or at least one and a half. A bullet with two words on the second line looks broken.

## Skills section

- Tools, technologies, platforms, named methodologies, standards, certifications. Nothing else.
- Grouped under short category labels, each led by the posting's named stack in the posting's order.
- Comma-separated within a line. No bars, no rating scales, no percentages, no star ratings.
- **No bracketed sub-module lists.** `SAP (FI, CO, MM, SD, PP)` is the single clearest signal that a CV
  was written at a scoring tool.

## Contact block

Plain text at the top of the body: name, professional title, email, phone, city, LinkedIn/portfolio. No
photo, no date of birth, no marital status, no full postal address — not required in the UK or US, and a
photo actively hurts in both.

## Page

- One page by default; two above roughly eight years, or where a regulated field genuinely needs a
  registrations or publications block. Never three.
- Fill 90–100% of the final page.
- Margins no tighter than ~1.25cm. Below that it prints badly and reads as cramped.

## File

- **PDF unless the posting asks for .docx.** Some older ATS parse .docx more reliably, and a few
  explicitly request it — follow the posting when it says.
- Name it `Firstname Lastname - Company - Role.pdf`. It becomes a filename in a recruiter's folder of
  hundreds; `CV_final_v3.pdf` is a wasted signal.

## What ATS-safe does *not* mean

It does not mean ugly. Type hierarchy, a restrained accent colour, generous section spacing and clean
alignment all survive parsing intact and are what makes a human keep reading. The constraint is
structural — one column, no tables, real text — not aesthetic.
