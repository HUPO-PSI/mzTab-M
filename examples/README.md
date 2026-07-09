# mzTab-M example files

Filename format: `software_version_databaseID.mztab` (e.g. `msdial_5console_zenodo14263441.mztab`).

Example files are split by the spec version they target, so each is validated
against the matching jmzTab-m validator in CI:

- **`2.0/`** — files that conform to mzTab-M **2.0.0**. Validated by
  [`validate-mztab-stable.yml`](../.github/workflows/validate-mztab-stable.yml)
  with the released jmzTab-m CLI **1.0.6**. These must validate cleanly.
- **`2.1/`** — files that use mzTab-M **2.1** features (e.g. nullable SMF
  `charge`, `study_variable_group`). Validated by
  [`validate-mztab-snapshot.yml`](../.github/workflows/validate-mztab-snapshot.yml)
  with the jmzTab-m **1.0.7-SNAPSHOT** CLI.

A file belongs in `2.1/` only if it genuinely requires 2.1 features; anything
that still validates under 2.0.0 stays in `2.0/`.

### `2.1/pending-validator/` — not validated in CI

Files here use 2.1 features the jmzTab-m validator does not support yet, so they
are deliberately excluded from validation (the CI glob does not recurse into this
subfolder). Move a file back up into `2.1/` once the validator can handle it.

- `example_study_variable_group.mztab` — the validator does not yet recognise the
  top-down `study_variable_group[1-n]-study_variable_refs` field.

> Separately, `2.1/xcms+MsIO_0.0.11_MTBLS4381_onlySMF.mztab` *is* still validated
> and is currently expected to fail — it trips a validator opt-column key-collision
> bug (`opt_global_mzmin` / `opt_global_mzmax`). The 2.1 validation job is
> `continue-on-error`, so this does not block merges.
