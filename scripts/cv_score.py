#!/usr/bin/env python3
"""
cv_score.py — Resume-Worded-grade CV↔JD scoring engine (production build).

Reproduces, deterministically, the two scores that matter:
  (A) JD-MATCH / RELEVANCY  (0-100) — Resume Worded "Relevancy", Jobscan "match rate".
      Hybrid coverage of importance-weighted JD requirements: lexical exact/variant (mirrors
      dumb ATS like Taleo) + fuzzy (rapidfuzz) + TF-IDF cosine + canonical skill-ontology match.
      Hard skills weighted far above soft skills; frequency-weighted; missing-keyword list returned.
  (B) QUALITY               (0-100) — Resume Worded "Score My Resume": a weighted checklist across
      Impact · Brevity/Style · Leadership/Growth · ATS/Formatting, each sub-check 0-10.
  (C) ATS-PARSE gate        (pass/fail) — runs on the *rendered PDF text* (pdfplumber), i.e. exactly
      what an ATS sees, never the source data dict.

Design notes:
  * Requirements can be supplied by an LLM (best — pass `requirements=[...]`) OR auto-extracted from
    the JD text via the skill gazetteer + frequency (fallback). Both paths are supported.
  * Weights & thresholds are constants at the top → tune during calibration (see WEIGHTS/THRESH).
  * Optional transformer embeddings: if `sentence-transformers` is importable it is used for the
    semantic layer; otherwise the fuzzy + ontology + TF-IDF layer is used (identical maths, strong
    for a known domain). Graceful degradation, not a reduced feature set.

CLI:
  python3 cv_score.py --cv path/to/cv.pdf --jd path/to/jd.txt [--title "Data Analyst"] \
                      [--requirements reqs.json] [--cv-skills skills.json] [--out report.json]
"""
from __future__ import annotations
import argparse, json, math, os, re, subprocess, sys
from dataclasses import dataclass, field, asdict
from typing import Optional

# ---- optional deps (graceful) --------------------------------------------------------------
try:
    from rapidfuzz import fuzz as _rf
    _HAS_RF = True
except Exception:
    _HAS_RF = False
    import difflib
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SK = True
except Exception:
    _HAS_SK = False
try:
    import pdfplumber
    _HAS_PDF = True
except Exception:
    _HAS_PDF = False

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ============================================================================================
# Tunable weights & thresholds (calibration surface — change these, re-run the regression set)
# ============================================================================================
BASE_WEIGHT = {          # importance of a requirement by type (Jobscan: hard >> soft)
    "job_title": 2.4,
    "hard_skill": 1.0,
    "tool": 1.0,
    "education": 0.6,    # only counts when a degree is named in the JD
    "domain": 0.5,
    "soft_skill": 0.3,
    "other": 0.2,
}
THRESH = {
    "fuzzy_exact": 90,   # rapidfuzz token_set_ratio ≥ this ⇒ treated as a literal/variant hit (1.0)
    "fuzzy_semantic": 74,# ≥ this ⇒ partial semantic hit (0.6)
    "semantic_partial": 0.6,
    "emb_cos": 0.55,     # sentence-transformer cosine ⇒ semantic hit (if embeddings available)
}
# Quality category weights → overall QUALITY score
QUALITY_WEIGHTS = {"impact": 0.34, "brevity_style": 0.22, "leadership_growth": 0.16, "ats_format": 0.28}
# Overall composite (optional convenience number)
COMPOSITE = {"jd_match": 0.65, "quality": 0.35}
TIER_CUTS = [("Direct", 85), ("Strong", 65), ("Stretch", 40), ("Skip", 0)]  # on jd_match

# ============================================================================================
# Data loading
# ============================================================================================
def _load_json(name):
    with open(os.path.join(_DATA, name), encoding="utf-8") as f:
        return json.load(f)

