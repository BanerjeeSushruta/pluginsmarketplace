#!/usr/bin/env python3
"""Validate that the PDF contains working navigable TOC links.

This checks for real internal GoTo links on the TOC page, not just any link
annotation. The validator fails if TOC entries do not resolve to valid pages.
"""
import argparse
import json
from pathlib import Path
import fitz

parser = argparse.ArgumentParser(description="Validate navigable PDF table of contents links.")
parser.add_argument("pdf")
parser.add_argument("--toc-page", type=int, default=2, help="1-based TOC page number. Default: 2")
parser.add_argument("--summary", default=None)
args = parser.parse_args()

pdf_path = Path(args.pdf)
errors = []
warnings = []
valid_links = []
link_count = 0
goto_count = 0
if not pdf_path.exists() or pdf_path.stat().st_size == 0:
    errors.append("PDF file is missing or empty.")
else:
    doc = fitz.open(pdf_path)
    toc_index = args.toc_page - 1
    if doc.page_count <= toc_index:
        errors.append(f"TOC page {args.toc_page} is outside page count {doc.page_count}.")
    else:
        page = doc[toc_index]
        links = page.get_links()
        link_count = len(links)
        for link in links:
            if link.get("kind") == fitz.LINK_GOTO:
                goto_count += 1
                target = link.get("page", -1)
                if isinstance(target, int) and 0 <= target < doc.page_count and target != toc_index:
                    valid_links.append({
                        "from_page": args.toc_page,
                        "target_page": target + 1,
                        "rect": [round(v, 2) for v in link.get("from")]
                    })
                else:
                    errors.append(f"Invalid TOC link target page: {target}.")
        if goto_count == 0:
            errors.append("No internal GoTo links found on TOC page.")
        elif not valid_links:
            errors.append("No valid internal TOC links resolve to document pages.")

result = {
    "status": "success" if not errors else "failed",
    "pdf_file": str(pdf_path),
    "toc_page": args.toc_page,
    "link_annotation_count": link_count,
    "goto_link_count": goto_count,
    "valid_toc_link_count": len(valid_links),
    "toc_clickable": len(valid_links) > 0 and not errors,
    "valid_links": valid_links,
    "warnings": warnings,
    "errors": errors,
}
if args.summary:
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)
    Path(args.summary).write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
