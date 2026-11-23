"""Tests for specification_documents/docx-theme/postprocess_docx.py.

Run from the repository root:
    python3 -m unittest discover -s tests
"""
import importlib.util
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.dom import minidom

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "specification_documents" / "docx-theme"
LOGO = ROOT / "specification_documents" / "pdf-theme" / "mzTab-M-logo.png"

spec = importlib.util.spec_from_file_location("postprocess_docx", THEME / "postprocess_docx.py")
pp = importlib.util.module_from_spec(spec)
sys.modules["postprocess_docx"] = pp
spec.loader.exec_module(pp)

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'

# Shape of pandoc's output: title block, dirty TOC field, bookmarked headings.
DOCUMENT = f"""<?xml version="1.0" encoding="UTF-8"?><w:document {W}><w:body>
<w:p><w:pPr><w:pStyle w:val="Title" /></w:pPr><w:r><w:t xml:space="preserve">mzTab-M</w:t></w:r></w:p>
<w:sdt><w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents" /><w:docPartUnique /></w:docPartObj></w:sdtPr><w:sdtContent>
<w:p><w:pPr><w:pStyle w:val="TOCHeading" /></w:pPr><w:r><w:t xml:space="preserve">Table of Contents</w:t></w:r></w:p>
<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true" /><w:instrText xml:space="preserve">TOC \\o &quot;1-2&quot; \\h \\z \\u</w:instrText><w:fldChar w:fldCharType="separate" /><w:fldChar w:fldCharType="end" /></w:r></w:p>
</w:sdtContent></w:sdt>
<w:bookmarkStart w:id="1" w:name="introduction" /><w:p><w:pPr><w:pStyle w:val="Heading1" /></w:pPr><w:r><w:t xml:space="preserve">1. Introduction</w:t></w:r></w:p>
<w:bookmarkStart w:id="2" w:name="background" /><w:p><w:pPr><w:pStyle w:val="Heading2" /></w:pPr><w:r><w:t xml:space="preserve">1.1. Back &amp; ground</w:t></w:r></w:p>
<w:bookmarkStart w:id="3" w:name="deep" /><w:p><w:pPr><w:pStyle w:val="Heading3" /></w:pPr><w:r><w:t xml:space="preserve">1.1.1. Too deep</w:t></w:r></w:p>
<w:bookmarkEnd w:id="3" /><w:bookmarkEnd w:id="2" /><w:bookmarkEnd w:id="1" /><w:sectPr /></w:body></w:document>"""
RELS = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
TYPES = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'
SETTINGS = f'<?xml version="1.0" encoding="UTF-8"?><w:settings {W}><w:updateFields w:val="true" /></w:settings>'


class PostprocessDocxTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        src, dst = Path(cls.tmp.name, "in.docx"), Path(cls.tmp.name, "out.docx")
        with zipfile.ZipFile(src, "w") as z:
            z.writestr("[Content_Types].xml", TYPES)
            z.writestr("word/document.xml", DOCUMENT)
            z.writestr("word/_rels/document.xml.rels", RELS)
            z.writestr("word/settings.xml", SETTINGS)
        pp.main([str(src), str(dst), "--logo", str(LOGO), "--version", "2.1.0 <dev>"])
        with zipfile.ZipFile(dst) as z:
            cls.parts = {n: z.read(n) for n in z.namelist()}
        cls.doc = cls.parts["word/document.xml"].decode()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_xml_parts_are_well_formed(self):
        for name, data in self.parts.items():
            if name.endswith((".xml", ".rels")):
                minidom.parseString(data)

    def test_toc_is_not_dirty_and_update_fields_removed(self):
        self.assertNotIn("w:dirty", self.doc)
        self.assertNotIn(b"updateFields", self.parts["word/settings.xml"])

    def test_toc_lists_headings_up_to_field_depth_with_links(self):
        entries = re.findall(r'<w:pStyle w:val="(TOC\d)" />.*?<w:hyperlink w:anchor="([^"]+)"', self.doc)
        self.assertEqual(entries, [("TOC1", "introduction"), ("TOC2", "background")])
        self.assertIn("1.1. Back &amp; ground", self.doc)
        self.assertEqual(self.doc.count('w:fldCharType="begin"'), 1)
        self.assertEqual(self.doc.count('w:fldCharType="end"'), 1)

    def test_title_page_has_logo_before_title(self):
        self.assertLess(self.doc.index('r:embed="rIdMzLogo"'), self.doc.index('w:val="Title"'))
        self.assertIn(b"word/media/mztabm-logo.png", b" ".join(n.encode() for n in self.parts))

    def test_section_is_a4_with_title_page_header_and_footer(self):
        sect = re.search(r"<w:sectPr>.*?</w:sectPr>", self.doc).group(0)
        self.assertIn('<w:pgSz w:w="11907" w:h="16840" />', sect)
        self.assertIn("<w:titlePg />", sect)
        rels = self.parts["word/_rels/document.xml.rels"].decode()
        for part in ("header-mztabm-first.xml", "footer-mztabm-first.xml", "footer-mztabm.xml"):
            self.assertIn(f'Target="{part}"', rels)
            self.assertIn(f"/word/{part}", self.parts["[Content_Types].xml"].decode())

    def test_footer_escapes_version(self):
        footer = self.parts["word/footer-mztabm.xml"].decode()
        self.assertIn("mzTab-M 2.1.0 &lt;dev&gt;", footer)
        self.assertIn('w:instr=" PAGE "', footer)

    def test_band_png_is_valid(self):
        self.assertEqual(pp.png_size(self.parts["word/media/mztabm-band.png"]), (8, 8))


class StyleTablesTest(unittest.TestCase):
    TABLE = ('<w:p><w:pPr><w:pStyle w:val="BodyText" /></w:pPr><w:r><w:t>outside</w:t></w:r></w:p>'
             '<w:tbl><w:tblPr><w:tblStyle w:val="Table" /></w:tblPr>'
             '<w:tr><w:trPr><w:tblHeader w:val="on" /></w:trPr><w:tc><w:tcPr />'
             '<w:p><w:pPr><w:pStyle w:val="Compact" /></w:pPr><w:r><w:t>Head</w:t></w:r></w:p></w:tc></w:tr>'
             '<w:tr><w:tc><w:tcPr /><w:p><w:pPr><w:pStyle w:val="FirstParagraph" /></w:pPr>'
             '<w:r><w:rPr><w:rStyle w:val="VerbatimChar" /></w:rPr><w:t>code</w:t></w:r></w:p>'
             '<w:p><w:pPr><w:pStyle w:val="SourceCode" /></w:pPr><w:r><w:t>MTD</w:t></w:r></w:p>'
             '<w:p><w:r><w:t>bare</w:t></w:r></w:p></w:tc></w:tr></w:tbl>')

    def setUp(self):
        self.out = pp.style_tables(self.TABLE)

    def test_text_outside_tables_is_untouched(self):
        self.assertTrue(self.out.startswith('<w:p><w:pPr><w:pStyle w:val="BodyText" />'))

    def test_header_row_is_shaded_heading(self):
        header = re.search(r"<w:tr><w:trPr>.*?</w:tr>", self.out).group(0)
        self.assertIn('w:val="TableHeading"', header)
        self.assertIn('w:fill="E6EDF4"', header)

    def test_body_cells_use_table_styles(self):
        body = self.out.split("</w:tr>", 1)[1]
        self.assertEqual(body.count('w:val="TableText"'), 2)
        self.assertIn('w:val="TableSourceCode"', body)
        self.assertIn('w:val="TableVerbatimChar"', body)
        self.assertNotIn('"VerbatimChar"', body)
        self.assertNotIn("<w:shd", body)


if __name__ == "__main__":
    unittest.main()
