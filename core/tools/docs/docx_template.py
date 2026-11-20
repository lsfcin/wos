# docx_template.py — fill a labelled .docx form table keeping its formatting, and read it back the same way
#
# A form table is one whose cells open with a label ("NOME:", "EMENTA:") and carry the value after
# it. A label is `(prefix, key, mode)`:
#   inline  the value replaces the cell's first paragraph, after the label — templates often ship a
#           default there ("60h", "NÃO TEM"), so appending would keep both
#   block   the value is appended below the label, one paragraph per line
#   cell    the whole cell becomes `prefix + value`, one paragraph per line — for a cell that packs
#           sub-labels the template pre-fills ("Teórica: 60h / Prática: / Extensão:")
#
# Why python-docx and not the Docs API: a table nested in an `sdt` content control survives neither a
# markdown round trip nor python-docx's `doc.tables`, so the table is found by XPath (`.//w:tbl`) and
# deep-copied into a blank document.
import copy

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table

MODES = ("inline", "block", "cell")


def uniq_cells(row) -> list:
    """A merged cell appears once per grid column it spans; return each underlying cell once."""
    seen, out = set(), []
    for cell in row.cells:
        if id(cell._tc) not in seen:
            seen.add(id(cell._tc))
            out.append(cell)
    return out


def match_label(text: str, labels: list) -> tuple:
    """(key, mode, remainder) for the first label `text` starts with, else (None, None, None)."""
    for prefix, key, mode in labels:
        if text.startswith(prefix):
            return key, mode, text[len(prefix):]
    return None, None, None


def set_font(run_el, name: str) -> None:
    rpr = run_el.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), name)


def _write_lines(cell, lines: list, replace: bool) -> None:
    if replace:
        for extra in list(cell.paragraphs[1:]):
            extra._element.getparent().remove(extra._element)
        for run in list(cell.paragraphs[0].runs):
            run._element.getparent().remove(run._element)
        cell.paragraphs[0].add_run(lines[0])
        lines = lines[1:]
    for line in lines:
        cell.add_paragraph().add_run(line)


def fill_cell(cell, prefix: str, mode: str, value: str) -> None:
    if mode == "inline":
        _write_lines(cell, [prefix + " " + value], replace=True)
    elif mode == "cell":
        _write_lines(cell, (prefix + value).split("\n"), replace=True)
    elif mode == "block":
        _write_lines(cell, value.split("\n"), replace=False)
    else:
        raise ValueError(f"unknown label mode {mode!r}; expected one of {MODES}")


def from_template(template: str) -> tuple:
    """A blank document holding a deep copy of the template's first table: (document, table)."""
    tbl_el = copy.deepcopy(Document(template).element.body.findall(".//" + qn("w:tbl"))[0])
    doc = Document()
    body = doc.element.body
    for p in [el for el in body if el.tag == qn("w:p")]:
        body.remove(p)
    body.insert(list(body).index(body.find(qn("w:sectPr"))), tbl_el)
    return doc, Table(tbl_el, doc)


def fill_table(table, labels: list, fields: dict) -> list:
    """Write every non-empty field into the cell its label opens; return the label keys never placed."""
    placed = set()
    for row in table.rows:
        for cell in uniq_cells(row):
            text = cell.text.strip()
            for prefix, key, mode in labels:
                if text.startswith(prefix) and fields.get(key):
                    fill_cell(cell, prefix, mode, fields[key])
                    placed.add(key)
                    break
    known = {key for _, key, _ in labels}
    return [k for k, v in fields.items() if v and k in known and k not in placed]


def fill(template: str, labels: list, fields: dict, out: str, font: str = "") -> list:
    """Template table + fields → `out`. Returns the label keys that found no cell (template drift)."""
    doc, table = from_template(template)
    missing = fill_table(table, labels, fields)
    if font:
        for run_el in table._tbl.iter(qn("w:r")):
            set_font(run_el, font)
    doc.save(out)
    return missing


