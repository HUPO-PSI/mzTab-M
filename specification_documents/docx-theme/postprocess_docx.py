#!/usr/bin/env python3
"""Finish the pandoc DOCX of the mzTab-M specification so it matches the PDF.

- Title page: mzTab-M logo above the title and a header-blue band at the top
  and bottom of the page (first-page header/footer), as on the PDF title page.
- Page setup: A4 with the PDF margins; footer "mzTab-M <version>" and the page
  number on all other pages.
- Table of contents: pandoc writes an empty TOC field marked "dirty", which
  makes Word ask on opening whether to update fields that "may refer to other
  files". The field is filled with hyperlinked entries for the headings and
  the dirty flag removed, so the document opens without that prompt. Word can
  still add page numbers with "Update Field" (F9) on the table of contents.

Usage:
    postprocess_docx.py <in.docx> <out.docx> --logo <logo.png> --version <text>
"""
import argparse
import re
import struct
import zipfile
import zlib
from html import escape

HEADER_BLUE = (0x2F, 0x42, 0x56)
MUTED = "5A6B7D"
RULE = "9EB5D0"

EMU_PER_CM = 360000
TWIPS_PER_CM = 567
PAGE_W_CM, PAGE_H_CM = 21.0, 29.7
MARGIN_TB_CM, MARGIN_LR_CM = 2.0, 1.8
BAND_CM = 24 / 72 * 2.54          # 24pt, as in pdf-theme/title-band.svg
LOGO_W_CM = 0.30 * (PAGE_W_CM - 2 * MARGIN_LR_CM)   # pdfwidth=30%
LOGO_TOP_CM = 0.18 * PAGE_H_CM     # logo top at 18% of the page
TITLE_TOP_CM = 0.52 * PAGE_H_CM    # title at 52% of the page

REL_LOGO, REL_BAND = "rIdMzLogo", "rIdMzBand"
REL_HDR_FIRST, REL_FTR_FIRST, REL_FTR_DEFAULT = "rIdMzHdrFirst", "rIdMzFtrFirst", "rIdMzFtrDefault"
LOGO_PART, BAND_PART = "media/mztabm-logo.png", "media/mztabm-band.png"
HDR_FIRST_PART, FTR_FIRST_PART, FTR_DEFAULT_PART = "header-mztabm-first.xml", "footer-mztabm-first.xml", "footer-mztabm.xml"

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_HEADER = "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"
CT_FOOTER = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"


def emu(cm: float) -> int:
    return round(cm * EMU_PER_CM)


def twips(cm: float) -> int:
    return round(cm * TWIPS_PER_CM)


