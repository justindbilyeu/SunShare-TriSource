import pathlib, re, json, datetime, markdown, frontmatter
from collections import defaultdict
from PyPDF2 import PdfReader
import bibtexparser, pandas as pd

DOCS = pathlib.Path("docs")
index_lines = ["# Extended Docs Index", f"_Updated {datetime.date.today()}_", ""]
tag_map = defaultdict(list)
bib_db = bibtexparser.bibdatabase.BibDatabase()

for file in sorted(DOCS.rglob("*")):
    if not file.is_file():
        continue
    rel = file.relative_to(DOCS)
    abs_tags, abstract, doi = set(), "", None

    if file.suffix.lower() in {".md", ".markdown"}:
        post = frontmatter.load(file)
        abstract = post.get("abstract", "")[:200]
        abs_tags.update(post.get("tags", []))
        raw = markdown.markdown(post.content).lower()
    elif file.suffix.lower() == ".pdf":
        reader = PdfReader(str(file))
        first_page = reader.pages[0].extract_text()[:2000].lower()
        m = re.search(r"abstract[:.\s]*(.+?)\n", first_page, re.I)
        abstract = m.group(1)[:200] if m else ""
        mdoi = re.search(r"10\.\d{4,9}/\S+", first_page)
        doi = mdoi.group(0) if mdoi else None
        raw = first_page
    else:
        continue  # skip binary etc.

    # simple keyword tagging
    for kw in ("awg", "desal", "microbial", "energy", "edge ai"):
        if kw in raw:
            abs_tags.add(kw)

    tag_map.update({t: tag_map[t] + [str(rel)] for t in abs_tags})

    index_lines.append(f"* [{rel}]({rel}) — {abstract or '⚠️ no abstract'}")

    if doi:
        bib_db.entries.append({
            "ENTRYTYPE": "misc",
            "ID": rel.stem,
            "title": rel.stem.replace('_', ' '),
            "howpublished": rel.as_posix(),
            "doi": doi
        })

# write outputs
(DOCS / "INDEX.md").write_text("\n".join(index_lines))
(DOCS / "ANNOTATED_BIB.md").write_text(
    "\n".join([f"* **{e['ID']}** — DOI: {e['doi']}" for e in bib_db.entries])
)
(DOCS / "tags.json").write_text(json.dumps(tag_map, indent=2))
with open(DOCS / "REFERENCES.bib", "w") as fh:
    bibtexparser.dump(bib_db, fh)
TAG_ALIAS = {
    "edge ai": "edge_ai",
    "ai edge": "edge_ai",
    "awg": "atmospheric_water",
}
for t in abs_tags:
    tag_map[TAG_ALIAS.get(t, t)].append(str(rel))
    import tabula, pandas as pd, subprocess, tempfile

if file.suffix.lower() == ".pdf" and "energy" in file.stem.lower():
    try:
        dfs = tabula.read_pdf(file.as_posix(), pages="all", lattice=True)
        for i, df in enumerate(dfs):
            out = pathlib.Path("analysis") / f"{rel.stem}_table{i}.csv"
            out.parent.mkdir(exist_ok=True)
            df.to_csv(out, index=False)
    except Exception as e:
        print("Tabula failed:", e)
    
