---
name: conf-paper-screener
description: >-
  Screen conference papers (IROS/ICRA or any papercept/DBLP conference) by domain —
  e.g. 感知 (perception), 定位 (localization), 规控 (planning & control) — extract authors,
  affiliations and Chinese-surname (百家姓 pinyin) authors, and write results to a Feishu
  spreadsheet plus local CSV. Use when the user wants to filter a conference's papers by
  topic, "筛选会议论文", "找出 SLAM/感知/规划 的论文", or build a candidate/author list from
  a conference program. Always ask the user which source to use (papercept TOC PDF they
  provide, papercept program HTML, or DBLP) and require an explicit domain definition
  before classifying.
---

# Conference Paper Screener

Pipeline: **ASK** (conference, source, domains) → **PARSE** (TOC/DBLP → papers.json) → **AFFILIATIONS** (optional) → **CLASSIFY** (domains + 百家姓) → **OUTPUT** (Feishu sheets + local CSV).

## Prerequisites

- Python 3 with `pymupdf` (`pip install pymupdf`) for PDF parsing.
- For Feishu output: `lark-cli` configured (see `lark-sheets` / `lark-shared` skills).

## Workflow

### 1. Ask the user (do not skip)

1. **Conference + year** — direct input, e.g. "IROS 2025".
2. **Data source** — papercept TOC PDF (user provides path) / papercept program HTML (fetch by day) / DBLP (fetch). See `references/sources.md` for URL construction and tradeoffs.
3. **Domains to filter** — require a clear definition per domain (what counts / what doesn't). Offer the built-in 感知/定位/规控 default (`assets/domains.default.json`); echo the derived keyword rules and borderline-session decisions back for confirmation. See `references/domains.md`. "定位" must be disambiguated (ego/robot pose vs object-level localization).

### 2. Parse

- papercept TOC PDF → `python scripts/parse_papercept_toc.py --toc <toc.pdf> [--author-index <ai.pdf>] --out papers.json`
- DBLP → save the page HTML, then `python scripts/parse_dblp.py --html <page.html> --out papers.json`

### 3. Affiliations (papercept only)

Fetch the per-day `ContentListWeb_N.html` pages, then:
`python scripts/parse_papercept_program.py --html page_1.html --html page_2.html ... --out affiliations.json`

### 4. Classify

`python scripts/classify_papers.py --papers papers.json [--domains domains.json] [--aff affiliations.json] --out-dir out`

Report to the user: per-category counts, uncategorized count, and a sample of borderline hits before writing output. If DBLP was used, state the coverage gap (DBLP may be incomplete — see `sources.md`).

### 5. Output

- **Feishu**: create a spreadsheet and write Sheet1/2/3 per `references/feishu_output.md` (use the `lark-sheets` skill). Read back to verify.
- **Local**: `sheet1/2/3.csv` + `.json` in `--out-dir` (UTF-8 with BOM).

## Scripts

| Script | Purpose |
|---|---|
| `scripts/parse_papercept_toc.py` | TOC PDF → papers.json (code/session/title/pages/authors; optional Author Index cross-validation) |
| `scripts/parse_dblp.py` | DBLP HTML → papers.json (title/authors/pages; no sessions) |
| `scripts/parse_papercept_program.py` | program day HTML → code→(author→affiliation) |
| `scripts/classify_papers.py` | classify by domains + 百家姓 + affiliations → sheet1/2/3 CSV+JSON |

## References

| File | Content |
|---|---|
| `references/sources.md` | the 3 sources, URL patterns, completeness tradeoffs |
| `references/domains.md` | domain-definition schema, default 感知/定位/规控, borderline-session table |
| `references/feishu_output.md` | sheet schema + lark-sheets gotchas (encoding, @file, merge caps) |

## Key principles

- **Ask source at runtime** — never assume papercept vs DBLP vs user PDF.
- **Domain definition is mandatory and explicit** — especially 定位.
- **Cross-validate authors** with the Author Index when parsing a papercept TOC.
- **Report completeness** (DBLP missing %) and **verify writes** by read-back.
- Chinese-surname (百家姓) matching uses `assets/surnames.json`; names are matched by surname pinyin (last-name-before-comma, or last token for "First Last" DBLP format).
