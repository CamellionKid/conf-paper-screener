#!/usr/bin/env python3
"""
Parse a DBLP conference page (e.g. https://dblp.org/db/conf/iros/iros2025.html,
saved locally) into papers JSON.

Usage:
    python parse_dblp.py --html iros2025.html --out dblp_papers.json

Output JSON: list of paper objects (same schema as parse_papercept_toc.py, but
no session/code):
    { "code": null, "session_title": null, "title": "...",
      "pages": "1-8", "authors": ["First Last", ...] }

Note: DBLP has no session info and may be incomplete for a given conference
(it is a bibliographic aggregator). Front-matter entries (roman-numeral pages)
are dropped.
"""
import argparse
import json
import re
import html as htm

ENTRY_START = '<li class="entry inproceedings"'
TITLE_RE = re.compile(r'<span class="title"[^>]*>(.*?)</span>', re.S)
AUTH_RE = re.compile(r'<span itemprop="name" title="([^"]*)"[^>]*>.*?</span>', re.S)
PAGE_RE = re.compile(r'<span itemprop="pagination">([^<]*)</span>')


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    return htm.unescape(s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True, help="path to saved DBLP conference html")
    ap.add_argument("--out", default="dblp_papers.json")
    args = ap.parse_args()

    h = open(args.html, encoding="utf-8").read()
    poses = [m.start() for m in re.finditer(re.escape(ENTRY_START), h)]

    papers = []
    for idx, pos in enumerate(poses):
        end = poses[idx + 1] if idx + 1 < len(poses) else len(h)
        e = h[pos:end]
        km = re.search(r'id="conf/[^/]+/([A-Za-z0-9]+)"', e)
        tm = TITLE_RE.search(e)
        title = clean(tm.group(1)) if tm else None
        if title and title.endswith("."):
            title = title[:-1]
        authors = AUTH_RE.findall(e)
        pm = PAGE_RE.search(e)
        pages = pm.group(1).strip() if pm else None
        # drop front matter (roman-numeral pages)
        if pages and pages[0].isalpha():
            continue
        papers.append({
            "code": None,
            "session_title": None,
            "title": title,
            "pages": pages,
            "authors": authors,
        })

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False)
    print("papers:", len(papers), "->", args.out)


if __name__ == "__main__":
    main()
