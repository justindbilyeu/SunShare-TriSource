#!/usr/bin/env python3
"""
Scan docs/, create INDEX.md and REFERENCES.bib.
Each file’s first 'Abstract:' line becomes its one-line summary.
If a DOI is found, it’s added to the BibTeX.
"""
import pathlib, re, datetime, bibtexparser

DOCS = pathlib.Path("docs")
index_lines = [
    "# 📚 Docs Index (auto-generated)",
    f"_Updated {datetime.date.today()}_",
    ""
]

bib_db = bibtexparser.bibdatabase.BibDatabase()

for path in sorted(DOCS.rglob("*")):
    if not path.is_file():
        continue
    rel = path.relative_to(DOCS)
    abstract = "⚠️ Abstract missing"
    doi = None

    with path.open(errors="ignore") as fh:
        for _ in range(15):                # scan first 15 lines
            line = fh.readline()
            if not line:
                break
            m = re.match(r"Abstract:\s*(.+)", line, re.I)
            if m:
                abstract = m.group(1).strip()
            d = re.search(r"10\.\d{4,9}/\S+", line)   # crude DOI
            if d and not doi:
                doi = d.group(0)

    index_lines.append(f"* [{rel}]({rel}) — {abstract}")

    if doi:
        bib_db.entries.append({
            "ENTRYTYPE": "misc",
            "ID": rel.stem,
            "title": rel.stem.replace('_', ' '),
            "doi": doi,
            "howpublished": rel.as_posix()
        })

# write outputs
(DOCS / "INDEX.md").write_text("\n".join(index_lines) + "\n")

with (DOCS / "REFERENCES.bib").open("w") as fh:
    bibtexparser.dump(bib_db, fh)
