import pathlib, re, json, bibtexparser, datetime

DOCS = pathlib.Path("docs")
index_lines = ["# 📚 Docs Index (auto-generated)\n",
               f"_Updated: {datetime.date.today()}_\n"]

bib_database = bibtexparser.bibdatabase.BibDatabase()

for file in sorted(DOCS.rglob("*")):
    if file.is_file():
        rel = file.relative_to(DOCS)
        # look for 'Abstract: ...' line in first 10 lines
        abstract = "⚠️ NO ABSTRACT"
        with file.open("r", errors="ignore") as f:
            head = [next(f, "") for _ in range(10)]
        for line in head:
            m = re.match(r"Abstract:\s*(.+)", line, re.I)
            if m:
                abstract = m.group(1).strip()
                break
        index_lines.append(f"* [{rel}]({rel}) — {abstract}")

        # crude: if PDF or MD contains DOI tag, add to bib
        doi = None
        for l in head:
            m = re.search(r"10\.\d{4,9}/[^\s]+", l)
            if m:
                doi = m.group(0)
                break
        if doi:
            bib_database.entries.append({
                "ENTRYTYPE": "misc",
                "ID": rel.stem,
                "doi": doi,
                "title": rel.stem,
                "howpublished": rel.as_posix(),
            })

# write outputs
(DOCS / "INDEX.md").write_text("\n".join(index_lines))
with open(DOCS / "REFERENCES.bib", "w") as f:
    bibtexparser.dump(bib_database, f)
