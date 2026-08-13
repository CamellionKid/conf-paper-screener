#!/usr/bin/env python3
"""
Parse papercept per-day program HTML pages (e.g.
"IROS25_ContentListWeb_1.html") to extract (paper code -> author -> affiliation).

Usage:
    python parse_papercept_program.py --html IROS25_ContentListWeb_1.html \
        [--html IROS25_ContentListWeb_2.html ...] --out affiliations.json

Output JSON: { "<paper code>": { "title": "...",
                                 "authors": [["Last, First", "Affiliation"], ...] } }

This is the cleaner affiliation source (full, untruncated) vs the TOC PDF, which
truncates long affiliations.
"""
import argparse
import json
import re
import html as htm

CODE_RE = re.compile(r"Paper\s+((?:Tu|We|Th|Fr|Sa|Su|Mo)(?:A|B|C|D)T\d+\.\d+)")
TITLE_RE = re.compile(r'class="pTtl">&nbsp;<a[^>]*>(.*?)</a></span>')
AUTH_RE = re.compile(r'AuthorIndex\w*\.html#\d+"[^>]*>(.*?)</a>\s*</td>\s*<td class="r">(.*?)</td>', re.S)


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    return htm.unescape(s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", action="append", required=True,
                    help="path to a day page (repeatable)")
    ap.add_argument("--out", default="affiliations.json")
    args = ap.parse_args()

    papers = {}
    for hp in args.html:
        h = open(hp, encoding="utf-8").read()
        cur = None
        for m in re.finditer(r"<tr([^>]*)>(.*?)</tr>", h, re.S):
            attrs, body = m.group(1), m.group(2)
            if "pHdr" in attrs:
                cm = CODE_RE.search(body)
                if cm:
                    cur = cm.group(1)
                    papers.setdefault(cur, {"title": None, "authors": []})
                continue
            if cur is None:
                continue
            tm = TITLE_RE.search(body)
            if tm and papers[cur]["title"] is None:
                papers[cur]["title"] = clean(tm.group(1))
            for am in AUTH_RE.finditer(body):
                papers[cur]["authors"].append([clean(am.group(1)), clean(am.group(2))])

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False)
    print("papers:", len(papers), "->", args.out)


if __name__ == "__main__":
    main()
