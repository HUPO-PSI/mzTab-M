#!/usr/bin/env python3
"""Create the pandoc reference.docx used for the DOCX specification.

Starts from pandoc's built-in reference.docx and
- pins the Word theme fonts so body text and headings are sans-serif,
  independent of the pandoc version (older pandoc releases default to the
  serif Cambria for body text). Code and verbatim text use pandoc's
  "Source Code" / "Verbatim Char" styles, which stay in the monospace Consolas;
- styles the title page like the PDF (centered title/subtitle in the logo
  blues) and starts every chapter (Heading 1) and the table of contents on a
  new page, as in the PDF;
- defines the TOC 1-3 entry styles used by postprocess_docx.py;
- styles tables like the PDF (light blue-grey grid, tinted header row in the
  header blue, 8.5pt text, 8pt code) and code blocks (light background).
  postprocess_docx.py assigns the Table* paragraph/character styles to the
  content of table cells.

Regenerate with:
    pandoc -o default.docx --print-default-data-file reference.docx
    python3 make_reference_docx.py default.docx reference.docx
"""
import re
import sys
import zipfile

BODY_FONT = "Calibri"     # Word theme "minor" font (body text, tables)
HEADING_FONT = "Calibri"  # Word theme "major" font (headings, title)
CODE_FONT = "Consolas"

HEADER_BLUE = "2F4256"
MTD_BLUE = "4D657F"
MUTED = "5A6B7D"

THEME = "word/theme/theme1.xml"

# Complete replacements for pandoc's title-page styles.
TITLE_PAGE_STYLES = {
    "Title": f"""<w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title" /><w:basedOn w:val="Normal" /><w:next w:val="Subtitle" />
    <w:uiPriority w:val="10" /><w:qFormat />
    <w:pPr><w:keepNext /><w:spacing w:before="0" w:after="160" w:line="240" w:lineRule="auto" /><w:jc w:val="center" /></w:pPr>
    <w:rPr><w:rFonts w:asciiTheme="majorHAnsi" w:hAnsiTheme="majorHAnsi" /><w:b /><w:bCs />
      <w:color w:val="{HEADER_BLUE}" /><w:kern w:val="28" /><w:sz w:val="52" /><w:szCs w:val="52" /></w:rPr>
  </w:style>""",
    "Subtitle": f"""<w:style w:type="paragraph" w:styleId="Subtitle">
    <w:name w:val="Subtitle" /><w:basedOn w:val="Normal" /><w:next w:val="BodyText" />
    <w:uiPriority w:val="11" /><w:qFormat />
    <w:pPr><w:keepNext /><w:spacing w:before="0" w:after="240" /><w:jc w:val="center" /></w:pPr>
    <w:rPr><w:i /><w:iCs /><w:color w:val="{MTD_BLUE}" /><w:sz w:val="30" /><w:szCs w:val="30" /></w:rPr>
  </w:style>""",
    "Date": f"""<w:style w:type="paragraph" w:styleId="Date">
    <w:name w:val="Date" /><w:basedOn w:val="Normal" /><w:next w:val="BodyText" /><w:qFormat />
    <w:pPr><w:keepNext /><w:keepLines /><w:jc w:val="center" /></w:pPr>
    <w:rPr><w:color w:val="{MUTED}" /></w:rPr>
  </w:style>""",
}

GRID = "C5D0DC"
HEAD_FILL = "E6EDF4"
CODE_FILL = "F4F6F9"
CODE_RULE = "D6DEE7"

_BORDERS = "".join(f'<w:{side} w:val="single" w:sz="4" w:space="0" w:color="{GRID}" />'
                   for side in ("top", "left", "bottom", "right", "insideH", "insideV"))