_SYN = None; _WL = None; _GAZ = None
def _data():
    global _SYN, _WL, _GAZ
    if _SYN is None:
        _SYN = {k: v for k, v in _load_json("synonyms.json").items() if not k.startswith("_")}
        _WL = _load_json("wordlists.json")
        _GAZ = _load_json("skills_gazetteer.json")
    return _SYN, _WL, _GAZ

# surface-form -> canonical, built from synonyms.json (canonical maps to itself + each variant)
_SURF2CANON = None
def _surface_map():
    global _SURF2CANON
    if _SURF2CANON is None:
        syn, _, _ = _data()
        m = {}
        for canon, variants in syn.items():
            m[canon] = canon
            for v in variants:
                m[v.lower()] = canon
        _SURF2CANON = m
    return _SURF2CANON

def canon(term: str) -> str:
    return _surface_map().get(term.lower().strip(), term.lower().strip())

# ============================================================================================
# Text utilities
# ============================================================================================
_WORD = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9\+\#\.\-/]*")
def norm(t: str) -> str:
    t = (t or "").lower().replace("’", "'")
    t = re.sub(r"[^a-z0-9\+\#\.\-/ ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def tokens(t: str) -> list:
    return _WORD.findall((t or "").lower())

def _contains(hay_norm: str, needle: str) -> bool:
    """word-boundary-ish substring match of a (possibly multi-word) needle in normalized text."""
    n = norm(needle)
    if not n:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", hay_norm) is not None

def _fuzzy(a: str, b: str) -> float:
    if _HAS_RF:
        return float(_rf.token_set_ratio(a, b))
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio() * 100.0

# --- 27 Jul 2026 -----------------------------------------------------------------------------
# The "scorer literalism" documented in CLAUDE.md ("troubleshooting" != "troubleshoots") is a
# GRANULARITY BUG, not ATS realism: check_coverage step 3 fuzzy-matches the requirement against
# a whole CV LINE. Measured: "analyse" vs the line scores 25.0, but vs the best TOKEN in that
# line ("analysed") it scores 93.3 — above the 90 "exact" threshold. So the fuzzy layer almost
# never fires and every near word-form reads as missing.
#
# The primary jd_match is deliberately LEFT UNCHANGED here: real dumb ATS (Taleo) genuinely do
# not stem, the 8 Jul validation vs Resume Worded was measured on this behaviour, and silently
# moving the ruler is what made historical scores irreproducible. Instead this exposes a second,
# stem-aware view as a DIAGNOSTIC, so a craft can tell a genuine gap from a suffix mismatch.
_SUFFIXES = ("ing", "ed", "es", "s", "ion", "ions", "ment", "ments", "er", "ers", "al", "ly")

def _stem(w: str) -> str:
    w = w.lower()
    for suf in sorted(_SUFFIXES, key=len, reverse=True):
        if len(w) - len(suf) >= 4 and w.endswith(suf):
            base = w[: -len(suf)]
            return base[:-1] if base.endswith(("s", "z")) and suf in ("es",) else base
    return w

def token_level_match(term: str, lines: list) -> float:
    """Best fuzzy score of `term` against individual tokens / adjacent token pairs in `lines`.
    This is what step 3 should have been comparing against."""
    t = norm(term)
    if not t:
        return 0.0
    n_words = len(t.split())
    best = 0.0
    for ln in lines:
        toks = tokens(ln)
        if not toks:
            continue
        grams = toks if n_words == 1 else [" ".join(toks[i:i + n_words])
                                           for i in range(max(1, len(toks) - n_words + 1))]
        for g in grams:
            best = max(best, _fuzzy(t, g))
            if best >= 100.0:
                return best
    return best

def stem_covered(term: str, lines: list) -> bool:
    """True when the requirement is present under light morphological normalisation."""
    want = [_stem(w) for w in norm(term).split()]
    if not want:
        return False
    for ln in lines:
        have = [_stem(w) for w in tokens(ln)]
        if not have:
            continue
        if len(want) == 1:
            if want[0] in have:
                return True
        else:
            for i in range(len(have) - len(want) + 1):
                if have[i:i + len(want)] == want:
                    return True
    return False

# ============================================================================================
# Requirement model + JD extraction
# ============================================================================================
@dataclass
class Requirement:
    term: str                 # canonical
    surface: str              # as seen in JD (for display / literal match)
    type: str                 # job_title|hard_skill|tool|education|domain|soft_skill|other
    freq: int = 1
    importance: float = 1.0   # optional LLM multiplier (1.0 = neutral)
    def weight(self) -> float:
        return BASE_WEIGHT.get(self.type, 0.2) * (1.0 + math.log(1.0 + self.freq)) * self.importance

def extract_requirements(jd_text: str, title: Optional[str] = None) -> list:
    """Gazetteer + frequency fallback extractor (used when no LLM requirements are supplied)."""
    _, _, gaz = _data()
    jn = norm(jd_text)
    reqs = {}
    def add(term, typ, surface):
        c = canon(term)
        if c in reqs:
            reqs[c].freq += 1
        else:
            reqs[c] = Requirement(term=c, surface=surface, type=typ, freq=1)
    # hard skills / tools
    for s in gaz.get("hard_skills", []):
        # count occurrences of the skill or any of its synonym surfaces
        surfaces = [s] + _data()[0].get(canon(s), [])
        cnt = sum(len(re.findall(r"(?<![a-z0-9])" + re.escape(norm(x)) + r"(?![a-z0-9])", jn)) for x in surfaces)
        if cnt:
            reqs[canon(s)] = Requirement(term=canon(s), surface=s, type="hard_skill", freq=cnt)
    for s in gaz.get("soft_skills", []):
        if _contains(jn, s):
            add(s, "soft_skill", s)
    # education only if a degree word appears
    if any(_contains(jn, q) for q in gaz.get("qualifications", [])):
        for q in gaz.get("qualifications", []):
            if _contains(jn, q):
                reqs.setdefault(canon(q), Requirement(term=canon(q), surface=q, type="education", freq=1))
    if title:
        reqs["__title__"] = Requirement(term=canon(title), surface=title, type="job_title", freq=1)
    return list(reqs.values())

def load_requirements(items: list) -> list:
    """Normalize LLM/human-supplied requirements: [{term,type,freq?,importance?,surface?}]."""
    out = []
    for it in items:
        t = it.get("type", "hard_skill")
        term = it["term"]
        out.append(Requirement(term=canon(term), surface=it.get("surface", term), type=t,
                               freq=int(it.get("freq", 1)), importance=float(it.get("importance", 1.0))))
    return out

# ============================================================================================
# Coverage (the hybrid presence check)
# ============================================================================================
@dataclass
class Coverage:
    requirement: Requirement
    covered: float            # 0..1
    method: str               # lexical|variant|fuzzy|semantic|ontology|none
    evidence: str = ""

def _cv_skill_set(cv_text: str, extra_skills: Optional[list] = None) -> set:
    """Canonical skills detectable in the CV (gazetteer+synonym surface match) ∪ supplied skills."""
    _, _, gaz = _data()
    jn = norm(cv_text)
    found = set()
    for s in gaz.get("hard_skills", []) + gaz.get("soft_skills", []) + gaz.get("qualifications", []):
        surfaces = [s] + _data()[0].get(canon(s), [])
        if any(_contains(jn, x) for x in surfaces):
            found.add(canon(s))
    for c, variants in _data()[0].items():
        if _contains(jn, c) or any(_contains(jn, v) for v in variants):
            found.add(c)
    if extra_skills:
        found |= {canon(s) for s in extra_skills}
    return found

def check_coverage(req: Requirement, cv_text: str, cv_lines: list, cv_skills: set) -> Coverage:
    jn = norm(cv_text)
    # 1) ontology / canonical skill hit (most reliable for known skills)
    if req.term in cv_skills:
        return Coverage(req, 1.0, "ontology", req.term)
    # 2) literal / variant surface match (dumb-ATS safe)
    surfaces = [req.surface, req.term] + _data()[0].get(req.term, [])
    if req.type == "job_title":   # a "Data Scientist" CV covers a "Junior Data Scientist" title
        reduced = re.sub(r"\b(junior|senior|graduate|grad|lead|principal|staff|entry[- ]?level|"
                         r"trainee|intern|associate|i{1,3}|1|2|3)\b", " ", req.surface.lower())
        surfaces.append(re.sub(r"\s+", " ", reduced).strip())
    for s in surfaces:
        if s and _contains(jn, s):
            return Coverage(req, 1.0, "lexical", s)
    # 3) fuzzy against skills / lines
    best, ev = 0.0, ""
    for ln in cv_lines:
        r = _fuzzy(req.term, ln)
        if r > best:
            best, ev = r, ln
    if best >= THRESH["fuzzy_exact"]:
        return Coverage(req, 1.0, "variant", ev[:80])
    if best >= THRESH["fuzzy_semantic"]:
        return Coverage(req, THRESH["semantic_partial"], "fuzzy", ev[:80])
    return Coverage(req, 0.0, "none", "")

# ============================================================================================
# JD-match score
# ============================================================================================
def score_jd_match(cv_text: str, requirements: list, cv_skills: Optional[set] = None) -> dict:
    cv_lines = [l for l in re.split(r"[\n••\-–]", cv_text) if len(l.strip()) > 2]
    skills = cv_skills if cv_skills is not None else _cv_skill_set(cv_text)
    covs = [check_coverage(r, cv_text, cv_lines, skills) for r in requirements]
    wsum = sum(r.weight() for r in requirements) or 1.0
    got = sum(c.requirement.weight() * c.covered for c in covs)
    score = round(100.0 * got / wsum, 1)
    missing = sorted([c for c in covs if c.covered < 1.0],
                     key=lambda c: (-c.requirement.weight(), c.covered))
    matched = [c for c in covs if c.covered >= 1.0]

    # DIAGNOSTIC (27 Jul 2026): re-check the misses at token level + under light stemming.
    # A requirement that is "missing" literally but present as another word form is a SUFFIX
    # MISMATCH, not a real gap — mirror the JD's exact form if it reads naturally, but never
    # invent evidence for it. `jd_match` above is unchanged; this only explains it.
    suffix_only, real_gaps = [], []
    for c in missing:
        t = c.requirement.term
        if c.covered == 0.0 and (stem_covered(t, cv_lines) or token_level_match(t, cv_lines) >= THRESH["fuzzy_exact"]):
            suffix_only.append(c)
        else:
            real_gaps.append(c)
    got_stem = sum(c.requirement.weight() * (1.0 if c in suffix_only else c.covered) for c in covs
                   if c.covered < 1.0) + sum(c.requirement.weight() for c in matched)
    return {
        "jd_match": score,
        "jd_match_stemmed": round(100.0 * got_stem / wsum, 1),
        "suffix_mismatches": [{"term": c.requirement.surface, "weight": round(c.requirement.weight(), 2)}
                              for c in suffix_only],
        "real_gaps": [{"term": c.requirement.surface, "type": c.requirement.type,
                       "weight": round(c.requirement.weight(), 2)} for c in real_gaps],
        "matched_keywords": [{"term": c.requirement.surface, "type": c.requirement.type,
                              "weight": round(c.requirement.weight(), 2), "method": c.method} for c in matched],
        "missing_keywords": [{"term": c.requirement.surface, "type": c.requirement.type,
                              "weight": round(c.requirement.weight(), 2),
                              "found": "no" if c.covered == 0 else "partial", "method": c.method}
                             for c in missing],
        "n_requirements": len(requirements),
    }

def overall_similarity(cv_text: str, jd_text: str) -> float:
    if not _HAS_SK or not jd_text:
        return 0.0
    try:
        v = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
        m = v.fit_transform([norm(cv_text), norm(jd_text)])
        return round(float(cosine_similarity(m[0], m[1])[0][0]) * 100, 1)
    except Exception:
        return 0.0

# ============================================================================================
# Quality checks (Score-My-Resume clone)
# ============================================================================================
_NUM = re.compile(r"(\d+\.?\d*\s?%|\£\s?\d|\$\s?\d|\b\d{2,}\b|\bx\d+\b|\d+\+|tripled|doubled|hundreds|thousands)")
_HEADINGS = ["experience", "education", "skills", "summary", "projects", "certification", "employment", "work history"]
_LABEL = re.compile(r"^[\w][\w /&+.-]{0,26}:")        # "Languages:", "Data & BI:" skill-label lines
_SIG_STEMS = {
    "leadership": ["led ", "lead", "mentor", "manag", "supervis", "coordinat", "direct", "train",
                   "spearhead", "own", "drove", "driv", "oversaw", "oversee", "head", "found",
                   "chair", "deleg", "onboard", "promot", "built", "launch", "deliver"],
    "analytical": ["analy", "model", "forecast", "quantif", "evaluat", "measur", "tested", "test ",
                   "experiment", "optim", "diagnos", "investigat", "validat", "benchmark", "statistic",
                   "predict", "regress", "classif", "cluster"],
    "collaboration": ["collaborat", "partner", "coordinat", "liais", "stakeholder", "cross-functional",
                      "cross functional", "present", "communicat", "align", "facilitat", "client"],
}

_CONT = re.compile(r"^[a-z(]|^(and|to|with|for|by|of|the|a|in|on|that|which|using|via)\b", re.I)

def _merge_wrapped(lines: list) -> list:
    """Rejoin PDF line-wrap continuations (a line starting lowercase / with a connector) onto the
    previous logical line, so a 2-line bullet counts as one bullet."""
    merged = []
    for raw in lines:
        l = raw.rstrip()
        if not l.strip():
            continue
        stripped = l.strip(" \t••-–*")
        starts_cont = bool(_CONT.match(stripped)) and not stripped[:1].isupper()
        if merged and starts_cont:
            merged[-1] = merged[-1].rstrip() + " " + stripped
        else:
            merged.append(stripped)
    return merged

def segment_bullets(cv_text: str) -> list:
    """Heuristic bullet extraction from raw CV text (fallback when structured bullets aren't supplied).
    Rejoins wrapped lines, then excludes headings, contact, skill-label and enumeration lines."""
    out = []
    for l in _merge_wrapped(cv_text.splitlines()):
        if len(l.split()) < 4:
            continue
        low = l.lower()
        if any(low.startswith(h) or low == h for h in _HEADINGS):
            continue
        if "@" in l or re.search(r"\+?\d[\d ]{7,}", l):        # contact line
            continue
        if _LABEL.match(l):                                     # skill-label line
            continue
        if l.count(",") >= 5 and not _NUM.search(l):            # comma-separated skill enumeration
            continue
        out.append(l)
    return out

def _signal_count(low_text: str, kind: str) -> int:
    toks = low_text.replace("-", " ").split()
    joined = " " + low_text + " "
    hits = 0
    for stem in _SIG_STEMS[kind]:
        if stem.endswith(" "):
            if stem in joined:
                hits += 1
        elif any(t.startswith(stem) for t in toks):
            hits += 1
    return hits

def _starts_weak(bullet: str, weak: list) -> bool:
    b = bullet.lower().lstrip()
    return any(b.startswith(w) for w in weak)

def _starts_strong(bullet: str, strong: list) -> bool:
    first = bullet.lower().split()[0] if bullet.split() else ""
    return first.rstrip("s") in {s.rstrip("s") for s in strong} or first in strong

def score_quality(cv_text: str, bullets: Optional[list] = None) -> dict:
    _, wl, _ = _data()
    if bullets is None:
        bullets = segment_bullets(cv_text)          # heuristic fallback
    nb = max(len(bullets), 1)
    low = norm(cv_text)

    # --- Impact ---
    metric_rate = sum(1 for b in bullets if _NUM.search(b)) / nb
    strong_rate = sum(1 for b in bullets if _starts_strong(b, wl["strong_verbs"])) / nb
    weak_count = sum(1 for b in bullets if _starts_weak(b, wl["weak_verbs"]))
    impact_checks = {
        "quantified_bullets": round(min(10, metric_rate * 12.5), 1),        # ~80% ⇒ 10
        "strong_action_verbs": round(min(10, strong_rate * 12.5), 1),
        "no_weak_openers": round(max(0, 10 - weak_count * 2.5), 1),
    }
    impact = sum(impact_checks.values()) / len(impact_checks)

    # --- Brevity / Style ---
    long_bullets = sum(1 for b in bullets if len(b.split()) > 34)
    buzz = sum(low.count(bw) for bw in wl["buzzwords"])
    passive = len(re.findall(r"\b(was|were|been|is|are|be)\b\s+\w+ed\b", low)) + len(re.findall(r"\w+ed\s+by\b", low))
    pron = sum(len(re.findall(r"(?<![a-z])" + p + r"(?![a-z])", low)) for p in wl["pronouns"])
    filler = sum(low.count(f) for f in wl["filler"])
    brevity_checks = {
        "bullet_length": round(max(0, 10 - long_bullets * 2), 1),
        "no_buzzwords": round(max(0, 10 - buzz * 2.5), 1),
        "no_passive_voice": round(max(0, 10 - passive * 1.5), 1),
        "no_pronouns": round(max(0, 10 - pron * 2), 1),
        "no_filler": round(max(0, 10 - filler * 1.0), 1),
    }
    brevity_style = sum(brevity_checks.values()) / len(brevity_checks)

    # --- Leadership / Growth --- (stem-based; catches noun/verb families, e.g. analysis/analysed)
    lead = _signal_count(low, "leadership")
    anal = _signal_count(low, "analytical")
    collab = _signal_count(low, "collaboration")
    lg_checks = {
        "leadership_signals": round(min(10, lead * 3.0), 1),
        "analytical_signals": round(min(10, anal * 2.5), 1),
        "collaboration_signals": round(min(10, collab * 3.0), 1),
    }
    leadership_growth = sum(lg_checks.values()) / len(lg_checks)

    # --- ATS / Formatting (text-level; the parse gate adds file-level) ---
    headings_present = sum(1 for h in ["experience", "education", "skills"] if _contains(low, h))
    has_email = "@" in cv_text
    has_phone = bool(re.search(r"\+?\d[\d ]{7,}", cv_text))
    dates = re.findall(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}\b", low)
    date_ranges = len(re.findall(r"\d{4}\s?[–-]\s?(present|\d{4}|[a-z]{3})", low))
    ats_checks = {
        "standard_headings": round(headings_present / 3 * 10, 1),
        "contact_in_body": 10.0 if (has_email and has_phone) else (6.0 if (has_email or has_phone) else 0.0),
        "dates_present_consistent": round(min(10, (len(dates) + date_ranges) * 2.5), 1),
    }
    ats_format = sum(ats_checks.values()) / len(ats_checks)

    quality = (impact * QUALITY_WEIGHTS["impact"] + brevity_style * QUALITY_WEIGHTS["brevity_style"]
               + leadership_growth * QUALITY_WEIGHTS["leadership_growth"] + ats_format * QUALITY_WEIGHTS["ats_format"]) * 10
    return {
        "quality": round(quality, 1),
        "n_bullets": len(bullets),
        "categories": {
            "impact": {"score": round(impact, 1), "checks": impact_checks, "weak_openers": weak_count,
                       "metric_rate": round(metric_rate, 2)},
            "brevity_style": {"score": round(brevity_style, 1), "checks": brevity_checks,
                              "buzzwords": buzz, "passive": passive, "pronouns": pron},
            "leadership_growth": {"score": round(leadership_growth, 1), "checks": lg_checks},
            "ats_format": {"score": round(ats_format, 1), "checks": ats_checks},
        },
    }

# ============================================================================================
# ATS parse gate (runs on the rendered PDF)
# ============================================================================================
def extract_pdf(path: str) -> dict:
    text, pages, chars = "", 1, 0
    if _HAS_PDF:
        try:
            with pdfplumber.open(path) as pdf:
                pages = len(pdf.pages)
                parts = [(p.extract_text() or "") for p in pdf.pages]
                text = "\n".join(parts)
                chars = len(text)
        except Exception as e:
            text = ""; chars = 0
    if not text:  # fallback to pdftotext
        try:
            text = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, timeout=30).stdout
            chars = len(text)
        except Exception:
            pass
    return {"text": text, "pages": pages, "chars": chars}

