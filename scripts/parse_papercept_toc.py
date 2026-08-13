#!/usr/bin/env python3
"""
Parse a papercept conference TOC PDF (e.g. IROS/ICRA "IROS_2025_TOC.pdf") into
structured papers JSON.

Usage:
    python parse_papercept_toc.py --toc IROS_2025_TOC.pdf \
        [--author-index IROS_2025_Author_Index.pdf] [--out papers.json]

Output JSON: list of paper objects:
    { "code": "TuAT1.1", "session_code": "TuAT1",
      "session_title": "SLAM 1 (Regular Session)", "title": "...",
      "pages": "1-8", "authors": ["Last, First", ...] }

If --author-index is provided, author lists are completed/validated against the
official Author Index PDF (name -> paper code). Without it, authors are extracted
from the TOC block via a "Last, First" heuristic.

Requires: pip install pymupdf
"""
import argparse
import json
import re
import sys

DAY = r"(Tu|We|Th|Fr|Sa|Su|Mo)"
SESS_RE = re.compile(r"^%s(A|B|C|D)T\d+$" % DAY)
PAP_RE = re.compile(r"^%s(A|B|C|D)T\d+\.\d+$" % DAY)
TIME_RE = re.compile(r"^\d{1,2}:\d{2}-\d{1,2}:\d{2}$")


def extract_text(pdf_path):
    import pymupdf  # falls back to legacy fitz
    doc = pymupdf.open(pdf_path)
    return "\n".join(page.get_text() for page in doc)


# --------------------------------------------------------------------------
# Author Index parsing: build name -> set(codes)
# --------------------------------------------------------------------------
def parse_author_index(text):
    name_to_codes = {}
    cur_name = ""
    cur_codes = []

    def is_paper(s):
        return bool(PAP_RE.match(s.replace("$", "A")))

    def is_session(s):
        return bool(SESS_RE.match(s.replace("$", "A")))

    def is_id(s):
        return bool(re.fullmatch(r"\d+", s))

    def is_marker(s):
        return s in ("A", "C", "CC")

    def flush():
        nonlocal cur_name, cur_codes
        if cur_name:
            name_to_codes.setdefault(cur_name, set()).update(cur_codes)
        cur_name = ""
        cur_codes = []

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if re.search(r"\.{3,}", line):
            parts = re.split(r"\.{3,}", line)
            frag = parts[0].strip()
            toks = " ".join(p.strip() for p in parts[1:] if p.strip()).split()
            if frag:
                if "," in frag:
                    flush()
                    cur_name = frag
                else:
                    cur_name = (cur_name + " " + frag).strip() if cur_name else frag
            for tk in toks:
                if is_paper(tk):
                    cur_codes.append(tk.replace("$", "A"))
        else:
            toks = line.split()
            if toks and all(is_paper(t) or is_session(t) or is_id(t) or is_marker(t) for t in toks):
                for tk in toks:
                    if is_paper(tk):
                        cur_codes.append(tk.replace("$", "A"))
            else:
                if "," in line:
                    flush()
                    cur_name = line
                else:
                    cur_name = (cur_name + " " + line).strip() if cur_name else line
    flush()
    return name_to_codes


# --------------------------------------------------------------------------
# TOC parsing
# --------------------------------------------------------------------------
def parse_toc(text, name_to_codes):
    lines = [l.strip() for l in text.split("\n")]
    papers = []
    cur_session = None
    i, n = 0, len(lines)

    def parse_session_header(i):
        # returns (session_dict, next_index)
        j = i + 1
        hdr = []
        while j < n and not SESS_RE.match(lines[j]) and not PAP_RE.match(lines[j]):
            hdr.append(lines[j])
            j += 1
        hdr = [h for h in hdr if h]
        room = title = None
        if hdr:
            if re.fullmatch(r"\d+[A-Za-z]?", hdr[0]):
                room = hdr[0]
                if len(hdr) > 1:
                    title = hdr[1]
            else:
                title = hdr[0]
        return {"code": lines[i], "title": title, "room": room}, j

    def parse_paper_block(code, block):
        k = 0
        title_end = None
        while k < len(block):
            ln = block[k]
            if re.search(r"pp\.\s*\d", ln):
                title_end = k
                break
            if re.fullmatch(r"\d+(?:-\d+)?\.?\s*(?:Attachment)?\s*", ln):
                p = k - 1
                while p >= 0 and not block[p]:
                    p -= 1
                if p >= 0 and re.search(r"pp\.\s*$", block[p]):
                    title_end = k
                    break
            k += 1
        if title_end is None:
            title = " ".join(block).strip()
            pages = None
            author_region = []
        else:
            k = title_end
            joined = " ".join(block[:k + 1]).strip()
            title = re.sub(r"\s*Attachment\s*$", "", joined).strip()
            title = re.sub(r",?\s*pp\.\s*\d+(?:-\d+)?\.?\s*$", "", title).strip()
            m = re.search(r"pp\.\s*(\d+(?:-\d+)?)", joined)
            pages = m.group(1) if m else None
            author_region = [l for l in block[k + 1:] if l]
            if author_region and author_region[0] == "Attachment":
                author_region = author_region[1:]
        # authors via whitelist (exact name + code match); fallback heuristic
        authors = []
        if name_to_codes:
            for al in author_region:
                if al in name_to_codes and code in name_to_codes[al]:
                    authors.append(al)
        if not authors:
            for al in author_region:
                if re.match(r"^[^,]+,\s*[^,]+$", al) and not re.search(
                        r"(university|institute|laboratory|lab|college|department|research|center|inc|llc|corp|gmbh|ag|ltd)", al, re.I):
                    authors.append(al)
        return title, pages, authors

    while i < n:
        l = lines[i]
        if SESS_RE.match(l):
            cur_session, i = parse_session_header(i)
            continue
        if PAP_RE.match(l):
            j = i + 1
            block = []
            while j < n and not TIME_RE.match(lines[j]) and not PAP_RE.match(lines[j]) and not SESS_RE.match(lines[j]):
                block.append(lines[j])
                j += 1
            title, pages, authors = parse_paper_block(l, block)
            papers.append({
                "code": l,
                "session_code": cur_session["code"] if cur_session else None,
                "session_title": cur_session["title"] if cur_session else None,
                "title": title,
                "pages": pages,
                "authors": authors,
            })
            i = j
            continue
        i += 1
    return papers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--toc", required=True, help="path to TOC PDF")
    ap.add_argument("--author-index", help="path to Author Index PDF (optional)")
    ap.add_argument("--out", default="papers.json")
    args = ap.parse_args()

    toc_text = extract_text(args.toc)
    name_to_codes = {}
    if args.author_index:
        ai_text = extract_text(args.author_index)
        name_to_codes = parse_author_index(ai_text)
        print("author-index names:", len(name_to_codes), file=sys.stderr)

    papers = parse_toc(toc_text, name_to_codes)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(papers, f, ensure_ascii=False)
    print("papers:", len(papers), "->", args.out, file=sys.stderr)


if __name__ == "__main__":
    main()
