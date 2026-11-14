# mzTab-M example files

Filename format: `software_version_databaseID.mztab` (e.g. `msdial_5console_zenodo14263441.mztab`).

Example files are split by the spec version they target, so each is validated
against the matching jmzTab-m validator in CI:

- **`2.0/`** — files that conform to mzTab-M **2.0.0**. Validated by
  [`validate-mztab-stable.yml`](../.github/workflows/validate-mztab-stable.yml)
  with the released jmzTab-m CLI **1.0.6**. These must validate cleanly.
  `validate-mztab-snapshot.yml` additionally validates them with the 2.1
  validator, to check backward compatibility. Failures there are reported but
  do not fail the workflow.
- **`2.1/`** — files that use mzTab-M **2.1** features (e.g. nullable SMF
  `charge`, `study_variable_group`, `mzTab-profile`). Validated by
  [`validate-mztab-snapshot.yml`](../.github/workflows/validate-mztab-snapshot.yml)
  with the native jmzTab-m validator from the
  [`dev-latest`](https://github.com/lifs-tools/jmzTab-m/releases/tag/dev-latest)
  pre-release (currently **2.1.0-SNAPSHOT**). Validation errors fail a file;
  warnings (e.g. `Warn-2056` for the tolerated `M+S+F` profile) are reported as
  annotations only.

A file belongs in `2.1/` only if it genuinely requires 2.1 features; anything
that still validates under 2.0.0 stays in `2.0/`.

### Validating locally

[`validate.sh`](../validate.sh) in the repository root downloads the same
validators as CI (cached in `build/validator/`) and applies the same rules:

```bash
./validate.sh                                 # all examples, stable + snapshot, like CI
./validate.sh my_file.mztab other.json        # own files, snapshot validator
./validate.sh -v stable examples/2.0/LDA*     # own files, stable validator
./validate.sh --help                          # all options
```

The stable validator needs Java. The snapshot validator is a native binary on
macOS (Apple silicon), Linux (x86_64) and Windows (x86_64), and falls back to the
CLI jar (needs Java) elsewhere.

### `mzTab-profile` examples

The following files demonstrate the `mzTab-profile` metadata field (one per
profile):

- `manual_null_MTD-only.mztab` — profile `M` (metadata only).
- `lipidcompass-script_226ea96_MTD_SML_LCS-00001-01_v2.1.mztab` — profile `M+S`
  (summary only).
- `xcms+MsIO_0.0.11_MTBLS1820_onlySMF_v2.1.mztab` — profile `M+F` (features only,
  no synthetic summary row).
- `manual_null_null_lipidomics_v2.1.mztab` — profile `M+F+E` (features + evidence,
  no summary).