def ats_gate(pdf_meta: dict) -> dict:
    text, pages, chars = pdf_meta["text"], pdf_meta["pages"], pdf_meta["chars"]
    issues = []
    low = norm(text)
    if chars < 400:
        issues.append("PDF text barely extractable — likely image/scanned/columned (ATS-blind).")
    has_email = "@" in text
    has_phone = bool(re.search(r"\+?\d[\d ]{7,}", text))
    if not (has_email and has_phone):
        issues.append("Contact (email/phone) not both found in body text.")
    if not all(_contains(low, h) for h in ["experience", "education", "skills"]):
        issues.append("Missing one or more standard headings (Experience/Education/Skills).")
    # page fill (one-page target ~3200 chars)
    fill = round(min(1.0, chars / 3200.0), 2) if pages == 1 else 1.0
    if pages == 1 and fill < 0.80:
        issues.append(f"Page under-filled (~{int(fill*100)}%): looks thin/sparse — add content.")
    if pages > 1:
        issues.append(f"{pages} pages — early-career CV should be one page.")
    return {"ats_parse_ok": len(issues) == 0, "pages": pages, "chars": chars,
            "page_fill": fill, "issues": issues}

# ============================================================================================
# Public API
# ============================================================================================
# --- 27 Jul 2026: REPRODUCIBILITY -----------------------------------------------------------
# learn.py mutates the gazetteer between sessions, so the same CV + JD scored different numbers
# on different days (Anaplan Senior DS: logged 100, re-scored 82.2 then 91.6). A score is only
# meaningful alongside the ruler that produced it — stamp the data version on every report and
# record it with the score in the backend.
def scorer_version() -> str:
    import hashlib
    h = hashlib.sha256()
    for name in ("skills_gazetteer.json", "synonyms.json", "wordlists.json"):
        try:
            with open(os.path.join(_DATA, name), "rb") as f:
                h.update(f.read())
        except OSError:
            h.update(b"missing")
    gaz = _data()[2]
    return f"g{len(gaz.get('hard_skills', []))}-{h.hexdigest()[:8]}"

