#!/usr/bin/env python3
"""
Classify parsed conference papers into user-defined domains, identify Chinese
surname (百家姓 pinyin) authors, optionally attach affiliations, and emit
sheet-ready CSVs + JSON.

Usage:
    python classify_papers.py --papers papers.json \
        [--domains domains.json] [--aff affiliations.json] \
        [--surnames surnames.json] [--out-dir .] [--with-surnames 1]

--papers    : output of parse_papercept_toc.py or parse_dblp.py
              schema: {code, session_title, title, pages, authors[]}
--domains   : domain definition (default: assets/domains.default.json)
--aff       : output of parse_papercept_program.py (optional; {code:{authors:[[name,aff]]}})
--surnames  : 百家姓 pinyin set (default: assets/surnames.json)
--out-dir   : where to write sheet1/sheet2/sheet3 .json + .csv

Emits:
    classified.json   full list with {cat, basis}
    sheet1.csv/.json  one row per classified paper
    sheet2.csv/.json  papers with >=1 百家姓 author
    sheet3.csv/.json  one row per 百家姓 author (title + "Name — Affiliation")
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def match_rule(rule, text):
    t = text.lower()
    if rule.get("exclude") and any(e in t for e in rule["exclude"]):
        return False
    if rule.get("include") and not any(i in t for i in rule["include"]):
        return False
    return any(re.search(p, t) for p in rule["patterns"])


def classify(paper, domains):
    st = paper.get("session_title") or ""
    # session rules
    for rule in domains.get("session_rules", []):
        if st and match_rule(rule, st):
            return rule["cat"], "session"
    # title rules
    for rule in domains.get("title_rules", []):
        if match_rule(rule, paper["title"] or ""):
            return rule["cat"], "title"
    return None, None


def surname(author):
    if "," in author:
        return author.split(",")[0].strip()
    toks = author.split()
    return toks[-1] if toks else author


def normalize_surname(s):
    return s.lower().replace("-", "").replace(" ", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", required=True)
    ap.add_argument("--domains", default=os.path.join(HERE, "..", "assets", "domains.default.json"))
    ap.add_argument("--aff")
    ap.add_argument("--surnames", default=os.path.join(HERE, "..", "assets", "surnames.json"))
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--with-surnames", default="1", help="1 (default) build sheet2/sheet3; 0 skip")
    args = ap.parse_args()

    papers = load_json(args.papers)
    domains = load_json(args.domains)
    sn = load_json(args.surnames)
    single = set(sn["single"])
    compound = set(sn["compound"])
    with_surnames = args.with_surnames != "0"

    aff_map = {}
    if args.aff:
        affs = load_json(args.aff)
        for code, v in affs.items():
            for name, a in v.get("authors", []):
                aff_map[(code, name)] = a

    fusion = domains.get("fusion_split", {})
    fusion_loc = fusion.get("loc_patterns", [])
    fusion_default = fusion.get("default", None)

    classified = []
    for p in papers:
        cat, basis = classify(p, domains)
        if cat == "FUSION":
            t = (p["title"] or "").lower()
            if any(k in t for k in fusion_loc):
                cat, basis = "定位", "session"
            else:
                cat, basis = fusion_default, "session"
        p["cat"] = cat
        p["basis"] = basis if cat else None
        classified.append(p)

    cats = {}
    for p in classified:
        if p["cat"]:
            cats[p["cat"]] = cats.get(p["cat"], 0) + 1

    # sheet1
    sheet1 = []
    for p in classified:
        if not p["cat"]:
            continue
        sheet1.append([p["cat"], p["title"], " / ".join(p["authors"]),
                       p["code"] or "", p["pages"] or "", p["session_title"] or "",
                       p["basis"]])

    sheet2, sheet3 = [], []
    if with_surnames:
        for p in classified:
            if not p["cat"]:
                continue
            hits = []
            for a in p["authors"]:
                s = normalize_surname(surname(a))
                if s in compound or s in single:
                    hits.append(a)
            if not hits:
                continue
            sheet2.append([p["title"], " / ".join(hits), p["code"] or ""])
            for a in hits:
                aff = aff_map.get((p["code"], a)) if p["code"] else None
                sheet3.append([p["title"], ("%s — %s" % (a, aff)) if aff else a,
                               p["code"] or ""])

    os.makedirs(args.out_dir, exist_ok=True)

    def write_json(name, data):
        json.dump(data, open(os.path.join(args.out_dir, name + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False)

    def write_csv(name, header, rows):
        with open(os.path.join(args.out_dir, name + ".csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    write_json("classified", classified)
    write_json("sheet1", sheet1)
    write_csv("sheet1", ["类别", "论文标题", "全部作者", "Session代码", "页码", "Session主题", "分类依据"], sheet1)
    if with_surnames:
        write_json("sheet2", sheet2)
        write_csv("sheet2", ["论文标题", "命中的百家姓作者", "Session代码"], sheet2)
        write_json("sheet3", sheet3)
        write_csv("sheet3", ["论文标题", "百家姓作者", "Session代码"], sheet3)

    print("classified:", cats, "total:", sum(cats.values()), file=sys.stderr)
    print("uncategorized:", sum(1 for p in classified if not p["cat"]), file=sys.stderr)
    print("sheet1 rows:", len(sheet1), "| sheet2 rows:", len(sheet2), "| sheet3 rows:", len(sheet3), file=sys.stderr)


if __name__ == "__main__":
    main()
