# Spec downloads, Quick access box and logo theme — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the spec as PDF/DOCX with the Antora site, link it from a Quick access box on three landing pages, fix build defects, and offer three logo-colored theme variants.

**Architecture:** Generated PDF/DOCX become Antora attachments of the `ROOT` module (git-ignored on `main`, committed on `vX.Y` doc branches). A shared AsciiDoc partial renders the Quick access box. Theme colors live in one supplemental CSS file keyed by `html[data-mztab-theme]`.

**Tech Stack:** Antora 3, antora-ui-default + vendored antora-dark-theme, asciidoctor / asciidoctor-pdf (Docker), pandoc, Python 3 (stdlib `unittest`), GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-23-spec-downloads-quick-access-design.md`

## Global Constraints

- Logo palette: MTD `#4d657f`/`#9eb5d0`, SML `#517e4e`/`#a2c79e`, SMF `#a57b27`/`#e5c380`, SME `#a44a28`/`#e39c82`.
- Attachment file names: `mzTab_format_specification_2_1-M.pdf`, `mzTab_format_specification_2_1-M.docx` in `docs/mztabm/modules/ROOT/attachments/`.
- Theme variants: `accent`, `sections`, `branded`; default chosen in `head-meta.hbs`.
- No new runtime dependencies for the site; Python tests use stdlib only.

## Review Focus

- Local `./build-site.sh` without generated attachments must still build (links render, Antora warns but does not fail).
- PR builds (not only pushes to `main`) must show the download links working.
- Released `vX.Y` versions must link to their own PDF, not the dev one.
- Dark mode and light mode both readable (WCAG AA for link/text colors) in every variant.
- Regenerating partials via `./gen-docs.sh` must not reintroduce the listing-block bug.

---

### Task 1: Generator fixes (schema + comparison AsciiDoc)

**Files:** Modify `schema/generate_schema_adoc.py`, `compare_adoc_specs.py`; Create `tests/test_doc_generators.py`; regenerate partials via `./gen-docs.sh`.

- [ ] Tests: `test_type_regex_cell_has_blank_line_before_listing` (line after `|*Type* a|Regex` is empty), `test_html_anchor_converted` (`<a href='U'>T</a>` → `U[T]`), `test_adoc_cell_strips_delimiters` (no `----`/`....` lines), `test_adoc_cell_escapes_attribute_refs` (`{4}` → `\{4}`, `{vbar}` kept), `test_summary_uses_first_paragraph`.
- [ ] Implement; run `python3 -m unittest discover -s tests`.
- [ ] `./gen-docs.sh`; asciidoctor build reports no "unterminated listing block".

### Task 2: Figures on the online spec page

**Files:** Modify `gen-docs.sh`; add `docs/mztabm/modules/developers/images/img/media/*` (copied from `specification_documents/img/media/`).

- [ ] gen-docs.sh `--spec` copies figures; Antora build has no "target of image not found".

### Task 3: PDF theme and build script

**Files:** Create `specification_documents/pdf-theme/mztabm-theme.yml`; Modify `build-docs.sh`, `specification_documents/mzTab_format_specification_2_1-M.adoc` (title-logo / theme attributes, PDF-only).

- [ ] PDF build shows 0 "table cell … truncated" errors; title page shows logo; pandoc exit code checked.

### Task 4: Attachments pipeline

**Files:** Modify `.gitignore`, `build-site.sh` (`--with-spec`), `.github/workflows/ci.yml`, `.github/workflows/release.yml`.

- [ ] `./build-site.sh --with-spec` produces `build/site/mztabm/2.1/_attachments/*.pdf|docx`.

### Task 5: Quick access box

**Files:** Create `docs/mztabm/modules/ROOT/partials/quick-access.adoc`; Modify the three `index.adoc` landing pages; styles in `docs/supplemental-ui/css/site-mztabm-theme.css`.

- [ ] Box present on the three pages; links resolve.

### Task 6: Theme variants and comparison

**Files:** Create `docs/supplemental-ui/css/site-mztabm-theme.css`; Modify `docs/supplemental-ui/partials/head-meta.hbs`.

- [ ] Screenshots of each variant (light + dark) published as a comparison page.
