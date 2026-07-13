#!/usr/bin/env python3
"""
compare_metadata.py

Compares ALL section elements (MTD, SML, SMF, SME) between:
  - mzTab-M v2.0 specification:
      ../mzTab/specification_document-releases/2_0-Metabolomics-Release/
          mzTab_format_specification_2_0-M_release.adoc
  - mzTab-M v2.1 schema reference:
      docs/mztabm/modules/developers/partials/mzTab_m_2_1_schema.adoc

Output: metadata_comparison.md

Usage:
    python3 compare_metadata.py
"""

import argparse
import re
import os
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Paths – defaults (overridden by CLI arguments)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_OLD = os.path.join(
    SCRIPT_DIR,
    "specification_documents",
    "mzTab_m_2_0_schema.adoc",
)
DEFAULT_NEW = os.path.join(SCRIPT_DIR, "docs", "mztabm", "modules", "developers", "partials", "mzTab_m_2_1_schema.adoc")
DEFAULT_OUT = os.path.join(SCRIPT_DIR, "specification_documents", "mzTab_m_2_0_to_2_1_changes.adoc")


# ---------------------------------------------------------------------------
# Section name mapping – map free-form === header text to a short key
# ---------------------------------------------------------------------------
SECTION_PATTERNS = [
    (re.compile(r"metadata", re.I),                        "MTD"),
    (re.compile(r"small molecule feature", re.I),          "SMF"),
    (re.compile(r"small molecule evidence", re.I),         "SME"),
    (re.compile(r"small molecule", re.I),                  "SML"),  # after SMF/SME check
]

SECTION_TITLES = {
    "MTD": "Metadata (MTD) Section",
    "SML": "Small Molecule (SML) Section",
    "SMF": "Small Molecule Feature (SMF) Section",
    "SME": "Small Molecule Evidence (SME) Section",
}


def _identify_section(header: str) -> Optional[str]:
    for pat, key in SECTION_PATTERNS:
        if pat.search(header):
            return key
    return None


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Element:
    name: str           # raw header text, e.g. "mzTab-version"
    description: str = ""
    type_: str = ""
    mandatory: str = ""
    nullable: str = ""
    example: str = ""


# ---------------------------------------------------------------------------
# Canonicalise element name for cross-version matching
# ---------------------------------------------------------------------------
def _canon(name: str) -> str:
    """
    Normalise an element name for cross-version matching:
      - lower-case
      - remove AsciiDoc escapes (backslash before {)
      - strip trailing [n] / [1-n] that represent column-set cardinality in
        SML/SMF/SME section headers (e.g. abundance_assay[1-n] -> abundance_assay)
      - normalise interior [1-n] to [n] for MTD parameter cardinality
      - collapse whitespace
    """
    n = name.lower().strip()
    n = n.replace("\\{", "{")          # AsciiDoc escape: opt_\{id} -> opt_{id}
    n = re.sub(r"\s+", " ", n)
    # Strip trailing [1-n] or [n] — these appear on SML/SMF/SME column headers
    # where v2.0 uses [1-n] suffix but v2.1 drops it.
    n = re.sub(r"\[1-n\]$", "", n)
    n = re.sub(r"\[n\]$", "", n)
    # Normalise interior [1-n] → [n] (MTD parameters still keep inner brackets)
    n = re.sub(r"\[1-n\]", "[n]", n)
    return n.strip()


# ---------------------------------------------------------------------------
# AsciiDoc table field extractors
# ---------------------------------------------------------------------------
def _clean(text: str) -> str:
    return "\n".join(l.rstrip() for l in text.strip().splitlines())


