"""Regression tests for the AsciiDoc generators used by gen-docs.sh.

Run from the repository root:
    python3 -m unittest discover -s tests
"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gsa = _load("generate_schema_adoc", ROOT / "schema" / "generate_schema_adoc.py")
cas = _load("compare_adoc_specs", ROOT / "compare_adoc_specs.py")


class SchemaGeneratorTest(unittest.TestCase):
    def _entry(self, prop: dict) -> list:
        lines: list = []
        gsa.write_field_entry(lines, "mzTab-version", prop, "MTD", {})
        return lines

    def test_type_regex_cell_has_blank_line_before_listing(self):
        # "Regex" directly above "----" is parsed by Asciidoctor as a two-line
        # section title, leaving the following listing block unterminated.
        lines = self._entry({"anyOf": [{"type": "string", "pattern": r"^\d$"}]})
        idx = next(i for i, l in enumerate(lines) if l.startswith("|*Type* a|"))
        self.assertEqual(lines[idx + 1], "")
        self.assertEqual(lines[idx + 2], "----")

    def test_html_anchor_converted(self):
        desc = gsa.get_description(
            {"description": "see <a href='http://dx.doi.org/10.1351/X'>terms relating to MS</a> e.g."}
        )
        self.assertNotIn("<a", desc)
        self.assertIn("http://dx.doi.org/10.1351/X[terms relating to MS]", desc)

    def test_html_anchor_double_quotes(self):
        desc = gsa.get_description({"description": 'x <a href="https://e.org/a">A</a>'})
        self.assertEqual(desc, "x https://e.org/a[A]")


class CompareScriptTest(unittest.TestCase):
    def test_adoc_cell_strips_delimiters(self):
        cell = cas._adoc_cell("Regex\n----\n^[0-9]$\n----")
        self.assertNotIn("----", cell)
        self.assertIn("Regex", cell)

    def test_adoc_example_block_strips_inner_delimiters(self):
        block = cas._adoc_example_block("----\nMTD\tmzTab-version\t2.1.0-M\n----")
        self.assertEqual(block.splitlines()[1:-1], ["MTD\tmzTab-version\t2.1.0-M"])

    def test_adoc_example_block_escapes_pipes_for_table_cell(self):
        # Literal blocks do not substitute {vbar}; escape the cell separator.
        block = cas._adoc_example_block(r"MTD	publication[1]	pubmed:1\|doi:2")
        self.assertIn(r"pubmed:1\|doi:2", block)
        self.assertNotIn("vbar", block)

    def test_adoc_cell_escapes_attribute_refs(self):
        cell = cas._adoc_cell("^[0-9]{4}-[0-9]{4}$ and a|b")
        self.assertIn(r"\{4}", cell)
        self.assertIn("{vbar}", cell)
        self.assertNotIn(r"\{vbar}", cell)

    def test_adoc_cell_already_escaped_pipe(self):
        # Source text "A \| separated" must not become "\{vbar}" (literal text).
        self.assertEqual(cas._adoc_cell(r"A \| separated"), "A {vbar} separated")

    def test_summary_description_uses_first_paragraph(self):
        text = "First paragraph line one.\nline two.\n\nSecond paragraph."
        self.assertEqual(cas._first_paragraph(text), "First paragraph line one.\nline two.")


if __name__ == "__main__":
    unittest.main()
