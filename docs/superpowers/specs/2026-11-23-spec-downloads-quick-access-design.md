# Spec downloads, Quick access box and logo-colored theme — design

Status: approved 2026-11-23

## Intent

Make the mzTab-M 2.1 specification downloadable as PDF (and DOCX) alongside
the Antora HTML site, link the downloads from a "Quick access" box on the
Documentation Hub, *mzTab-M for Users* and *mzTab-M for Developers* pages, and
offer alternative, more colorful stylings derived from the mzTab-M logo on top
of the vendored antora-dark-theme.

## Goals

- PDF and DOCX of the specification are published with the site, per version.
- One reusable Quick access box, shown on the three landing pages.
- The PDF is complete (no truncated table cells) and branded.
- The online spec page shows all figures.
- Three switchable color variants, compared via screenshots.

## Non-goals

- Rewriting the specification content.
- Replacing antora-ui-default / antora-dark-theme.

## Approaches considered (downloads)

1. **Antora attachments (chosen).** CI writes the generated PDF/DOCX into
   `docs/mztabm/modules/ROOT/attachments/` before running Antora; links use
   `xref:ROOT:attachment$…`. Versioned automatically; the release job commits
   the files into the `vX.Y` doc branch so released versions keep their files.
   Generated files are git-ignored on `main`.
2. Copy files into `build/site/downloads/` after Antora. Simple, but not
   versioned and links are hard-coded.
3. Link to GitHub release assets. Only works for releases, not dev builds.

## Design

- **Build (`build-docs.sh`)**: correct exit-code handling, a custom
  asciidoctor-pdf theme using the logo palette with the logo on the title page,
  and a fix for table cells that exceed one page.
- **CI**: `build-docs` job downloads the `specification-documents` artifact
  into the attachments folder; release `publish-site` does the same; release
  `create-doc-branch` force-adds the files into the version branch.
  `build-site.sh` gains `--with-spec` to build them locally.
- **Quick access box**: `ROOT/partials/quick-access.adoc`, included from the
  three landing pages, styled by `.quick-access` in supplemental CSS.
- **Fixes**: sync spec figures into the developers module images; fix
  unterminated listing blocks in the generated schema / changes AsciiDoc.
- **Theme**: logo palette as CSS custom properties in
  `site-mztabm-theme.css`; variants `accent`, `sections`, `branded` selected by
  a `data-mztab-theme` attribute on `<html>`; screenshots of all three were
  published for comparison.
  **Decision (2026-11-23):** default is `branded` combined with the
  section-coded MTD/SML/SMF/SME chips. The PDF title page uses a single band
  in the header blue (`#2f4256`) at top and bottom instead of the four bands.
  **Decision (2026-11-23):** PDF and DOCX body text and headings are
  sans-serif (PDF: Noto Sans, bundled with asciidoctor-pdf; DOCX: Calibri via
  `specification_documents/docx-theme/reference.docx`); only code, verbatim
  text and inline keywords use a monospace font (PDF: M+ 1mn; DOCX: Consolas).
  **Decision (2026-11-23):** the DOCX matches the PDF: same title page (logo,
  single header-blue band at top and bottom), A4, chapters on new pages,
  section/figure/table numbers and cross-reference text taken from
  Asciidoctor (`docx-theme/docbook-numbering.rb`), and a pre-filled table of
  contents without the "dirty" field flag so Word opens it without asking to
  update fields (`docx-theme/postprocess_docx.py`). Tables follow the PDF
  theme: `#c5d0dc` grid, header row shaded `#e6edf4` with `#2f4256` text,
  8.5pt cell text and 8pt code; code blocks get a light background.

## Logo palette

| Section | Dark      | Light tint |
|---------|-----------|------------|
| MTD     | `#4d657f` | `#9eb5d0`  |
| SML     | `#517e4e` | `#a2c79e`  |
| SMF     | `#a57b27` | `#e5c380`  |
| SME     | `#a44a28` | `#e39c82`  |

## Left to the builder

Exact link list in the box, shade derivations for dark mode contrast, PDF
theme details.
