#!/usr/bin/env python3
"""
Scan repo for desalination-related content, write docs/DESAL_REPORT.md
"""
import pathlib, re, textwrap, datetime
from PyPDF2 import PdfReader
from rich.console import Console

console = Console()
ROOT   = pathlib.Path(".")
DOCS   = ROOT / "docs"
OUT    = DOCS / "DESAL_REPORT.md"
OUT.parent.mkdir(exist_ok=True)

KEYWORDS = [
    r"\bdesal(inat(e|ion)?)\b",
    r"\bmembrane distillation\b",
    r"\breverse osmosis\b",
    r"\bMD\b",  # careful—over-broad; tweak if noise
    r"\bbrine\b",
]

regex = re.compile("|".join(KEYWORDS), re.I)

def md_heading(level, text):
    return ("#"*level) + " " + text + "\n"

lines = [
    md_heading(1, "📑 Desalination Report (auto-generated)"),
    f"_Updated {datetime.date.today()}_\n",
    "> Shows every repo file that mentions desalination or related terms.\n"
]

def add_entry(fname, excerpt):
    lines.append(md_heading(2, fname))
    lines.append("```text")
    lines.extend(textwrap.wrap(excerpt, width=100))
    lines.append("```\n")

for path in ROOT.rglob("*"):
    if path.is_dir():
        continue
    if path.relative_to(ROOT).parts[:2] == (".git",):
        continue   # skip .git internals

    if path.suffix.lower() in {".md", ".txt"}:
        text = path.read_text(errors="ignore")
        hits = regex.findall(text)
        if hits:
            # grab surrounding context (first hit only)
            m = regex.search(text)
            start = max(m.start()-200, 0)
            end   = min(m.end()+200, len(text))
            excerpt = text[start:end].replace("\n", " ")
            add_entry(str(path), excerpt)

    elif path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(path.open("rb"))
            hit_pages = []
            for i, page in enumerate(reader.pages):
                t = page.extract_text() or ""
                if regex.search(t):
                    snippet = regex.sub(lambda m: f">>>{m.group(0)}<<<", t[:500])
                    hit_pages.append(f"Page {i+1}: {snippet[:200]}…")
            if hit_pages:
                add_entry(str(path), "\n".join(hit_pages[:3]))
        except Exception as e:
            console.print(f"[yellow]PDF extract failed for {path}: {e}")

OUT.write_text("\n".join(lines))
console.print(f"[green]Wrote {OUT} with {len(lines)} lines")
