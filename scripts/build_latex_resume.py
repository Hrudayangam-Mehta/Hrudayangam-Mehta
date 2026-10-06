"""Compile the hand-edited LaTeX resume; never regenerate its source.

Usage: python scripts/build_latex_resume.py
Optional: --engine /path/to/pdflatex
Requires an existing pdfLaTeX installation and pypdf (local .tools/python works).
Uses PyMuPDF for plain-text spacing when available; otherwise uses pypdf.
The build disables shell escape and MiKTeX's automatic package installer.
Outputs: resumes/Hrudayangam-Mehta-Resume.pdf and its extracted .txt companion.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "resumes" / "Hrudayangam-Mehta-Resume.tex"
sys.path.insert(0, str(ROOT / ".tools" / "python"))

try:
    from pypdf import PdfReader
except ImportError as exc:
    raise SystemExit("pypdf is required to verify searchable PDF text.") from exc

try:
    import pymupdf
except ImportError:
    pymupdf = None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="pdflatex", help="pdfLaTeX executable or path")
    args = parser.parse_args()
    engine = shutil.which(args.engine)
    if not engine:
        raise SystemExit("pdfLaTeX was not found. Add your existing TeX installation to PATH or use --engine.")
    if not SOURCE.is_file():
        raise SystemExit(f"Missing editable source: {SOURCE}")

    work_root = ROOT / ".tools" / "latex"
    work_root.mkdir(parents=True, exist_ok=True)
    log_path = SOURCE.with_suffix(".log")

    # A staging directory protects the existing PDF if compilation fails.
    with tempfile.TemporaryDirectory(prefix="resume-", dir=work_root) as temporary:
        build_dir = Path(temporary)
        command = [engine, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error"]
        if "miktex" in engine.lower():
            command.append("--disable-installer")
        command.extend([f"-output-directory={build_dir}", str(SOURCE)])

        for _ in range(2):
            try:
                result = subprocess.run(
                    command, cwd=SOURCE.parent, capture_output=True,
                    text=True, errors="replace", timeout=120, check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise SystemExit("pdfLaTeX exceeded the 120-second limit; existing PDF was preserved.") from exc
            build_log = build_dir / SOURCE.with_suffix(".log").name
            if build_log.is_file():
                shutil.copyfile(build_log, log_path)
            if result.returncode:
                print(result.stdout[-7000:], file=sys.stderr)
                print(result.stderr[-2000:], file=sys.stderr)
                raise SystemExit(f"pdfLaTeX failed; existing PDF was preserved. Log, when available: {log_path}")

        log = log_path.read_text(encoding="utf-8", errors="replace")
        if "Overfull \\hbox" in log or "Overfull \\vbox" in log:
            raise SystemExit(f"LaTeX reported overflowing content. Fix the layout before publishing: {log_path}")

        built_pdf = build_dir / SOURCE.with_suffix(".pdf").name
        reader = PdfReader(built_pdf)
        if pymupdf is not None:
            with pymupdf.open(built_pdf) as document:
                pages = [page.get_text() for page in document]
        else:
            pages = [page.extract_text() or "" for page in reader.pages]
        if not pages or any(len(page.strip()) < 50 for page in pages):
            raise SystemExit("The PDF has a blank page or insufficient searchable text; existing PDF was preserved.")
        text = "\n\n".join(pages).strip() + "\n"
        if "\ufffd" in text:
            raise SystemExit("The PDF contains unreadable replacement characters; check fonts and encoding.")
        urls = []
        for page in reader.pages:
            for reference in page.get("/Annots", []):
                action = reference.get_object().get("/A", {})
                if action.get("/URI"):
                    urls.append(str(action["/URI"]))

        output = SOURCE.with_suffix(".pdf")
        shutil.copyfile(built_pdf, output)
        SOURCE.with_suffix(".txt").write_text(text, encoding="utf-8")
        print(json.dumps({
            "pdf": str(output.relative_to(ROOT)),
            "source": str(SOURCE.relative_to(ROOT)),
            "pages": len(reader.pages),
            "searchable_characters": len(text),
            "hyperlinks": len(urls),
            "overflow": False,
        }, indent=2))
        if len(reader.pages) != 1:
            print("Note: the edited resume is no longer one page.", file=sys.stderr)


if __name__ == "__main__":
    main()