def solid_png(rgb, size: int = 8) -> bytes:
    """A small single-color PNG (stretched to form the title page bands)."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(rgb) * size for _ in range(size))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def png_size(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("logo must be a PNG file")
    return struct.unpack(">II", data[16:24])


def _picture(rel_id: str, name: str, doc_pr_id: int, cx: int, cy: int) -> str:
    return (f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{doc_pr_id}" name="{name}" /><pic:cNvPicPr /></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rel_id}" /><a:stretch><a:fillRect /></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0" /><a:ext cx="{cx}" cy="{cy}" /></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst /></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>')


def logo_paragraph(width_px: int, height_px: int, doc_pr_id: int) -> str:
    cx = emu(LOGO_W_CM)
    cy = round(cx * height_px / width_px)
    before = twips(LOGO_TOP_CM - MARGIN_TB_CM)
    return (f'<w:p><w:pPr><w:spacing w:before="{before}" w:after="0" /><w:jc w:val="center" /></w:pPr>'
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}" /><wp:docPr id="{doc_pr_id}" name="mzTab-M logo" />'
            f'<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1" /></wp:cNvGraphicFramePr>'
            f'{_picture(REL_LOGO, "mzTab-M logo", doc_pr_id, cx, cy)}</wp:inline></w:drawing></w:r></w:p>')


def band_paragraph(top_cm: float, doc_pr_id: int) -> str:
    """A full-width band anchored to the page (behind text), for header/footer."""
    cx, cy = emu(PAGE_W_CM), emu(BAND_CM)
    return (f'<w:p><w:pPr><w:spacing w:before="0" w:after="0" /></w:pPr><w:r><w:drawing>'
            f'<wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0" '
            f'behindDoc="1" locked="1" layoutInCell="1" allowOverlap="1"><wp:simplePos x="0" y="0" />'
            f'<wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionH>'
            f'<wp:positionV relativeFrom="page"><wp:posOffset>{emu(top_cm)}</wp:posOffset></wp:positionV>'
            f'<wp:extent cx="{cx}" cy="{cy}" /><wp:effectExtent l="0" t="0" r="0" b="0" /><wp:wrapNone />'
            f'<wp:docPr id="{doc_pr_id}" name="Title page band" /><wp:cNvGraphicFramePr />'
            f'{_picture(REL_BAND, "Title page band", doc_pr_id, cx, cy)}</wp:anchor></w:drawing></w:r></w:p>')


def header_footer_xml(root: str, body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:{root} {NS}>{body}</w:{root}>'


def footer_paragraph(version: str) -> str:
    right = twips(PAGE_W_CM - 2 * MARGIN_LR_CM)
    rpr = f'<w:rPr><w:color w:val="{MUTED}" /><w:sz w:val="16" /><w:szCs w:val="16" /></w:rPr>'
    return (f'<w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="4" w:color="{RULE}" /></w:pBdr>'
            f'<w:tabs><w:tab w:val="right" w:pos="{right}" /></w:tabs><w:spacing w:before="0" w:after="0" /></w:pPr>'
            f'<w:r>{rpr}<w:t xml:space="preserve">mzTab-M {escape(version, quote=False)}</w:t></w:r>'
            f'<w:r>{rpr}<w:tab /></w:r><w:fldSimple w:instr=" PAGE "><w:r>{rpr}<w:t>1</w:t></w:r></w:fldSimple></w:p>')


def section_properties() -> str:
    return (f'<w:sectPr><w:headerReference w:type="first" r:id="{REL_HDR_FIRST}" />'
            f'<w:footerReference w:type="default" r:id="{REL_FTR_DEFAULT}" />'
            f'<w:footerReference w:type="first" r:id="{REL_FTR_FIRST}" />'
            f'<w:pgSz w:w="{twips(PAGE_W_CM)}" w:h="{twips(PAGE_H_CM)}" />'
            f'<w:pgMar w:top="{twips(MARGIN_TB_CM)}" w:right="{twips(MARGIN_LR_CM)}" '
            f'w:bottom="{twips(MARGIN_TB_CM)}" w:left="{twips(MARGIN_LR_CM)}" '
            f'w:header="567" w:footer="567" w:gutter="0" /><w:titlePg /></w:sectPr>')


_SECTPR_RE = re.compile(r"<w:sectPr\s*/>|<w:sectPr\b.*?</w:sectPr>", re.S)
_TITLE_RE = re.compile(r'<w:p>\s*<w:pPr>\s*<w:pStyle w:val="Title"\s*/>')
_HEADING_RE = re.compile(
    r'(?:<w:bookmarkStart w:id="\d+" w:name="(?P<bm>[^"]+)"\s*/>\s*)?'
    r'<w:p>\s*<w:pPr>\s*<w:pStyle w:val="Heading(?P<lvl>[1-9])"\s*/>(?P<body>.*?)</w:p>', re.S)
_TOC_FIELD_RE = re.compile(
    r'<w:p>\s*<w:r>\s*<w:fldChar w:fldCharType="begin"[^>]*/>\s*'
    r'<w:instrText[^>]*>(?P<instr>\s*TOC\b[^<]*)</w:instrText>\s*'
    r'<w:fldChar w:fldCharType="separate"\s*/>\s*<w:fldChar w:fldCharType="end"\s*/>\s*</w:r>\s*</w:p>', re.S)
_TOC_LEVELS_RE = re.compile(r'\\o\s*&quot;(\d)-(\d)&quot;|\\o\s*"(\d)-(\d)"')


def toc_entries(document: str, max_level: int):
    """(level, bookmark or None, escaped text) for each heading up to max_level."""
    entries = []
    for m in _HEADING_RE.finditer(document):
        level = int(m.group("lvl"))
        if level > max_level:
            continue
        text = "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", m.group("body"))).strip()
        bookmark = m.group("bm")
        if not bookmark:  # some pandoc versions put the bookmark inside the paragraph
            inner = re.search(r'<w:bookmarkStart w:id="\d+" w:name="([^"]+)"', m.group("body"))
            bookmark = inner.group(1) if inner else None
        if text:
            entries.append((level, bookmark, text))
    return entries


def fill_toc(document: str) -> str:
    """Replace pandoc's empty, dirty TOC field with a filled, clean one."""
    field = _TOC_FIELD_RE.search(document)
    if not field:
        return document.replace(' w:dirty="true"', "")
    instr = field.group("instr")
    levels = _TOC_LEVELS_RE.search(instr)
    max_level = int(next(g for g in levels.groups()[1::2] if g)) if levels else 3
    entries = toc_entries(document, max_level)
    if not entries:
        return document.replace(' w:dirty="true"', "")
    paragraphs = []
    for i, (level, bookmark, text) in enumerate(entries):
        parts = [f'<w:p><w:pPr><w:pStyle w:val="TOC{min(level, 3)}" /></w:pPr>']
        if i == 0:
            parts.append(f'<w:r><w:fldChar w:fldCharType="begin" /></w:r>'
                         f'<w:r><w:instrText xml:space="preserve">{instr}</w:instrText></w:r>'
                         f'<w:r><w:fldChar w:fldCharType="separate" /></w:r>')
        run = f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'
        parts.append(f'<w:hyperlink w:anchor="{bookmark}" w:history="1">{run}</w:hyperlink>' if bookmark else run)
        if i == len(entries) - 1:
            parts.append('<w:r><w:fldChar w:fldCharType="end" /></w:r>')
        parts.append("</w:p>")
        paragraphs.append("".join(parts))
    return document[: field.start()] + "".join(paragraphs) + document[field.end():]


