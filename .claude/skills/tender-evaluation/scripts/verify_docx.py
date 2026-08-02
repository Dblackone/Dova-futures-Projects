#!/usr/bin/env python3
"""Read a .docx back and print its structure, so you can confirm what landed.

Rendering to PDF and looking at the pages is the better check, but LibreOffice
is frequently missing or broken in sandboxes. This is the fallback: it proves
every heading, paragraph and bullet is present and correctly typed, which is
what usually goes wrong when a document is generated rather than typed.

    python verify_docx.py document.docx
    python verify_docx.py document.docx --expect "A1." --expect "B6."

Bullets are shown with a leading dash so you can see at a glance whether a list
item was built as a real list paragraph or accidentally as body text.

Requires python-docx: pip install python-docx
"""

import argparse
import sys

try:
    from docx import Document
except ImportError:
    sys.exit("python-docx is not installed. Run: pip install python-docx")


def paragraphs(path):
    """Yield (is_bullet, text) for every non-empty paragraph."""
    for para in Document(path).paragraphs:
        text = para.text.strip()
        if not text:
            continue
        pPr = para._p.pPr
        yield (pPr is not None and pPr.numPr is not None), text


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("--expect", action="append", default=[], metavar="TEXT",
                    help="require a paragraph starting with TEXT; repeatable")
    ap.add_argument("--quiet", action="store_true",
                    help="only report the summary and any missing expectations")
    args = ap.parse_args()

    paras = list(paragraphs(args.docx))
    if not paras:
        sys.exit(f"{args.docx}: no text found — the document is empty")

    if not args.quiet:
        for is_bullet, text in paras:
            print(f"  - {text}" if is_bullet else text)
        print()

    bullets = sum(1 for is_bullet, _ in paras if is_bullet)
    print(f"{len(paras)} paragraphs, {bullets} bullets, "
          f"{len(paras) - bullets} body/heading")

    missing = [want for want in args.expect
               if not any(text.startswith(want) for _, text in paras)]
    if missing:
        print("\nMISSING:")
        for want in missing:
            print(f"  {want}")
        sys.exit(1)

    if args.expect:
        print(f"all {len(args.expect)} expected paragraphs present")


if __name__ == "__main__":
    main()