# Replacements / additions for tables and code (style id -> definition).
TABLE_STYLES = {
    "Table": f"""<w:style w:type="table" w:default="1" w:styleId="Table">
    <w:name w:val="Table" /><w:basedOn w:val="TableNormal" /><w:uiPriority w:val="59" /><w:qFormat />
    <w:tblPr><w:tblInd w:w="0" w:type="dxa" /><w:tblBorders>{_BORDERS}</w:tblBorders>
      <w:tblCellMar><w:top w:w="40" w:type="dxa" /><w:left w:w="85" w:type="dxa" />
        <w:bottom w:w="40" w:type="dxa" /><w:right w:w="85" w:type="dxa" /></w:tblCellMar></w:tblPr>
    <w:tblStylePr w:type="firstRow"><w:rPr><w:b /><w:bCs /><w:color w:val="{HEADER_BLUE}" /></w:rPr>
      <w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="{HEAD_FILL}" /></w:tcPr></w:tblStylePr>
  </w:style>""",
    "TableText": """<w:style w:type="paragraph" w:customStyle="1" w:styleId="TableText">
    <w:name w:val="Table Text" /><w:basedOn w:val="Normal" /><w:qFormat />
    <w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto" /></w:pPr>
    <w:rPr><w:sz w:val="17" /><w:szCs w:val="17" /></w:rPr>
  </w:style>""",
    "TableHeading": f"""<w:style w:type="paragraph" w:customStyle="1" w:styleId="TableHeading">
    <w:name w:val="Table Heading" /><w:basedOn w:val="TableText" /><w:qFormat />
    <w:pPr><w:keepNext /></w:pPr>
    <w:rPr><w:b /><w:bCs /><w:color w:val="{HEADER_BLUE}" /></w:rPr>
  </w:style>""",
    "SourceCode": f"""<w:style w:type="paragraph" w:customStyle="1" w:styleId="SourceCode">
    <w:name w:val="Source Code" /><w:basedOn w:val="Normal" />
    <w:pPr><w:pBdr>{"".join(f'<w:{side} w:val="single" w:sz="4" w:space="4" w:color="{CODE_RULE}" />' for side in ("top", "left", "bottom", "right"))}</w:pBdr>
      <w:shd w:val="clear" w:color="auto" w:fill="{CODE_FILL}" />
      <w:wordWrap w:val="off" /><w:spacing w:before="120" w:after="120" w:line="240" w:lineRule="auto" /></w:pPr>
  </w:style>""",
    "TableSourceCode": """<w:style w:type="paragraph" w:customStyle="1" w:styleId="TableSourceCode">
    <w:name w:val="Table Source Code" /><w:basedOn w:val="SourceCode" />
    <w:pPr><w:spacing w:before="40" w:after="40" /></w:pPr>
  </w:style>""",
    "TableVerbatimChar": """<w:style w:type="character" w:customStyle="1" w:styleId="TableVerbatimChar">
    <w:name w:val="Table Verbatim Char" /><w:basedOn w:val="VerbatimChar" />
    <w:rPr><w:sz w:val="16" /><w:szCs w:val="16" /></w:rPr>
  </w:style>""",
}

# Table of contents entries (names must be "toc N" for Word to treat them as such).
TOC_STYLES = "".join(
    f"""<w:style w:type="paragraph" w:styleId="TOC{n}">
    <w:name w:val="toc {n}" /><w:basedOn w:val="Normal" /><w:next w:val="Normal" />
    <w:uiPriority w:val="39" /><w:unhideWhenUsed />
    <w:pPr><w:spacing w:before="{60 if n == 1 else 0}" w:after="40" /><w:ind w:left="{(n - 1) * 240}" /></w:pPr>
    {"<w:rPr><w:b /><w:bCs /></w:rPr>" if n == 1 else ""}
  </w:style>"""
    for n in (1, 2, 3)
)
STYLES = "word/styles.xml"


def set_theme_font(xml: str, which: str, typeface: str) -> str:
    pattern = re.compile(r'(<a:%s>\s*<a:latin typeface=")[^"]*(")' % which)
    xml, n = pattern.subn(r"\g<1>%s\g<2>" % typeface, xml)
    if n != 1:
        raise SystemExit(f"could not find <a:{which}> latin font in {THEME}")
    return xml


def _style_re(style_id: str) -> "re.Pattern[str]":
    return re.compile(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % style_id, re.S)


def patch_styles(xml: str) -> str:
    for style_id, definition in {**TITLE_PAGE_STYLES, **TABLE_STYLES}.items():
        xml, n = _style_re(style_id).subn(lambda _m: definition, xml)
        if n == 0:
            xml = xml.replace("</w:styles>", definition + "</w:styles>")
    # Chapters (and the TOC heading, which is based on Heading 1) start a new page.
    heading1 = _style_re("Heading1").search(xml)
    if not heading1:
        raise SystemExit(f"no Heading1 style in {STYLES}")
    patched = heading1.group(0).replace("<w:pPr>", "<w:pPr>\n      <w:pageBreakBefore />", 1)
    xml = xml[: heading1.start()] + patched + xml[heading1.end():]
    for n in (1, 2, 3):
        xml = _style_re(f"TOC{n}").sub("", xml)
    return xml.replace("</w:styles>", TOC_STYLES + "</w:styles>")


def main(src: str, dst: str) -> None:
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == THEME:
                xml = data.decode("utf-8")
                xml = set_theme_font(xml, "majorFont", HEADING_FONT)
                xml = set_theme_font(xml, "minorFont", BODY_FONT)
                data = xml.encode("utf-8")
            elif item.filename == STYLES:
                xml = data.decode("utf-8")
                if f'w:ascii="{CODE_FONT}"' not in xml:
                    raise SystemExit(f"expected the {CODE_FONT} code style in {STYLES}")
                data = patch_styles(xml).encode("utf-8")
            zout.writestr(item, data)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
