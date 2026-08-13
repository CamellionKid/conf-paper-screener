# Feishu Output

Use the `lark-sheets` skill (and `lark-shared` for auth) to write results to a Feishu spreadsheet. This file only covers the conference-specific schema and the gotchas we hit.

## Sheet layout

| Sheet | Columns | Rows |
|---|---|---|
| Sheet1 `感知定位规控论文` | 类别 / 论文标题 / 全部作者 / Session代码 / 页码 / Session主题 / 分类依据 | one per classified paper |
| Sheet2 `百家姓作者论文` | 论文标题 / 命中的百家姓作者 / Session代码 | papers with >=1 百家姓 author |
| Sheet3 `百家姓作者明细` | 论文标题 / 百家姓作者 / Session代码 | one per 百家姓 author, title+code merged across a paper's rows |

Sheet3 merge: for a paper with N 百家姓 authors occupying rows R..R+N-1 (data starts row 2), merge `A{R}:A{R+N-1}` and `C{R}:C{R+N-1}`.

## Writing (typed) via `+workbook-create` / `+table-put`

- Build a `{"sheets":[{"name":..,"columns":..,"data":..}, ...]}` payload. All values are text; no numeric types needed.
- Large payload → write to a temp file, pass via stdin (`--sheets -`) or `@file`.
- `+workbook-create` for a new workbook; `+table-put` to write into an existing one (a named sheet that doesn't exist is auto-created).

## Gotchas (learned the hard way)

1. **PowerShell stdin encoding**: `$OutputEncoding = [System.Text.Encoding]::UTF8` and read files with `Get-Content -Raw -Encoding UTF8`, or Chinese gets mangled.
2. **`@file` only accepts cwd-relative paths** — set `workdir` to the temp dir and use `--sheets '@payload.json'` (quote the `@arg` so PowerShell doesn't treat it as splatting).
3. **`--styles` / merges arg is too long for the command line** (Windows ~32k limit) — pass it via `@file` too, not inline.
4. **`+batch-update --operations` caps at 100 entries**; merges require `--yes` (high-risk write). Chunk into batches of <=100.
5. **Re-running a merge over already-merged cells fails** ("overlaps existing merged cells") — `+cells-unmerge` the full A/C columns first, then re-merge.
6. **Write returns `ok` ≠ data correct** — read back (`+workbook-info` for row counts/merged count, `+csv-get` for content). Terminal may show `�?` for multi-byte chars; confirm via CSV export instead.
7. Updating one column in-place: `+cells-set --range B2:B4615 --cells '@cells.json'` (cells = `[[{"value":..}], ...]`); leaves merges in other columns intact.

## Local files

`classify_papers.py` also writes `sheet1/2/3.csv` (UTF-8 with BOM) and `.json` to `--out-dir`. Hand these to the user as the local artifact alongside the Feishu link.
