# mzTab-M Schema Comparison Report

**Files compared:**
- `mztabm.schema-2.1.0-M.json` — JSON Schema (version 2.1.0-M)
- `mzTab_m_openapi.yml` — OpenAPI 3.1.1 YAML, version 2.1.0-M

**Date:** 2026-05-14

**Purpose:** This report reflects the current state of both schemas. All actionable datamodel differences have been resolved. The remaining documented differences are intentional architectural choices (Sections 2–3).

---

## 1. Resolved Changes (full history)

All items below are confirmed resolved in the current state of both schemas.

| # | Schema | Change | Details |
|---|---|---|---|
| 1 | OpenAPI | Version bump | `info.version` updated from `2.0.0` to `2.1.0-M` |
| 2 | OpenAPI | `Protocol` schema added | New object: `id`, `name` (required), `type` (`$ref Parameter`, required), `description`, `parameters` (array of `$ref ExtendedParameter`) |
| 3 | OpenAPI | `Metadata.protocol` added | Array of `$ref Protocol` |
| 4 | OpenAPI | `ExtendedParameter` schema added | Variant of `Parameter` where `value` is `oneOf [string, $ref Parameter]`; `cv_accession` CURIE pattern applied |
| 5 | OpenAPI | `Assay.parameters` added | Array of `$ref ExtendedParameter` |
| 6 | OpenAPI | `Assay.protocol_refs` added | Array of `$ref Protocol` |
| 7 | OpenAPI | `MsRun.parameters` added | Array of `$ref ExtendedParameter` |
| 8 | OpenAPI | `StudyVariable.ms_run_refs` added | Array of `$ref MsRun` |
| 9 | OpenAPI | `StudyVariable.group_refs` pluralised | Changed from singular `group_ref: $ref StudyVariableGroup` to `group_refs: array of $ref StudyVariableGroup` |
| 10 | OpenAPI | `StudyVariableGroup.name` property name fixed | Renamed from `parameter` to `name` (type `$ref Parameter`) |
| 11 | OpenAPI | `StudyVariableGroup.datatype` enum added | Constrained to 8 XSD datatypes: `xsd:string`, `xsd:integer`, `xsd:decimal`, `xsd:boolean`, `xsd:date`, `xsd:time`, `xsd:dateTime`, `xsd:anyURI` |
| 12 | OpenAPI | `SmallMoleculeFeature.sme_id_ref_ambiguity_code` range | Added `format: int32, minimum: 1, maximum: 3` |
| 13 | OpenAPI | `SmallMoleculeEvidence.spectra_ref` minItems | Added `minItems: 1` |
| 14 | OpenAPI | `Metadata.fileDescription` removed from required | Stale entry removed |
| 15 | OpenAPI | `Metadata.small_molecule_feature-quantification_unit` removed from required | Conditionally optional on SMF table presence; cannot be expressed as a schema constraint |
| 16 | OpenAPI | `OptColumnMapping.identifier` pattern added | Pattern `^(global\|ms_run\[\d+\]\|assay\[\d+\]\|study_variable\[\d+\])$` |
| 17 | OpenAPI | `Parameter.cv_accession` CURIE pattern added | Pattern `^([A-Za-z][A-Za-z0-9_\-\.]*:[^\s]+)?$` — empty string allowed for user parameters |
| 18 | OpenAPI | `SampleProcessing.sampleProcessing` renamed | Renamed to `sample_processing` (snake_case) |
| 19 | OpenAPI | `Publication.publicationItems` renamed | Renamed to `publication_items` (snake_case) |
| 20 | OpenAPI | `SpectraRef` renamed to `SpectraReference` | Type name now consistent with JSON Schema |
| 21 | OpenAPI | `StringList` removed | Unreferenced utility type removed |
| 22 | JSON Schema | `StudyVariable.factors` removed | Field was erroneously retained; removed |
| 23 | JSON Schema | `SmallMoleculeFeature.charge` made optional | `validation_policy.required` changed from `true` to `false` |
| 24 | JSON Schema | `Metadata.small_molecule-identification_reliability` made optional | `validation_policy.required` changed from `true` to `null` |
| 25 | JSON Schema | `Parameter.name` made non-nullable and required | Removed null from `anyOf`; `validation_policy.required` changed from `null` to `true` — now consistent with OpenAPI |
| 26 | JSON Schema | `Parameter.value` made non-nullable and required | Removed null from `anyOf`; `validation_policy.required` changed from `null` to `true` — now consistent with OpenAPI |
| 27 | JSON Schema | `OptColumnMapping.param` made optional | `validation_policy.required` changed from `true` to `false` — now consistent with OpenAPI (`param` is not in OpenAPI `required` list) |
| 28 | JSON Schema | Table-section column names lowercased | `SME_ID`→`sme_id`, `SMF_ID`→`smf_id`, `SME_ID_REFS`→`sme_id_refs`, `SME_ID_REF_ambiguity_code`→`sme_id_ref_ambiguity_code`, `SML_ID`→`sml_id`, `SMF_ID_REFS`→`smf_id_refs` — now consistent with OpenAPI |

---

## 2. Remaining Known Differences (Intentional)

All actionable differences have been resolved. The following differences are intentional and require no further changes.

