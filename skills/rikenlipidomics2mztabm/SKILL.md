---
name: rikenlipidomics2mztabm
description: Convert a pair of RIKEN-LIPIDOMICS-style MSDIAL alignment TSV files (a *_forMTD.tsv per-sample metadata table plus a *_forSMLSMF.tsv alignment export, layout used in https://github.com/kozo2/hupopsi-pymztabm-handson/tree/main/RIKEN_LIPIDOMICS) into a valid mzTab-M 2.0.0-M file using the `pymztab-m` Python package, where success means the in-memory `MzTabM.validate(...)` reports zero ERROR-level messages. Use this skill whenever the user has MSDIAL alignment TSVs (or anything called "RIKEN lipidomics", "forMTD/forSMLSMF", "MS-DIAL export", "alignment_results.tsv") and wants to convert, export, share, archive, or upload it as mzTab-M / "the standard metabolomics format" / "mzTab" — even if they don't say "mzTab-M" explicitly. Also trigger when the user wants to check that an existing mzTab-M file passes the pymzTab-m validator, or asks for help wiring metadata + SML/SMF/SME sections together.
metadata:
  author: Kozo Nishida
  version: "1.0"
---

# rikenlipidomics2mztabm

Convert the two-TSV RIKEN_LIPIDOMICS export from MSDIAL alignment into an mzTab-M 2.0.0-M file that passes the `pymztab-m` package's in-memory validator with **zero ERROR-level messages**. WARNING-level messages (e.g. unreferenced `study_variable`, recommended-but-missing `best_id_confidence_value`) are tolerated — only ERRORs count as failure.

## What the inputs look like

The RIKEN_LIPIDOMICS handson repo splits the dataset into two TSV files per study:

`<study>_forMTD.tsv` — 9 rows describing each sample column:

| Row index | Column 0 label | Columns 1.. |
|---|---|---|
| 0 | (empty)             | sample names (one per ms_run) |
| 1 | Public/Private      | per-sample value |
| 2 | Category            | Mouse / Human / Blank |
| 3 | Tissue/Species      | e.g. "Adrenal gland" |
| 4 | Genotype/Background | e.g. "C57BL/6J", "B6-fads2/J" |
| 5 | Perturbation        | per-sample value |
| 6 | Diet/Culture        | per-sample value |
| 7 | Biological replicate| 1, 2, 3, ... |
| 8 | Technical replicate | 1, 2, 3, ... |
| 9 | Unit                | e.g. "Height" |

`<study>_forSMLSMF.tsv` — the MSDIAL alignment export. Row 0 is the column header. The first ~31 columns are identification fields (`Alignment ID`, `Average Rt(min)`, `Average Mz`, `Metabolite name`, `Adduct type`, `Formula`, `SMILES`, `INCHIKEY`, `Total score`, `Spectrum reference file name`, ...); the remaining columns are one per sample, named to match the sample-name row in the MTD TSV.

## How to use this skill

A bundled converter script does the heavy lifting — call it once per study (one MTD + one SMLSMF pair). **Do not** hand-author mzTab-M TSV: required-field checks are easy to miss on the SMF/SME sections, and the `pymztab-m` model classes already encode every constraint, so building through the model is the safest path to a 0-error file.

### Step 1 — Confirm the Python environment

The skill ships with a `uv`-managed virtualenv under `<skill-dir>/.venv` whose only runtime dependency is `pymztab-m` (installed editable from a local checkout of the package's `development` branch). From the skill directory:

```bash
cd /Users/knishida/skills/rikenlipidomics2mztabm
/Users/knishida/.local/bin/uv sync   # idempotent; no-op when nothing changed
```

If the pymzTab-m checkout has moved on this host, edit the `tool.uv.sources.pymztabm.path` in `pyproject.toml` to point at the new location and re-run `uv sync`.

### Step 2 — Gather user-supplied metadata (optional)

The TSVs themselves carry no study-level metadata (mzTab-ID, instrument CV terms, ms_run file locations, contacts, publication, software version, scan polarity, ...). Ask the user — or pull from prior conversation context — for any of the following. Anything they don't supply falls back to a reasonable default in `DEFAULT_METADATA`; the file will still validate, but the metadata won't be informative.

Useful fields (everything is optional; defaults exist for all):

- `mztab_id` — study identifier (e.g. `RIKEN-LIPIDOMICS-001`, `MTBLS123`)
- `title`, `description`
- `contact[]` — list of `{name, affiliation, email, orcid}`. **Email deliverability is checked**: only supply addresses with a real MX record. Leave the field out rather than supply a placeholder.
- `publication[]` — each entry is a list of `"type:accession"` strings (e.g. `["pubmed:12345678", "doi:10.1234/abc"]`). Strings are split on the first `:`.
- `instrument[]` — `{name, source, analyzer[], detector}` where each value is a `{cv_label, cv_accession, name}` PSI-MS CV-term dict (e.g. `MS:1002416 = Q Exactive HF`).
- `software[]` — list of CV-term dicts (e.g. `MS:1003082 = MS-DIAL`).
- `ms_run_format`, `ms_run_id_format`, `ms_run_scan_polarity[]` — CV-term dicts; defaults are mzML / mzML unique identifier / positive scan.
- `ms_run_location_template` — Python format string with `{name}` for the sample column header (default `file:///data/{name}.mzML`).
- `database[]` — `{param: <CV-dict>, prefix, version, uri}` (default LIPID MAPS).
- `quantification_method`, `small_molecule_quantification_unit`, `small_molecule_feature_quantification_unit`, `small_molecule_identification_reliability` — CV-term dicts.
- `id_confidence_measure[]` — list of CV-term dicts.

Save what you collected to a JSON file. See `scripts/example_metadata.json` for a populated reference.

### Step 3 — Run the converter

```bash
cd /Users/knishida/skills/rikenlipidomics2mztabm
/Users/knishida/.local/bin/uv run python scripts/tsv_to_mztabm.py \
  <FOR_MTD.tsv> <FOR_SMLSMF.tsv> <OUTPUT.mztab> \
  [--metadata META.json] \
  [--format tsv|json|yaml] \
  [--include-blank]
```

The script prints a one-line validation summary plus any ERRORs/WARNs, and exits non-zero if any ERROR-level message was emitted. By default `Blank`-category columns are excluded (they're solvent blanks, not real biological samples); pass `--include-blank` to keep them.

### Step 4 — Verify (optional)

The script's exit code already tells you whether validation passed. To re-validate an existing file independently:

```python
import mztab_m_io as mztabm
from mztab_m_io.model.validation import MessageType

# IMPORTANT: pass auto_complete_ids=True when re-reading TSV. The TSV reader
# discards the `id` field on indexed metadata items (instrument, sample,
# ms_run, ...) during parsing, which would otherwise produce spurious
# "id is missing" ERROR messages on a perfectly valid file. The flag re-fills
# the ids by enumeration. The authoritative validation is the in-memory
# `MzTabM.validate(...)` call the converter performs before writing — that is
# the check the script's exit code reflects.
result = mztabm.read("output.mztab", format="tsv", auto_complete_ids=True)
errors = [m for m in result.messages if m.message_type == MessageType.ERROR]
print(f"errors: {len(errors)}")
```

For a TSV-free round-trip check, write JSON instead (`--format json`) and read it back with `format="json"` — JSON preserves ids without needing `auto_complete_ids`.

## Validation rules cheat-sheet

The validator enforces these constraints. Every one is encoded in the converter — this list exists so you can reason about edge cases or new inputs.

- **Indexed metadata items must carry `id`.** `Software`, `Instrument`, `MsRun`, `Sample`, `Assay`, `StudyVariable`, `CV`, `Database`, `Contact`, `Publication`, and any `Parameter` that lives inside an indexed list (`id_confidence_measure[]`, `study_variable[].factors[]`) must have `id=1, 2, …` set explicitly — otherwise validation reports `$.metadata.<field>.<i>.id is missing`.
- **Adduct strings** must match `^\[\d*M([+-][\w\d]+)*\]\d*[+-]$`. MSDIAL emits `[M-H]-` / `[M+H]+` without the explicit charge digit; the converter normalises to `[M-H]1-` / `[M+H]1+`.
- **Cross-references** in `assay.sample_ref`, `assay.ms_run_refs`, `study_variable.assay_refs`, and `spectra_references[].ms_run_ref` must point to integer ids that actually exist in the relevant indexed list. The converter assigns `id` consecutively from 1 to keep these consistent.
- **`SmallMoleculeFeature`** requires `exp_mass_to_charge` and `charge`. The converter uses MSDIAL's `Average Mz` and assumes charge=1 (override in code if your data has explicit charge values).
- **`SmallMoleculeEvidence`** requires `evidence_input_id`, `database_identifier`, `exp_mass_to_charge`, `charge`, `theoretical_mass_to_charge`, `identification_method`, `ms_level`, `rank`, and at least one entry in `spectra_references` (whose `ms_run_ref` must point to a defined ms_run id).
- **Email deliverability** is checked via `email-validator` whenever a `contact[].email` is provided — `example.org`, `localhost`, `test.com`, etc. are rejected. Omit the field rather than pass a placeholder.
- **Unit fields** (`small_molecule_quantification_unit`, `small_molecule_feature_quantification_unit`) must be CV-term `Parameter`s whose semantics match the values you wrote (`MS:1002857` = isotopologue peak intensity for MSDIAL "Height" exports; switch to a concentration term if your block is "pmol/mg tissue").
- **Study-variable cross-check.** A `study_variable` is reported as `not referenced` (warning) unless either an SML row's `abundance_study_variable` list is at least as long as the SV index, or the SVs are referenced by an `opt_*` column. The converter computes mean-across-assays for `abundance_study_variable` so all SVs are covered.

## When to step outside the bundled script

The bundled `tsv_to_mztabm.py` is hard-coded to the RIKEN_LIPIDOMICS layout (9-row metadata table, MSDIAL alignment column names). If the user hands you something materially different — a different CSV from another vendor, raw mzML files, a MetaboLights archive — adapt the script rather than fight it. The function `build_mztabm()` is the reusable core: it maps "tabular row + sample columns" into mzTab-M model objects, so you can rewrite the TSV-reading prologue (`parse_mtd_tsv`, `_read_tsv`) for a new schema and keep the rest. Any change must keep the in-memory `validate()` ERROR count at zero.

## Files in this skill

- `SKILL.md` (this file)
- `scripts/tsv_to_mztabm.py` — converter + in-memory validator (CLI and import-as-module)
- `scripts/example_metadata.json` — populated metadata override exercising every field
- `pyproject.toml` — uv-managed env pinning `pymztab-m` to a local development-branch checkout