def add_title_page(document: str, logo_size, doc_pr_id: int) -> str:
    title = _TITLE_RE.search(document)
    if not title:
        raise SystemExit("no Title paragraph in the DOCX")
    logo = logo_paragraph(*logo_size, doc_pr_id)
    logo_h_cm = LOGO_W_CM * logo_size[1] / logo_size[0]
    title_before = max(0, twips(TITLE_TOP_CM - LOGO_TOP_CM - logo_h_cm))
    title_ppr = f'<w:p><w:pPr><w:pStyle w:val="Title" /><w:spacing w:before="{title_before}" />'
    return (document[: title.start()] + logo + title_ppr + document[title.end():])


def set_section(document: str) -> str:
    sections = list(_SECTPR_RE.finditer(document))
    if sections:
        last = sections[-1]
        return document[: last.start()] + section_properties() + document[last.end():]
    return document.replace("</w:body>", section_properties() + "</w:body>")


def add_relationships(rels: str) -> str:
    new = (f'<Relationship Id="{REL_LOGO}" Type="{REL_NS}/image" Target="{LOGO_PART}" />'
           f'<Relationship Id="{REL_HDR_FIRST}" Type="{REL_NS}/header" Target="{HDR_FIRST_PART}" />'
           f'<Relationship Id="{REL_FTR_FIRST}" Type="{REL_NS}/footer" Target="{FTR_FIRST_PART}" />'
           f'<Relationship Id="{REL_FTR_DEFAULT}" Type="{REL_NS}/footer" Target="{FTR_DEFAULT_PART}" />')
    return rels.replace("</Relationships>", new + "</Relationships>")


def band_rels() -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="{REL_BAND}" Type="{REL_NS}/image" Target="{BAND_PART}" /></Relationships>')


def add_content_types(types: str) -> str:
    add = ""
    if not re.search(r'<Default Extension="png"', types, re.I):
        add += '<Default Extension="png" ContentType="image/png" />'
    for part, ctype in ((HDR_FIRST_PART, CT_HEADER), (FTR_FIRST_PART, CT_FOOTER), (FTR_DEFAULT_PART, CT_FOOTER)):
        add += f'<Override PartName="/word/{part}" ContentType="{ctype}" />'
    return types.replace("</Types>", add + "</Types>")


def next_doc_pr_id(document: str) -> int:
    ids = [int(i) for i in re.findall(r'<wp:docPr id="(\d+)"', document)]
    return max(ids, default=0) + 1


def postprocess(src: str, dst: str, logo_path: str, version: str) -> None:
    with open(logo_path, "rb") as fh:
        logo = fh.read()
    logo_size = png_size(logo)
    with zipfile.ZipFile(src) as zin:
        items = [(info, zin.read(info.filename)) for info in zin.infolist()]
    names = {info.filename for info, _ in items}
    if "word/document.xml" not in names:
        raise SystemExit(f"{src} is not a Word document")
    pr_id = 0
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in items:
            if info.filename == "word/document.xml":
                xml = data.decode("utf-8")
                pr_id = next_doc_pr_id(xml)
                xml = add_title_page(xml, logo_size, pr_id)
                xml = fill_toc(xml)
                xml = set_section(xml)
                data = xml.encode("utf-8")
            elif info.filename == "word/_rels/document.xml.rels":
                data = add_relationships(data.decode("utf-8")).encode("utf-8")
            elif info.filename == "[Content_Types].xml":
                data = add_content_types(data.decode("utf-8")).encode("utf-8")
            elif info.filename == "word/settings.xml":
                data = re.sub(rb"<w:updateFields[^>]*/>", b"", data)
            zout.writestr(info, data)
        pr_base = pr_id  # unique drawing ids: logo = pr_id, bands = pr_id + 1, + 2
        zout.writestr(f"word/{LOGO_PART}", logo)
        zout.writestr(f"word/{BAND_PART}", solid_png(HEADER_BLUE))
        zout.writestr(f"word/{HDR_FIRST_PART}", header_footer_xml("hdr", band_paragraph(0, pr_base + 1)))
        zout.writestr(f"word/{FTR_FIRST_PART}",
                      header_footer_xml("ftr", band_paragraph(PAGE_H_CM - BAND_CM, pr_base + 2)))
        zout.writestr(f"word/{FTR_DEFAULT_PART}", header_footer_xml("ftr", footer_paragraph(version)))
        zout.writestr(f"word/_rels/{HDR_FIRST_PART}.rels", band_rels())
        zout.writestr(f"word/_rels/{FTR_FIRST_PART}.rels", band_rels())


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("--logo", required=True, help="PNG logo for the title page")
    parser.add_argument("--version", required=True, help="document version for the footer")
    args = parser.parse_args(argv)
    postprocess(args.src, args.dst, args.logo, args.version)


if __name__ == "__main__":
    main()
