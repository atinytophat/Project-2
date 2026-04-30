#!/usr/bin/env python3
"""Extract text from one PDF into a plain text file.

Usage:
    python pdf_to_text.py input.pdf
    python pdf_to_text.py input.pdf -o output.txt
    python pdf_to_text.py input.pdf --no-clean
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def load_pdf_reader():
    """Return a PdfReader class from an available dependency."""
    try:
        from pypdf import PdfReader  # type: ignore

        return PdfReader
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader  # type: ignore

        return PdfReader
    except ImportError:
        pass

    raise SystemExit(
        "Missing PDF dependency. Install one of these first:\n"
        "  python -m pip install pypdf\n"
        "  python -m pip install PyPDF2"
    )


def clean_text(text: str) -> str:
    """Normalize whitespace without destroying paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(pdf_path: Path, clean: bool) -> str:
    """Extract text from each page and join it with page markers."""
    PdfReader = load_pdf_reader()
    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []

    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if clean:
            page_text = clean_text(page_text)
        chunks.append(f"===== Page {page_index} =====\n{page_text}")

    return "\n\n".join(chunks).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a PDF into a plain text file."
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the input PDF file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to the output text file. Defaults to the PDF name with .txt.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Disable whitespace cleanup.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_pdf = args.input_pdf.expanduser().resolve()

    if not input_pdf.exists():
        print(f"Input file not found: {input_pdf}", file=sys.stderr)
        return 1

    if input_pdf.suffix.lower() != ".pdf":
        print(f"Input file must be a PDF: {input_pdf}", file=sys.stderr)
        return 1

    output_txt = (
        args.output.expanduser().resolve()
        if args.output
        else input_pdf.with_suffix(".txt")
    )

    text = extract_pdf_text(input_pdf, clean=not args.no_clean)
    output_txt.write_text(text, encoding="utf-8")
    print(f"Wrote text to: {output_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
