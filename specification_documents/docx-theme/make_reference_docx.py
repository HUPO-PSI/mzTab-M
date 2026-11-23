#!/usr/bin/env python3
"""Create the pandoc reference.docx used for the DOCX specification.

Starts from pandoc's built-in reference.docx and pins the Word theme fonts so
body text and headings are sans-serif, independent of the pandoc version
(older pandoc releases default to the serif Cambria for body text). Code and
verbatim text use pandoc's "Source Code" / "Verbatim Char" styles, which stay
in the monospace Consolas.

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

THEME = "word/theme/theme1.xml"
STYLES = "word/styles.xml"


def set_theme_font(xml: str, which: str, typeface: str) -> str:
    pattern = re.compile(r'(<a:%s>\s*<a:latin typeface=")[^"]*(")' % which)
    xml, n = pattern.subn(r"\g<1>%s\g<2>" % typeface, xml)
    if n != 1:
        raise SystemExit(f"could not find <a:{which}> latin font in {THEME}")
    return xml


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
            zout.writestr(item, data)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