def _roman(n: int) -> str:
    out = ""
    for value, digits in ((1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
                          (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= value:
            out, n = out + digits, n - value
    return out


_FORMATS = {"decimal": str, "lowerLetter": lambda n: chr(96 + n), "upperLetter": lambda n: chr(64 + n),
            "lowerRoman": _roman, "upperRoman": lambda n: _roman(n).upper()}


def _levels(doc) -> dict:
    """numId → {ilvl: (numFmt, lvlText, start)} from the numbering part (empty when there is none)."""
    try:
        numbering = doc.part.numbering_part.element
    except (KeyError, NotImplementedError):
        return {}
    abstract = {a.get(qn("w:abstractNumId")): a for a in numbering.findall(qn("w:abstractNum"))}
    out = {}
    for num in numbering.findall(qn("w:num")):
        levels = {}
        for lvl in abstract[num.find(qn("w:abstractNumId")).get(qn("w:val"))].findall(qn("w:lvl")):
            fmt, text, start = (lvl.find(qn(f"w:{tag}")) for tag in ("numFmt", "lvlText", "start"))
            levels[int(lvl.get(qn("w:ilvl")))] = (fmt.get(qn("w:val")) if fmt is not None else "decimal",
                                                  text.get(qn("w:val")) if text is not None else "",
                                                  int(start.get(qn("w:val"))) if start is not None else 1)
        out[num.get(qn("w:numId"))] = levels
    return out


def paragraphs(path: str) -> list:
    """Body paragraphs as the reader sees them: a list item carries its rendered label ("1.2. Texto").

    Word stores a list number as numbering state, not text, so `paragraph.text` drops it. A bullet
    renders as "-", an unknown format as its lvlText unexpanded; counters restart per list.
    """
    doc = Document(path)
    levels, counters, out = _levels(doc), {}, []
    for p in doc.paragraphs:
        num_pr = p._p.pPr.numPr if p._p.pPr is not None else None
        if num_pr is None and p.style is not None and p.style.element.pPr is not None:
            num_pr = p.style.element.pPr.numPr  # numbering inherited from a list style
        if num_pr is None or num_pr.numId is None or str(num_pr.numId.val) not in levels:
            out.append(p.text)
            continue
        num_id, ilvl = str(num_pr.numId.val), int(num_pr.ilvl.val) if num_pr.ilvl is not None else 0
        spec = levels[num_id]
        count = counters.setdefault(num_id, {})
        count[ilvl] = count.get(ilvl, spec.get(ilvl, ("", "", 1))[2] - 1) + 1
        for deeper in [k for k in count if k > ilvl]:
            del count[deeper]
        fmt, label, _ = spec.get(ilvl, ("bullet", "", 1))
        if fmt == "bullet":
            label = "-"
        else:
            for k in range(ilvl + 1):
                render = _FORMATS.get(spec.get(k, ("decimal",))[0], str)
                label = label.replace(f"%{k + 1}", render(count.get(k, 1)))
        out.append(f"{label} {p.text}".strip())
    return out


def read(path: str, labels: list, name: str = "") -> dict:
    """Fields of the first table (or the first whose top cell contains `name`), keyed by label.

    A cell with no label continues the last `block` field, so a value split across cells reads
    whole. When the first label met reappears, the table packs a second record and reading stops.
    """
    doc = Document(path)
    for tbl_el in doc.element.body.findall(".//" + qn("w:tbl")):
        table = Table(tbl_el, doc)
        if name and name.upper() not in table.rows[0].cells[0].text.upper():
            continue
        fields, current, first = {}, None, None
        for row in table.rows:
            for cell in uniq_cells(row):
                key, mode, rest = match_label(cell.text, labels)
                if key:
                    if key == first:
                        return fields
                    first = first or key
                    current = (key, mode)
                    fields[key] = rest.lstrip("\n ")
                elif current and current[1] == "block":
                    fields[current[0]] = (fields[current[0]] + "\n" + cell.text).strip("\n")
        return fields
    raise LookupError(f"no table{' for ' + repr(name) if name else ''} in {path}")