### 2.1 Foreign key vs. embedded object (cross-references)

| Field | JSON Schema | OpenAPI |
|---|---|---|
| `Assay.sample_ref` | `integer` (foreign key index) | `$ref Sample` (embedded object) |
| `Assay.ms_run_ref` | `array of integer` | `array of $ref MsRun` |
| `Assay.protocol_refs` | `array of integer` | `array of $ref Protocol` |
| `MsRun.instrument_ref` | `integer` | `$ref Instrument` |
| `StudyVariable.assay_refs` | `array of integer` | `array of $ref Assay` |
| `StudyVariable.group_refs` | `array of integer` | `array of $ref StudyVariableGroup` |
| `StudyVariable.ms_run_refs` | `array of integer` | `array of $ref MsRun` |
| `SpectraReference.ms_run` | `integer` | `$ref MsRun` |

**Rationale:** JSON Schema reflects the mzTab tabular file format where cross-references use `[n]` integer indices. OpenAPI uses embedded objects suitable for REST API serialisation.

---

### 2.2 Nullable fields

JSON Schema uses `anyOf [<type>, {"type": "null"}]` systematically for most optional fields. OpenAPI uses direct non-nullable types.

Implementors should allow null values in mzTab files even where the OpenAPI definition does not declare nullability, since the mzTab specification uses `"null"` as the literal value for missing data in many fields.

---

### 2.3 JSON Schema-specific extension fields (no OpenAPI equivalent)

JSON Schema contains implementation metadata for parser/validator behaviour with no standard OpenAPI counterpart:

- `allow_multiple`, `ignore`, `list_concatenation_str`, `mztab_example`, `non_indexed_list_value`, `object_level_value`, `referenced_field_name`
- `validation_policy` sub-fields: `enforcement_level`, `maximum`, `minimum`, `pattern`, `required`, `value_constraint`
- `column_value_field`, `multiple_columns`, `referenced_section`

OpenAPI uses `x-mztab-example` and `x-mztab-serialize-by-id` as extension properties instead.

---

## 3. Types Only in OpenAPI (No JSON Schema Equivalent)

These are API infrastructure types, not part of the mzTab-M data model.

| Type | Description |
|---|---|
| `Error` | HTTP error response: `code: integer (int32)`, `message: string` |
| `ValidationMessage` | Validation result: `code: string`, `category: enum [format, logical, cross_check]`, `message_type: enum [error, warn, info]`, `message: string`, `line_number: integer (int64)` |

---

## 4. Type / Definition Inventory (Current State)

| Type Name | JSON Schema (`$defs`) | OpenAPI (`components/schemas`) | Status |
|---|---|---|---|
| `MzTab` | Yes | Yes | Match |
| `Assay` | Yes | Yes | Match |
| `CV` | Yes | Yes | Match |
| `ColumnParameterMapping` | Yes | Yes | Match |
| `Comment` | Yes | Yes | Match |
| `Contact` | Yes | Yes | Match |
| `Database` | Yes | Yes | Match |
| `ExtendedParameter` | Yes | Yes | Match |
| `Instrument` | Yes | Yes | Match |
| `Metadata` | Yes | Yes | Match |
| `MsRun` | Yes | Yes | `instrument_ref` int vs `$ref` — intentional (§2.1) |
| `OptColumnMapping` | Yes | Yes | Match |
| `Parameter` | Yes | Yes | Match |
| `Protocol` | Yes | Yes | Match |
| `Publication` | Yes | Yes | Match |
| `PublicationItem` | Yes | Yes | Match |
| `Sample` | Yes | Yes | Match |
| `SampleProcessing` | Yes | Yes | Match |
| `SmallMoleculeEvidence` | Yes | Yes | Match |
| `SmallMoleculeFeature` | Yes | Yes | Match |
| `SmallMoleculeSummary` | Yes | Yes | Match |
| `Software` | Yes | Yes | Match |
| `SpectraReference` | Yes | Yes | Match |
| `StudyVariable` | Yes | Yes | Match |
| `StudyVariableGroup` | Yes | Yes | Match |
| `Uri` | Yes | Yes | Match |
| `Error` | No | Yes | OpenAPI-only API infrastructure type |
| `ValidationMessage` | No | Yes | OpenAPI-only API infrastructure type |

---

## 5. Notable Observations

1. **Both schemas are now fully aligned** on all actionable mzTab-M 2.1.0 data model elements.

2. **Column name casing** in table sections (`sml_id`, `smf_id`, `sme_id`, etc.) is now consistent between both schemas, using lowercase API-friendly names.

3. **`Parameter.name` and `Parameter.value`** are now non-nullable and required in both schemas, providing a consistent contract for CV and user parameter serialisation.

4. **`Metadata.small_molecule_feature-quantification_unit`** is marked optional in both schemas. Its presence is conditionally expected when an SMF table exists, which cannot be expressed as a JSON Schema or OpenAPI constraint.

5. **`SmallMoleculeFeature.adduct_ion`** carries the adduct ion regex pattern in OpenAPI (`^\[\d*M([+-][\w\d]+)*\]\d*[+-]$`) but not in the JSON Schema. This minor inconsistency remains and should be addressed in a future JSON Schema update.
