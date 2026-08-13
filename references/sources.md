# Data Sources & Their Tradeoffs

Three sources for conference paper metadata. Ask the user which to use at runtime.

## 1. papercept TOC PDF (official, most complete)

- **What**: the official program book (e.g. `IROS_2025_TOC.pdf` + `IROS_2025_Author_Index.pdf`).
- **Has**: session code + session title (the official topic grouping) + paper code + title + pages + author list (name + affiliation inline, though long affiliations are truncated).
- **URL pattern** (IROS example): `https://ras.papercept.net/conferences/conferences/IROS25/program/` — TOC / Author Index / Cover PDFs are usually linked from the conference program page. Download the PDFs first, then feed local paths to the scripts.
- **Use for**: the primary source. Session-based classification is the most defensible (it's the conference's own topic assignment) and covers 100% of papers.
- **Caveat**: affiliations truncated in the TOC; use source #2 for full affiliations.

## 2. papercept program HTML (affiliations)

- **What**: per-day program pages `IROS25_ContentListWeb_N.html` (N = 1,2,3 for Tue/Wed/Thu).
- **Has**: paper code + title + author name -> full affiliation (untruncated).
- **URL pattern**: `https://ras.papercept.net/conferences/conferences/IROS25/program/IROS25_ContentListWeb_3.html`. Day count varies (IROS 2025 = 3 days).
- **Use for**: resolving full affiliations. Pair with source #1 (match by paper code).

## 3. DBLP (bibliographic, convenient but incomplete)

- **What**: `https://dblp.org/db/conf/iros/iros2025.html` (conference key `iros`, year `2025`; ICRA is `icra`).
- **Has**: title + authors + pages. **No session/track info.**
- **Caveats** (verified on IROS 2025):
  - Incomplete: ~1983 entries vs 2672 in the official TOC (missing ~26%).
  - No sessions → classification must be title-keyword-only → noisier and lower recall.
- **Use for**: when the user has no TOC PDF, or as a cross-check. Report the coverage gap to the user.

## Choosing (ask the user)

| User says | Use |
|---|---|
| "用 papercept / 官方 TOC / 我给你的 PDF" | source #1 (+ #2 for affiliations) |
| "用 DBLP" | source #3 (title-only classification; no affiliations) |
| "我提供 TOC PDF" | source #1 with their file path |

## URL construction from conference + year

- DBLP: `https://dblp.org/db/conf/<key>/<key><YYYY>.html` (IROS -> `iros`, ICRA -> `icra`, RSS -> `rss`, CoRL -> `corl`).
- papercept: IEEE RAS conferences (IROS/ICRA) use `https://ras.papercept.net/conferences/conferences/<CONF><YY>/program/`. The directory is case-sensitive (`IROS25`, `ICRA25`). Open the program index and download the TOC PDF / day pages.
