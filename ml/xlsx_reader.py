"""Minimal, dependency-free .xlsx reader (stdlib only: zipfile + xml).

Written so the ML pipeline does not require pandas/openpyxl to be
installed (this environment's network access to PyPI proved unreliable
for large wheels such as scipy/pandas). It only supports what the survey
export actually uses: shared strings, inline numbers, one header row.

Usage:
    sheets = list_sheets(path)                       # -> {name: index}
    rows = read_sheet(path, sheet_name="Form Responses 1")
    # rows: list[dict[str, str]], keyed by the first-row header text
"""

from __future__ import annotations

import re
import zipfile
from xml.etree import ElementTree as ET

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PKG_REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def _col_to_index(cell_ref: str) -> int:
    """'C7' -> 2 (0-based column index)."""
    letters = re.match(r"[A-Z]+", cell_ref).group(0)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def _load_shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    strings = []
    for si in root.findall(f"{_NS}si"):
        # Concatenate all <t> text runs (handles rich text with multiple <r>).
        text = "".join(t.text or "" for t in si.findall(f".//{_NS}t"))
        strings.append(text)
    return strings


def list_sheets(path: str) -> dict[str, str]:
    """Returns {sheet_name: internal_zip_path}."""
    with zipfile.ZipFile(path) as z:
        wb_root = ET.fromstring(z.read("xl/workbook.xml"))
        rels_root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {
            rel.get("Id"): rel.get("Target")
            for rel in rels_root.findall(f"{_PKG_REL_NS}Relationship")
        }
        sheets = {}
        for sheet in wb_root.findall(f"{_NS}sheets/{_NS}sheet"):
            name = sheet.get("name")
            rid = sheet.get(f"{_REL_NS}id")
            target = rid_to_target.get(rid, "")
            sheets[name] = f"xl/{target}" if not target.startswith("xl/") else target
        return sheets


def read_sheet(path: str, sheet_name: str) -> list[dict[str, str]]:
    """Reads a sheet into a list of {header_text: cell_value} dicts.

    The first row is treated as the header row. Numeric cells are returned
    as their raw string representation; shared-string / inline-string
    cells are returned as text. Blank cells are omitted from the row dict.
    """
    with zipfile.ZipFile(path) as z:
        sheets = list_sheets(path)
        if sheet_name not in sheets:
            raise KeyError(f"Sheet '{sheet_name}' not found among {list(sheets)}")
        shared = _load_shared_strings(z)
        sheet_root = ET.fromstring(z.read(sheets[sheet_name]))

        header: dict[int, str] = {}
        rows: list[dict[str, str]] = []
        for r, row in enumerate(sheet_root.findall(f".//{_NS}sheetData/{_NS}row")):
            values: dict[int, str] = {}
            for c in row.findall(f"{_NS}c"):
                ref = c.get("r")
                col = _col_to_index(ref)
                cell_type = c.get("t")
                if cell_type == "s":
                    v = c.find(f"{_NS}v")
                    text = shared[int(v.text)] if v is not None else ""
                elif cell_type == "inlineStr":
                    is_el = c.find(f"{_NS}is")
                    text = "".join(t.text or "" for t in is_el.findall(f".//{_NS}t")) if is_el is not None else ""
                else:
                    v = c.find(f"{_NS}v")
                    text = v.text if v is not None else ""
                if text:
                    values[col] = text
            if r == 0:
                header = {col: text for col, text in values.items()}
                continue
            row_dict = {
                header.get(col, f"col_{col}"): text for col, text in values.items()
            }
            if row_dict:
                rows.append(row_dict)
        return rows