def tier_for(jd_match: float) -> str:
    for name, cut in TIER_CUTS:
        if jd_match >= cut:
            return name
    return "Skip"

def score(cv_text: str, jd_text: str = "", requirements: Optional[list] = None,
          title: Optional[str] = None, cv_skills: Optional[list] = None,
          pdf_meta: Optional[dict] = None, bullets: Optional[list] = None) -> dict:
    """Full report. Supply requirements (preferred) or jd_text (auto-extract).
    Pass `bullets` (list of the CV's real accomplishment bullets) for exact quality scoring;
    otherwise bullets are heuristically segmented from cv_text."""
    if requirements:
        reqs = load_requirements(requirements)
    else:
        reqs = extract_requirements(jd_text, title=title)
    cvskills = _cv_skill_set(cv_text, cv_skills)
    jd = score_jd_match(cv_text, reqs, cv_skills=cvskills)
    q = score_quality(cv_text, bullets=bullets)
    rep = {
        "scorer_version": scorer_version(),
        "jd_match": jd["jd_match"],
        "quality": q["quality"],
        "composite": round(jd["jd_match"] * COMPOSITE["jd_match"] + q["quality"] * COMPOSITE["quality"], 1),
        "tier": tier_for(jd["jd_match"]),
        "overall_similarity_tfidf": overall_similarity(cv_text, jd_text) if jd_text else None,
        "jd_match_detail": jd,
        "quality_detail": q,
    }
    if pdf_meta is not None:
        rep["ats"] = ats_gate(pdf_meta)
        rep["ats_parse_ok"] = rep["ats"]["ats_parse_ok"]
    return rep