def _extract_field(body: str, field_name: str) -> str:
    """
    Extract table-cell value for  |*FieldName* a|...  or  |*FieldName* |...
    The cell-content specifier ('a') comes BEFORE the pipe in AsciiDoc.
    """
    pat = re.compile(
        r"\|\*" + re.escape(field_name) + r"\*[:\s]*a?\|(.*?)(?=\n\||\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    m = pat.search(body)
    if not m:
        # Variant: *FieldName:* (used in some v2.0 rows)
        pat2 = re.compile(
            r"\|\*" + re.escape(field_name) + r"[:\*]+\s*a?\|(.*?)(?=\n\||\Z)",
            re.DOTALL | re.IGNORECASE,
        )
        m = pat2.search(body)
    return _clean(m.group(1)) if m else ""


def _extract_example(body: str) -> str:
    ex_pat = re.compile(
        r"\|\*Example\*\s*a?\|(.*?)(?=\n\|[=|]|\Z)",
        re.DOTALL | re.IGNORECASE,
    )
    m = ex_pat.search(body)
    if not m:
        return ""
    raw = m.group(1)
    raw = re.sub(r"^\s*\.\.\.\.\s*$", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"^\s*\[subs=[^\]]+\]\s*$", "", raw, flags=re.MULTILINE)
    return _clean(raw)


def _parse_element(header: str, body_lines: list[str]) -> Element:
    body = "\n".join(body_lines)
    return Element(
        name=header,
        description=_extract_field(body, "Description"),
        type_=_extract_field(body, "Type"),
        mandatory=_extract_field(body, "Mandatory"),
        nullable=_extract_field(body, "Is Nullable"),
        example=_extract_example(body),
    )


# ---------------------------------------------------------------------------
# Full-file parser: splits into level-3 sections then level-4 elements
# ---------------------------------------------------------------------------
def parse_adoc(path: str, v20_mtd_start: Optional[str] = None) -> dict[str, list[Element]]:
    """
    Returns {section_key: [Element, ...]} for MTD, SML, SMF, SME.

    v20_mtd_start: optional regex – for v2.0 we skip the preamble of the
    metadata chapter until we hit the *Core Metadata* marker, so that we
    only capture the per-element blocks and not the narrative text.
    """
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()

    lines = raw.splitlines()

    sec3_re  = re.compile(r"^={3}\s+(.+)$")
    sec4_re  = re.compile(r"^={4}\s+(.+)$")

    sections: dict[str, list[Element]] = {k: [] for k in SECTION_TITLES}

    current_section: Optional[str] = None
    current_header:  Optional[str] = None
    current_body:    list[str]     = []

    # For v2.0, we want to skip MTD narrative until the *Core Metadata* marker
    # so that section-3 level text blobs don't create spurious elements.
    # We achieve this by treating the MTD section as only active after the marker.
    mtd_active = (v20_mtd_start is None)  # for v2.1 we're always active
    mtd_trigger = re.compile(v20_mtd_start) if v20_mtd_start else None

    def flush_element() -> None:
        if current_section and current_header:
            el = _parse_element(current_header, current_body)
            sections[current_section].append(el)

    for line in lines:
        # Check for v2.0 MTD activation trigger
        if mtd_trigger and mtd_trigger.search(line):
            mtd_active = True

        # Level-3 section boundary
        m3 = sec3_re.match(line)
        if m3:
            flush_element()
            current_header = None
            current_body   = []
            key = _identify_section(m3.group(1))
            current_section = key  # None if unrecognised
            continue

        # Level-4 element header
        m4 = sec4_re.match(line)
        if m4:
            flush_element()
            current_header = m4.group(1).strip()
            current_body   = []
            # For v2.0 MTD section, only capture elements after the trigger
            if current_section == "MTD" and not mtd_active:
                current_header = None
            continue

        if current_header is not None:
            current_body.append(line)

    flush_element()
    return sections


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
def match_elements(
    v20: list[Element], v21: list[Element]
) -> list[tuple[Optional[Element], Optional[Element]]]:
    """Pair elements by canonical name, preserving v2.0 order then v2.1-only."""
    v20_map = {_canon(e.name): e for e in v20}
    v21_map = {_canon(e.name): e for e in v21}

    seen: set[str] = set()
    ordered: list[str] = []

    for e in v20:
        k = _canon(e.name)
        if k not in seen:
            ordered.append(k)
            seen.add(k)

    for e in v21:
        k = _canon(e.name)
        if k not in seen:
            ordered.append(k)
            seen.add(k)

    return [(v20_map.get(k), v21_map.get(k)) for k in ordered]


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# AsciiDoc rendering helpers
# ---------------------------------------------------------------------------

def _adoc_cell(text: str) -> str:
    """Escape text for use in a regular (non-asciidoc) AsciiDoc table cell."""
    if not text:
        return "—"
    text = text.replace("|", "{vbar}")
    # Soft line-break: AsciiDoc ' +\n' continues within a cell
    lines = [l.rstrip() for l in text.splitlines()]
    return (" +\n").join(lines).strip() or "—"


def _adoc_example_block(text: str) -> str:
    """
    Return text suitable for placement inside an `a|` cell as a literal block.
    Returns an empty string when there is no content.
    """
    if not text:
        return ""
    lines = [l.rstrip() for l in text.splitlines() if l.rstrip()]
    body = "\n".join(lines)
    body = body.replace("|", "{vbar}")
    return f"....\n{body}\n...."


def _mandatory_badge(mandatory: str) -> str:
    """AsciiDoc bold badge for summary tables."""
    m = mandatory.strip().lower()
    if m in ("true", "yes", "*true*"):
        return "*True*"
    if m in ("false", "no", "*false*"):
        return "False"
    return mandatory.strip() or "—"


def _mandatory_plain(mandatory: str) -> str:
    m = mandatory.strip().lower()
    if m in ("true", "yes", "*true*"):
        return "True"
    if m in ("false", "no", "*false*"):
        return "False"
    return mandatory.strip() or "—"


def _nullable_plain(nullable: str) -> str:
    n = nullable.strip().lower().strip("*")
    if n == "true":
        return "True"
    if n == "false":
        return "False"
    return nullable.strip() or "—"


# ---------------------------------------------------------------------------
# Render one section comparison (AsciiDoc)
# ---------------------------------------------------------------------------
def _render_section(
    section_key: str,
    pairs: list[tuple[Optional[Element], Optional[Element]]],
    out: list[str],
) -> None:
    title = SECTION_TITLES[section_key]
    out.append(f"== {title}")
    out.append("")

    added   = [p for p in pairs if p[0] is None]
    removed = [p for p in pairs if p[1] is None]

    def _summary_table(items: list[Element]) -> None:
        out.append('[cols="20,~,10,10,10",options="header"]')
        out.append("|===")
        out.append("| Column/Field | Description | Type | Mandatory | Nullable")
        out.append("")
        for el in items:
            desc = _adoc_cell(el.description)
            out.append(f"| `{el.name}`")
            out.append(f"a| {desc}")
            out.append(f"| {_adoc_cell(el.type_)}")
            out.append(f"| {_mandatory_badge(el.mandatory)}")
            out.append(f"| {_nullable_plain(el.nullable)}")
            out.append("")
        out.append("|===")
        out.append("")

    if added:
        out.append("=== 🟢 Added in v2.1")
        out.append("")
        _summary_table([el for _, el in added if el is not None])

    if removed:
        out.append("=== 🔴 Removed in v2.1")
        out.append("")
        _summary_table([el for el, _ in removed if el is not None])

    out.append("=== Element Details")
    out.append("")

    for v20_el, v21_el in pairs:
        elem_name = (v20_el or v21_el).name
        is_added   = v20_el is None
        is_removed = v21_el is None

        badge = ""
        if is_added:
            badge = " 🟢 _(Added in v2.1)_"
        elif is_removed:
            badge = " 🔴 _(Removed in v2.1)_"

        out.append(f"==== `{elem_name}`{badge}")
        out.append("")

        # Changed-fields admonition
        if v20_el and v21_el:
            changed: list[str] = []
            if v20_el.description != v21_el.description:
                changed.append("Description")
            if v20_el.type_ != v21_el.type_:
                changed.append("Type")
            if _mandatory_plain(v20_el.mandatory) != _mandatory_plain(v21_el.mandatory):
                changed.append("Mandatory")
            if _nullable_plain(v20_el.nullable) != _nullable_plain(v21_el.nullable):
                changed.append("Nullable")
            if v20_el.example != v21_el.example:
                changed.append("Example")
            if changed:
                out.append(f"NOTE: ⚠️ Changed fields: {', '.join(changed)}")
                out.append("")

        # Detail table: Field | v2.0 | v2.1
        # Use 'a|' cells for Description, Type, and Example (may be multi-line).
        # Use plain '|' cells for Mandatory and Nullable (always short).
        out.append('[cols="15,~,~",options="header"]')
        out.append("|===")
        out.append("| Field | v2.0 | v2.1")
        out.append("")

        def _text_differs(a: str, b: str) -> bool:
            return v20_el is not None and v21_el is not None and a != b

        def _plain_cell(val: str, present: bool, highlight: bool) -> str:
            """Simple cell value, bolded when it differs."""
            if not present:
                return "_(not present)_"
            s = _adoc_cell(val)
            if highlight and s != "—":
                return f"*{s}*"
            return s

        def _rich_cell(val: str, present: bool) -> str:
            """Cell body for `a|` cells (Description / Type)."""
            if not present:
                return "_(not present)_"
            return _adoc_cell(val)

        def _emit_row(label: str, v20_val: str, v21_val: str, rich: bool = False) -> None:
            differs = _text_differs(v20_val, v21_val)
            if rich:
                v20_body = _rich_cell(v20_val, v20_el is not None)
                v21_body = _rich_cell(v21_val, v21_el is not None)
                if differs:
                    if v20_body != "—":
                        v20_body = f"*{v20_body}*"
                    if v21_body != "—":
                        v21_body = f"*{v21_body}*"
                out.append(f"| {label}")
                out.append(f"a| {v20_body}")
                out.append(f"a| {v21_body}")
            else:
                v20_s = _plain_cell(v20_val, v20_el is not None, differs)
                v21_s = _plain_cell(v21_val, v21_el is not None, differs)
                out.append(f"| {label} | {v20_s} | {v21_s}")
            out.append("")

        def _emit_example_row(v20_val: str, v21_val: str) -> None:
            v20_block = _adoc_example_block(v20_val) if v20_el else ""
            v21_block = _adoc_example_block(v21_val) if v21_el else ""
            v20_body  = v20_block if v20_block else ("_(not present)_" if not v20_el else "—")
            v21_body  = v21_block if v21_block else ("_(not present)_" if not v21_el else "—")
            out.append("| Example")
            out.append(f"a| {v20_body}")
            out.append(f"a| {v21_body}")
            out.append("")

        desc_v20 = v20_el.description if v20_el else ""
        desc_v21 = v21_el.description if v21_el else ""
        type_v20 = v20_el.type_       if v20_el else ""
        type_v21 = v21_el.type_       if v21_el else ""
        mand_v20 = _mandatory_plain(v20_el.mandatory) if v20_el else ""
        mand_v21 = _mandatory_plain(v21_el.mandatory) if v21_el else ""
        null_v20 = _nullable_plain(v20_el.nullable)   if v20_el else ""
        null_v21 = _nullable_plain(v21_el.nullable)   if v21_el else ""
        ex_v20   = v20_el.example if v20_el else ""
        ex_v21   = v21_el.example if v21_el else ""

        _emit_row("Description", desc_v20, desc_v21, rich=True)
        _emit_row("Type",        type_v20, type_v21, rich=True)
        _emit_row("Mandatory",   mand_v20, mand_v21, rich=False)
        _emit_row("Nullable",    null_v20, null_v21, rich=False)
        _emit_example_row(ex_v20, ex_v21)

        out.append("|===")
        out.append("")


# ---------------------------------------------------------------------------
# Top-level render (AsciiDoc)
# ---------------------------------------------------------------------------
def render_asciidoc(
    v20_sections: dict[str, list[Element]],
    v21_sections: dict[str, list[Element]],
) -> str:
    out: list[str] = []

    out.append("= mzTab-M Complete Column/Field Comparison: v2.0 vs v2.1")
    out.append(":toc: left")
    out.append(":toclevels: 3")
    out.append(":numbered:")
    out.append("")
    out.append(
        "Element-by-element comparison of all four mzTab-M sections "
        "(MTD, SML, SMF, SME) between version 2.0 and version 2.1."
    )
    out.append("")
    out.append("*Legend:*")
    out.append("")
    out.append("* 🟢 *Added in v2.1* – element is new, not present in v2.0")
    out.append("* 🔴 *Removed in v2.1* – element existed in v2.0 but is absent in v2.1")
    out.append("* ⚠️ *Changed* – one or more fields differ between versions")
    out.append("* Differing cell values are shown in *bold* in the detail rows")
    out.append("")

    # Summary table
    out.append("== Summary")
    out.append("")
    out.append('[cols="4,1,1,1,1,1",options="header"]')
    out.append("|===")
    out.append("| Section | v2.0 elements | v2.1 elements | Added | Removed | Changed")
    out.append("")
    for key in ("MTD", "SML", "SMF", "SME"):
        v20_els = v20_sections.get(key, [])
        v21_els = v21_sections.get(key, [])
        pairs   = match_elements(v20_els, v21_els)
        added   = sum(1 for a, b in pairs if a is None)
        removed = sum(1 for a, b in pairs if b is None)
        changed = sum(
            1 for a, b in pairs
            if a and b and (
                a.description != b.description
                or a.type_ != b.type_
                or _mandatory_plain(a.mandatory) != _mandatory_plain(b.mandatory)
                or _nullable_plain(a.nullable)   != _nullable_plain(b.nullable)
                or a.example != b.example
            )
        )
        out.append(
            f"| {SECTION_TITLES[key]} | {len(v20_els)} | {len(v21_els)} | "
            f"{added} | {removed} | {changed}"
        )
        out.append("")
    out.append("|===")
    out.append("")

    # Per-section detailed comparison
    for key in ("MTD", "SML", "SMF", "SME"):
        v20_els = v20_sections.get(key, [])
        v21_els = v21_sections.get(key, [])
        pairs   = match_elements(v20_els, v21_els)
        _render_section(key, pairs, out)

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare mzTab-M AsciiDoc specification documents element by element.",
    )
    parser.add_argument(
        "--old",
        metavar="PATH",
        default=DEFAULT_OLD,
        help="Path to the old (v2.0) AsciiDoc spec file (default: %(default)s)",
    )
    parser.add_argument(
        "--new",
        metavar="PATH",
        default=DEFAULT_NEW,
        help="Path to the new (v2.1) AsciiDoc spec/schema file (default: %(default)s)",
    )
    parser.add_argument(
        "--out",
        metavar="PATH",
        default=DEFAULT_OUT,
        help="Output Markdown file path (default: %(default)s)",
    )
    args = parser.parse_args()

    print(f"Parsing old spec: {args.old}")
    v20 = parse_adoc(args.old, v20_mtd_start=r"\*Core Metadata\*")
    for k, els in v20.items():
        print(f"  {k}: {len(els)} elements")

    print(f"Parsing new spec: {args.new}")
    v21 = parse_adoc(args.new)
    for k, els in v21.items():
        print(f"  {k}: {len(els)} elements")

    md = render_asciidoc(v20, v21)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"\nWrote comparison to: {args.out}")


if __name__ == "__main__":
    main()