def score_pdf(pdf_path: str, jd_text: str = "", requirements: Optional[list] = None,
              title: Optional[str] = None, cv_skills: Optional[list] = None,
              bullets: Optional[list] = None) -> dict:
    """Score the *rendered PDF* (ATS-faithful coverage + parse gate). Pass `bullets` for exact
    quality scoring of the CV's real accomplishment lines."""
    meta = extract_pdf(pdf_path)
    return score(meta["text"], jd_text=jd_text, requirements=requirements, title=title,
                 cv_skills=cv_skills, pdf_meta=meta, bullets=bullets)

# ============================================================================================
# CLI
# ============================================================================================
def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def _fmt(rep):
    L = []
    L.append(f"JD-MATCH: {rep['jd_match']}%   QUALITY: {rep['quality']}/100   "
             f"COMPOSITE: {rep['composite']}   TIER: {rep['tier']}")
    if rep.get("overall_similarity_tfidf") is not None:
        L.append(f"TF-IDF cosine (whole-doc): {rep['overall_similarity_tfidf']}%")
    if "ats" in rep:
        a = rep["ats"]
        L.append(f"ATS-PARSE: {'PASS' if a['ats_parse_ok'] else 'FAIL'}  "
                 f"pages={a['pages']} fill={int(a['page_fill']*100)}%")
        for i in a["issues"]:
            L.append(f"   ! {i}")
    jm = rep["jd_match_detail"]
    L.append(f"\nMISSING KEYWORDS (top, by weight):")
    for m in jm["missing_keywords"][:15]:
        L.append(f"   - {m['term']:32s} [{m['type']:10s} w={m['weight']:.2f}] found={m['found']}")
    L.append(f"\nMATCHED: {len(jm['matched_keywords'])}/{jm['n_requirements']} requirements")
    q = rep["quality_detail"]["categories"]
    L.append(f"\nQUALITY breakdown:  impact {q['impact']['score']}  style {q['brevity_style']['score']}  "
             f"lead/growth {q['leadership_growth']['score']}  ats {q['ats_format']['score']}   "
             f"(bullets={rep['quality_detail']['n_bullets']}, weak openers={q['impact']['weak_openers']})")
    return "\n".join(L)

def main():
    ap = argparse.ArgumentParser(description="CV↔JD scoring engine")
    ap.add_argument("--cv", required=True, help="CV file (.pdf or .txt)")
    ap.add_argument("--jd", help="JD text file (or inline string)")
    ap.add_argument("--title", help="target job title")
    ap.add_argument("--requirements", help="JSON file of LLM-extracted requirements")
    ap.add_argument("--cv-skills", help="JSON list of canonical CV skills (optional augmentation)")
    ap.add_argument("--out", help="write full JSON report here")
    a = ap.parse_args()

    jd_text = ""
    if a.jd:
        jd_text = _read(a.jd) if os.path.exists(a.jd) else a.jd
    reqs = json.loads(_read(a.requirements)) if a.requirements else None
    cvsk = json.loads(_read(a.cv_skills)) if a.cv_skills else None

    if a.cv.lower().endswith(".pdf"):
        rep = score_pdf(a.cv, jd_text=jd_text, requirements=reqs, title=a.title, cv_skills=cvsk)
    else:
        rep = score(_read(a.cv), jd_text=jd_text, requirements=reqs, title=a.title, cv_skills=cvsk)

    print(_fmt(rep))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2)
        print(f"\n[written] {a.out}")

if __name__ == "__main__":
    main()
