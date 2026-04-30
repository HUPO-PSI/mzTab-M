# mzTab-M Schema Comparison Report

**Files compared:**
- `mztabm.schema-2.1.0-M.json` — JSON Schema (version 2.1.0-M), 6002 lines
- `mzTab_m_openapi.yml` — OpenAPI 3.1.1 YAML, 2461 lines

**Date:** 2026-04-30

---

## 1. Type/Definition Inventory

### 1.1 All Types: Cross-Reference Table

| Type Name | JSON Schema (`$defs`) | OpenAPI (`components/schemas`) |
|---|---|---|
| `MzTab` (root/top-level) | Yes (root properties) | Yes |
| `Assay` | Yes | Yes |
| `CV` | Yes | Yes |
| `ColumnParameterMapping` | Yes | Yes |
| `Comment` | Yes | Yes |
| `Contact` | Yes | Yes |
| `Database` | Yes | Yes |
| `ExtendedParameter` | Yes | **No** |
| `Instrument` | Yes | Yes |
| `Metadata` | Yes | Yes |
| `MsRun` | Yes | Yes |
| `OptColumnMapping` | Yes | Yes |
| `Parameter` | Yes | Yes |
| `Protocol` | Yes | **No** |
| `Publication` | Yes | Yes |
| `PublicationItem` | Yes | Yes |
| `Sample` | Yes | Yes |
| `SampleProcessing` | Yes | Yes |
| `SmallMoleculeEvidence` | Yes | Yes |
| `SmallMoleculeFeature` | Yes | Yes |
| `SmallMoleculeSummary` | Yes | Yes |
| `Software` | Yes | Yes |
| `SpectraReference` | Yes (named `SpectraReference`) | Yes (named `SpectraRef`) |
| `StudyVariable` | Yes | Yes |
| `StudyVariableGroup` | Yes | Yes |
| `Uri` | Yes | Yes |
| `StringList` | **No** | Yes |
| `Error` | **No** | Yes |
| `ValidationMessage` | **No** | Yes |

**Summary:**
- Types only in JSON Schema: `ExtendedParameter`, `Protocol`
- Types only in OpenAPI: `StringList`, `Error`, `ValidationMessage`
- Name difference: JSON Schema uses `SpectraReference`; OpenAPI uses `SpectraRef`

---

## 2. Detailed Per-Type Comparison

### 2.1 `MzTab` (Root Object)

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `metadata` | Yes (`$ref Metadata`, required) | Yes (`$ref Metadata`, required) | Match |
| `smallMoleculeSummary` | Yes (array of `SmallMoleculeSummary`, required) | Yes (array, required, `minItems: 1`) | JSON Schema has `required: true` in validation_policy; OpenAPI has `minItems: 1` |
| `smallMoleculeFeature` | Yes (array of `SmallMoleculeFeature`, required) | Yes (array, not `minItems`) | OpenAPI lacks `minItems: 1` |
| `smallMoleculeEvidence` | Yes (array of `SmallMoleculeEvidence`, required) | Yes (array, not `minItems`) | OpenAPI lacks `minItems: 1` |
| `comment` | Yes (array of `Comment`) | Yes (array of `Comment`) | Match |

#### `required` field differences

OpenAPI `MzTab.required` lists all four main fields (`metadata`, `smallMoleculeSummary`, `smallMoleculeFeature`, `smallMoleculeEvidence`). The JSON Schema top-level `required` array is not explicitly present (validation driven by `validation_policy.required`).

---

### 2.2 `Metadata`

#### Properties present in JSON Schema but **missing** in OpenAPI

| Property | JSON Schema type | Notes |
|---|---|---|
| `protocol` | array of `$ref Protocol` | JSON Schema has `Protocol` type; OpenAPI has no `Protocol` schema and no `protocol` property in `Metadata` |

#### Properties present in OpenAPI but **missing** in JSON Schema

| Property | OpenAPI type | Notes |
|---|---|---|
| `fileDescription` | (listed in `required` but not defined as a standalone property) | Listed in `Metadata.required` in OpenAPI: `fileDescription`. No equivalent in JSON Schema. |

#### `required` field differences

OpenAPI `Metadata.required` is an explicit list:
```yaml
required:
  - prefix
  - fileDescription
  - mzTab-version
  - mzTab-ID
  - quantification_method
  - software
  - ms_run
  - assay
  - study_variable
  - study_variable_group
  - cv
  - database
  - small_molecule-quantification_unit
  - small_molecule_feature-quantification_unit
  - id_confidence_measure
```

JSON Schema: Only `cv` is in the top-level `required` array; other fields use `validation_policy.required: true`.

Key differences in `required`:
- OpenAPI requires `fileDescription` — JSON Schema has no such field.
- OpenAPI requires `study_variable` — JSON Schema marks this with `minimum: 1` in validation_policy but does not explicitly require it in a JSON Schema `required` array.
- OpenAPI requires `study_variable_group` — same as above.
- OpenAPI requires `small_molecule-quantification_unit` — JSON Schema marks as `required: true` in validation_policy.
- OpenAPI does NOT require `small_molecule_feature-quantification_unit` (it is absent from the `required` list) — JSON Schema marks this as NOT required (validation_policy.required is null).
- OpenAPI requires `id_confidence_measure` — JSON Schema marks as `required: true`.
- JSON Schema requires `small_molecule-identification_reliability` (`required: true`) — not in OpenAPI's required list.

#### Property-level differences

| Property | JSON Schema | OpenAPI | Difference |
|---|---|---|---|
| `prefix` | `anyOf [string, null]`, default `"MTD"`, pattern `"MTD"` | `string`, enum `["MTD"]`, default `"MTD"` | JSON Schema is nullable; OpenAPI uses enum |
| `mzTab-version` | `anyOf [string, null]`, default `"2.1.0-M"`, pattern `^\d{1}\.\d{1}\.\d{1}-[A-Z]{1}$` | `string`, pattern `^\d{1}\.\d{1}\.\d{1}-[A-Z]{1}$` | JSON Schema is nullable; both have same pattern |
| `mzTab-ID` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `title` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `description` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `protocol` | array of `$ref Protocol` | **Not present** | Only in JSON Schema |
| `fileDescription` | **Not present** | Listed in `required` but no property defined | Only in OpenAPI (and not even defined as a property) |

---

### 2.3 `Assay`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present; JSON Schema is nullable |
| `name` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `custom` | `anyOf [array of Parameter, null]` | `array of Parameter` | JSON Schema is nullable |
| `external_uri` | `anyOf [string, null]`, value_constraint: any-url | `string, format: uri` | JSON Schema is nullable; OpenAPI uses `format: uri` |
| `sample_ref` | `anyOf [integer, null]`, referenced_field_name: sample | `$ref Sample` | **Type difference**: JSON Schema uses integer (foreign key); OpenAPI embeds the full `Sample` object |
| `ms_run_ref` | `anyOf [array of integer, null]`, required, list_concatenation_str: "\|" | `array of $ref MsRun`, required, `minItems: 1` | **Type difference**: JSON Schema uses integer array; OpenAPI embeds full `MsRun` objects |
| `protocol_refs` | `anyOf [array of integer, null]` | **Not present** | Only in JSON Schema |
| `parameters` | `anyOf [array of ExtendedParameter, null]` | **Not present** | Only in JSON Schema (`ExtendedParameter` does not exist in OpenAPI) |

#### `required` differences

| Field | JSON Schema (validation_policy) | OpenAPI (`required` list) |
|---|---|---|
| `name` | required: true | Yes (`name`) |
| `ms_run_ref` | required: true | Yes (`ms_run_ref`) |
| `protocol_refs` | required: null | Not in OpenAPI at all |
| `parameters` | required: null | Not in OpenAPI at all |

---

### 2.4 `CV`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `label` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `full_name` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `version` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `uri` | `anyOf [string, null]`, required, value_constraint: any-url | `string, format: uri`, required | JSON Schema is nullable; OpenAPI adds `format: uri` |

Both schemas agree on required fields (`label`, `full_name`, `version`, `uri`). No structural differences beyond nullable vs non-nullable.

---

### 2.5 `ColumnParameterMapping`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `column_name` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `param` | `anyOf [$ref Parameter, null]`, required | `$ref Parameter`, required | JSON Schema is nullable |

No significant differences. OpenAPI has `required: [column_name, param]` explicitly.

---

### 2.6 `Comment`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `prefix` | `string`, default `"COM"`, pattern `"COM"` | `string`, enum `["COM"]`, default `"COM"` | JSON Schema uses pattern; OpenAPI uses enum |
| `msg` | `anyOf [string, null]`, required | `string` | JSON Schema is nullable; OpenAPI marks as required |
| `line_number` | `anyOf [integer, null]`, value_constraint: positive-integer | `integer, format: int32` | JSON Schema is nullable; both have the field |

#### `required` differences

OpenAPI `Comment.required: [prefix, msg]`. JSON Schema: `msg` is required via `validation_policy`.

---

### 2.7 `Contact`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `name` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `affiliation` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `email` | `anyOf [string, null]`, value_constraint: email | `string`, pattern `^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$` | JSON Schema uses value_constraint; OpenAPI has explicit email regex |
| `orcid` | `anyOf [string, null]`, pattern `^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$` | `string`, pattern `^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$` | Same pattern; JSON Schema is nullable |

No properties are exclusive to one schema. OpenAPI lacks a formal `required` list for `Contact` — no fields are explicitly required.

---

### 2.8 `Database`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `param` | `$ref Parameter`, required | `$ref Parameter`, required | Match |
| `prefix` | `anyOf [string, null]`, enforcement_level: recommended | `string`, default `"null"`, required | JSON Schema is nullable, enforcement recommended; OpenAPI has default `"null"` and marks required |
| `version` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `uri` | `anyOf [string, null]`, enforcement_level: recommended | `string, format: uri`, required | JSON Schema is nullable, enforcement recommended; OpenAPI marks required and adds `format: uri` |

#### `required` differences

JSON Schema `validation_policy.required: true` for `param`, `prefix`, `version`, `uri`. OpenAPI explicitly: `required: [param, prefix, version, uri]`.

Notable: JSON Schema `enforcement_level` for `prefix` and `uri` is `"recommended"` (not `"required"`), suggesting they are best-effort — but OpenAPI treats them as fully required.

---

### 2.9 `ExtendedParameter` (JSON Schema only)

**This type exists only in the JSON Schema** and has no equivalent in OpenAPI.

Properties: `id`, `cv_label`, `cv_accession`, `name`, `value` (where `value` can be `string | $ref Parameter | null`).

The key distinction from `Parameter` is that `ExtendedParameter.value` can itself be a `Parameter` object (nested/compound value), whereas `Parameter.value` is always a `string`.

`ExtendedParameter` is used in:
- `Assay.parameters` (array of `ExtendedParameter`)
- `MsRun.parameters` (array of `ExtendedParameter`)
- `Protocol.parameters` (array of `ExtendedParameter`)

None of these usages are represented in OpenAPI.

---

### 2.10 `Instrument`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `name` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `source` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `analyzer` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable; OpenAPI has default `[]` |
| `detector` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |

No exclusive properties. OpenAPI has no `required` fields for `Instrument`.

---

### 2.11 `MsRun`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1`, **required** | OpenAPI requires `id` |
| `name` | `anyOf [string, null]`, ignore: true | `string` | JSON Schema ignores it (non-serialized); OpenAPI includes |
| `location` | `anyOf [string, null]`, required, value_constraint: any-url | `string, format: uri`, **required** | JSON Schema is nullable; OpenAPI adds `format: uri` |
| `instrument_ref` | `anyOf [integer, null]` | `$ref Instrument` | **Type difference**: JSON Schema is an integer (foreign key); OpenAPI embeds the full `Instrument` object |
| `format` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `id_format` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `fragmentation_method` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable; OpenAPI has default `[]` |
| `scan_polarity` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable; OpenAPI has default `[]` |
| `hash` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `hash_method` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `parameters` | `anyOf [array of $ref ExtendedParameter, null]` | **Not present** | Only in JSON Schema |

#### `required` differences

OpenAPI `MsRun.required: [id, location]`. JSON Schema: `location` is required via validation_policy; `id` is not (it has `ignore: true`).

---

### 2.12 `OptColumnMapping`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `identifier` | `anyOf [$ref Parameter, string, null]`, required, pattern `^global|ms_run\[\d+\]|assay\[\d+\]|study_variable\[\d+\]` | `string`, required | **Type difference**: JSON Schema allows `Parameter` or `string`; OpenAPI is `string` only. JSON Schema has pattern constraint; OpenAPI lacks it. |
| `param` | `anyOf [$ref Parameter, null]`, required | `$ref Parameter` | JSON Schema is nullable |
| `value` | `anyOf [string, null]` | `string` | JSON Schema is nullable |

#### `required` differences

OpenAPI: `required: [identifier]`. JSON Schema: `identifier` and `param` are both required via validation_policy.

---

### 2.13 `Parameter`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `cv_label` | `anyOf [string, null]`, default `""` | `string`, default `""` | JSON Schema is nullable |
| `cv_accession` | `anyOf [string, null]`, default `""`, value_constraint: curie | `string`, default `""` | JSON Schema is nullable and has CURIE format constraint; OpenAPI lacks the CURIE constraint |
| `name` | `anyOf [string, null]`, default `""` | `string`, **required** | JSON Schema is nullable and not marked required; OpenAPI marks `name` as required |
| `value` | `anyOf [string, null]`, default `""` | `string`, default `""`, **required** | JSON Schema is nullable; OpenAPI marks `value` as required |

#### `required` differences

OpenAPI `Parameter.required: [name, value]`. JSON Schema does not mark `name` or `value` as required (validation_policy.required is null).

This is a significant difference. OpenAPI requires both `name` and `value` for every `Parameter`. JSON Schema allows them to be null.

---

### 2.14 `Protocol` (JSON Schema only)

**This type exists only in the JSON Schema** and has no equivalent in OpenAPI.

Properties: `id`, `name` (required), `type` ($ref Parameter, required), `description`, `parameters` (array of ExtendedParameter).

`Protocol` is used in `Metadata.protocol` (array of Protocol). Since OpenAPI lacks both `Protocol` and the `Metadata.protocol` field, this entire feature of the 2.1.0-M spec is absent from the OpenAPI schema.

---

### 2.15 `Publication`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `publication_items` | `anyOf [array of $ref PublicationItem, null]`, required | `publicationItems` (array of $ref PublicationItem), required | **Name difference**: JSON Schema uses `publication_items`; OpenAPI uses `publicationItems` (camelCase) |

---

### 2.16 `PublicationItem`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `type` | `anyOf [string, null]`, pattern `doi|pubmed|uri` | `string`, enum `[doi, pubmed, uri]`, default `doi`, required | JSON Schema is nullable and uses pattern; OpenAPI uses enum and marks required |
| `accession` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |

---

### 2.17 `Sample`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `name` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `custom` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable |
| `species` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable |
| `tissue` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable |
| `cell_type` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable |
| `disease` | `anyOf [array of $ref Parameter, null]` | `array of $ref Parameter`, default `[]` | JSON Schema is nullable |
| `description` | `anyOf [string, null]` | `string` | JSON Schema is nullable |

No exclusive properties. No OpenAPI `required` list.

---

### 2.18 `SampleProcessing`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `sample_processing` | `anyOf [array of $ref Parameter, null]`, object_level_value: true | — | — |
| `sampleProcessing` | — | `array of $ref Parameter`, default `[]` | — |

**Name difference**: JSON Schema uses `sample_processing` (snake_case); OpenAPI uses `sampleProcessing` (camelCase).

---

### 2.19 `Software`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `parameter` | `anyOf [$ref Parameter, null]`, object_level_value: true | `$ref Parameter` | JSON Schema is nullable |
| `setting` | `anyOf [array of string, null]` | `array of string`, default `[]` | JSON Schema is nullable |

No exclusive properties.

---

### 2.20 `SpectraReference` / `SpectraRef`

The JSON Schema names this type `SpectraReference`; OpenAPI names it `SpectraRef`.

#### Properties comparison

| Property | JSON Schema (`SpectraReference`) | OpenAPI (`SpectraRef`) | Notes |
|---|---|---|---|
| `ms_run` | `anyOf [integer, null]`, required, value_constraint: positive-integer | `$ref MsRun`, required | **Type difference**: JSON Schema uses integer (foreign key); OpenAPI embeds full `MsRun` object |
| `reference` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |

---

### 2.21 `StudyVariable`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1`, required | OpenAPI requires `id` |
| `name` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `group_refs` | `anyOf [array of integer, null]`, referenced: study_variable_group | — | Only in JSON Schema |
| `group_ref` | — | `$ref StudyVariableGroup` | Only in OpenAPI |
| `assay_refs` | `anyOf [array of integer, null]`, referenced: assay | `array of $ref Assay`, default `[]` | **Type difference**: JSON Schema uses integer array; OpenAPI embeds Assay objects |
| `ms_run_refs` | `anyOf [array of integer, null]`, referenced: ms_run | **Not present** | Only in JSON Schema |
| `average_function` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `variation_function` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `description` | `anyOf [string, null]` | `string` | JSON Schema is nullable |
| `factors` | `anyOf [array of $ref Parameter, null]` | **Not present** | Only in JSON Schema |

#### `required` differences

OpenAPI `StudyVariable.required: [id, name]`. JSON Schema: `name` required via validation_policy; `id` has `ignore: true`.

Key exclusive properties:
- **JSON Schema only**: `group_refs` (plural, integer array), `ms_run_refs`, `factors`
- **OpenAPI only**: `group_ref` (singular, `$ref StudyVariableGroup`)

The `group_refs` vs `group_ref` discrepancy indicates the JSON Schema tracks multi-group membership (array of integer IDs), whereas OpenAPI allows only a single group reference.

---

### 2.22 `StudyVariableGroup`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1`, required | OpenAPI requires `id` |
| `name` | `anyOf [$ref Parameter, null]`, required | — | **Only in JSON Schema** as a Parameter |
| `parameter` | — | `$ref Parameter`, description: CV or user parameter | **Only in OpenAPI** as a property named `parameter` |
| `description` | `anyOf [string, null]`, required | `string`, required | JSON Schema is nullable |
| `type` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |
| `datatype` | `anyOf [enum string, null]` — see below | `string` | JSON Schema has constrained enum; OpenAPI has plain string |
| `unit` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema is nullable |

**Name difference**: The principal CV/parameter that defines the group is called `name` in JSON Schema and `parameter` in OpenAPI. This is a direct naming conflict that will affect serialization.

#### `datatype` enum values

JSON Schema (`StudyVariableGroup.datatype`) constrains to:
```json
["xsd:string", "xsd:integer", "xsd:decimal", "xsd:boolean", "xsd:date", "xsd:time", "xsd:dateTime", "xsd:anyURI"]
```

OpenAPI (`StudyVariableGroup.datatype`) is defined as plain `string` without enum constraints. This means OpenAPI accepts any string value; JSON Schema restricts to the eight XSD datatypes listed.

#### `required` differences

OpenAPI: `required: [id, parameter, description]`. JSON Schema: `name` (= the parameter) is required; `description` is required; `id` has `ignore: true`.

---

### 2.23 `Uri`

#### Properties comparison

| Property | JSON Schema | OpenAPI | Notes |
|---|---|---|---|
| `id` | `anyOf [integer (min 1), null]`, ignore: true | `integer (int32), minimum: 1` | Both present |
| `value` | `anyOf [string, null]`, value_constraint: any-url | `string, format: uri` | JSON Schema is nullable; OpenAPI adds `format: uri` |

---

### 2.24 `SmallMoleculeSummary`

#### Property naming

JSON Schema uses **uppercase** property names for table columns: `SML_ID`, `SMF_ID_REFS`. OpenAPI uses **lowercase/camelCase**: `sml_id`, `smf_id_refs`.

#### Properties comparison

| JSON Schema name | OpenAPI name | JSON Schema type | OpenAPI type | Notes |
|---|---|---|---|---|
| `SML_ID` | `sml_id` | `anyOf [integer, null]`, required | `integer, format: int32`, required | Case difference |
| `SMF_ID_REFS` | `smf_id_refs` | `anyOf [array of integer, null]` | `array of integer (int32)`, default `[]` | Case difference; JSON Schema nullable |
| `database_identifier` | `database_identifier` | `anyOf [array of string, null]` | `array of string`, default `[]` | JSON Schema nullable |
| `chemical_formula` | `chemical_formula` | `anyOf [array of string, null]` | `array of string`, default `[]` | JSON Schema nullable |
| `smiles` | `smiles` | `anyOf [array of string, null]` | `array of string`, default `[]` | JSON Schema nullable |
| `inchi` | `inchi` | `anyOf [array of string, null]` | `array of string`, default `[]` | JSON Schema nullable |
| `chemical_name` | `chemical_name` | `anyOf [array of string, null]` | `array of string`, default `[]` | JSON Schema nullable |
| `uri` | `uri` | `anyOf [array of string, null]`, value_constraint: any-url | `array of string (format: uri)`, default `[]` | JSON Schema nullable; OpenAPI adds `format: uri` to items |
| `theoretical_neutral_mass` | `theoretical_neutral_mass` | `anyOf [array of number\|null, null]` | `array of number (double)`, default `[]` | JSON Schema allows null items in array; OpenAPI does not |
| `adduct_ions` | `adduct_ions` | `anyOf [array of string with pattern, null]` | `array of string`, `pattern: '^\[\d*M...'` | Pattern is on array-level in OpenAPI, on item-level in JSON Schema |
| `reliability` | `reliability` | `anyOf [string, null]` | `string` | JSON Schema nullable |
| `best_id_confidence_measure` | `best_id_confidence_measure` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema nullable |
| `best_id_confidence_value` | `best_id_confidence_value` | `anyOf [number, null]` | `number (double)` | JSON Schema nullable |
| `abundance_assay` | `abundance_assay` | `anyOf [array of number\|null, null]` | `array of number (double)`, default `[]` | JSON Schema allows null items; OpenAPI does not |
| `abundance_study_variable` | `abundance_study_variable` | `anyOf [array of number\|null, null]` | `array of number (double)`, default `[]` | JSON Schema allows null items; OpenAPI does not |
| `abundance_variation_study_variable` | `abundance_variation_study_variable` | `anyOf [array of number\|null, null]` | `array of number (double)`, default `[]` | JSON Schema allows null items; OpenAPI does not |
| `opt` | `opt` | `anyOf [array of $ref OptColumnMapping, null]` | `array of $ref OptColumnMapping`, default `[]` | JSON Schema nullable |
| `comment` | `comment` | `anyOf [array of $ref Comment, null]`, ignore: true | `array of $ref Comment`, default `[]` | JSON Schema nullable |
| `prefix` | `prefix` | pattern `"SML"`, ignore: true | enum `["SML"]`, default `"SML"`, readOnly: true | Both present; style difference |
| `header_prefix` | `header_prefix` | pattern `"SMH"`, ignore: true | enum `["SMH"]`, default `"SMH"`, readOnly: true | Both present; style difference |

#### `required` differences

OpenAPI: `required: [sml_id]`. JSON Schema: `SML_ID` required via validation_policy.

---

### 2.25 `SmallMoleculeFeature`

#### Property naming

JSON Schema uses uppercase: `SMF_ID`, `SME_ID_REFS`, `SME_ID_REF_ambiguity_code`. OpenAPI uses lowercase/camelCase: `smf_id`, `sme_id_refs`, `sme_id_ref_ambiguity_code`.

#### Properties comparison

| JSON Schema name | OpenAPI name | JSON Schema type | OpenAPI type | Notes |
|---|---|---|---|---|
| `SMF_ID` | `smf_id` | `anyOf [integer, null]`, required | `integer, format: int32`, required | Case difference |
| `SME_ID_REFS` | `sme_id_refs` | `anyOf [array of integer, null]`, list_sep: "\|" | `array of integer (int32)`, default `[]` | JSON Schema nullable |
| `SME_ID_REF_ambiguity_code` | `sme_id_ref_ambiguity_code` | `anyOf [integer, null]`, max: 3, min: 1 | `integer (int32)` | JSON Schema has min/max constraint (1–3); OpenAPI lacks this constraint |
| `adduct_ion` | `adduct_ion` | `anyOf [string, null]` (no pattern in JSON Schema for SMF) | `string`, pattern `'^\[\d*M...'` | OpenAPI has pattern; JSON Schema has no pattern for this field (adduct pattern missing) |
| `isotopomer` | `isotopomer` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema nullable |
| `exp_mass_to_charge` | `exp_mass_to_charge` | `anyOf [number, null]`, required | `number (double)`, required | JSON Schema nullable |
| `charge` | `charge` | `anyOf [integer, null]`, required | `integer (int32)`, required | JSON Schema nullable |
| `retention_time_in_seconds` | `retention_time_in_seconds` | `anyOf [number, null]` | `number (double)` | JSON Schema nullable |
| `retention_time_in_seconds_start` | `retention_time_in_seconds_start` | `anyOf [number, null]` | `number (double)` | JSON Schema nullable |
| `retention_time_in_seconds_end` | `retention_time_in_seconds_end` | `anyOf [number, null]` | `number (double)` | JSON Schema nullable |
| `abundance_assay` | `abundance_assay` | `anyOf [array of number\|null, null]` | `array of number (double)`, default `[]` | JSON Schema allows null items; OpenAPI does not |
| `opt` | `opt` | `anyOf [array of $ref OptColumnMapping, null]` | `array of $ref OptColumnMapping`, default `[]` | JSON Schema nullable |
| `comment` | `comment` | `anyOf [array of $ref Comment, null]`, ignore: true | `array of $ref Comment`, default `[]` | JSON Schema nullable |

#### `required` differences

OpenAPI: `required: [smf_id, exp_mass_to_charge]`. JSON Schema: `SMF_ID`, `exp_mass_to_charge`, `charge` required via validation_policy.

**Discrepancy**: JSON Schema requires `charge`; OpenAPI does not.

---

### 2.26 `SmallMoleculeEvidence`

#### Property naming

JSON Schema uses uppercase: `SME_ID`. OpenAPI uses lowercase: `sme_id`.

#### Properties comparison

| JSON Schema name | OpenAPI name | JSON Schema type | OpenAPI type | Notes |
|---|---|---|---|---|
| `SME_ID` | `sme_id` | `anyOf [integer, null]`, required | `integer (int32)`, required | Case difference |
| `evidence_input_id` | `evidence_input_id` | `anyOf [string, null]`, required | `string`, required | JSON Schema nullable |
| `database_identifier` | `database_identifier` | `anyOf [string, null]`, required | `string`, required | JSON Schema nullable |
| `chemical_formula` | `chemical_formula` | `anyOf [string, null]` | `string` | JSON Schema nullable |
| `smiles` | `smiles` | `anyOf [string, null]` | `string` | JSON Schema nullable |
| `inchi` | `inchi` | `anyOf [string, null]` | `string` | JSON Schema nullable |
| `chemical_name` | `chemical_name` | `anyOf [string, null]` | `string` | JSON Schema nullable |
| `uri` | `uri` | `anyOf [string, null]`, value_constraint: any-url | `string, format: uri` | JSON Schema nullable; OpenAPI adds `format: uri` |
| `derivatized_form` | `derivatized_form` | `anyOf [$ref Parameter, null]` | `$ref Parameter` | JSON Schema nullable |
| `adduct_ion` | `adduct_ion` | `anyOf [string, null]`, pattern `^\[\d*M...` | `string`, pattern `'^\[\d*M...'` | Both have the same pattern; JSON Schema nullable |
| `exp_mass_to_charge` | `exp_mass_to_charge` | `anyOf [number, null]`, required | `number (double)`, required | JSON Schema nullable |
| `charge` | `charge` | `anyOf [integer, null]`, required | `integer (int32)`, required | JSON Schema nullable |
| `theoretical_mass_to_charge` | `theoretical_mass_to_charge` | `anyOf [number, null]`, required | `number (double)`, required | JSON Schema nullable |
| `spectra_ref` | `spectra_ref` | `anyOf [array of $ref SpectraReference, null]`, required, min 1 | `array of $ref SpectraRef`, default `[]` | **Name difference in $ref**; JSON Schema requires it; OpenAPI doesn't; JSON Schema min 1 |
| `identification_method` | `identification_method` | `anyOf [$ref Parameter, null]`, required | `$ref Parameter`, required | JSON Schema nullable |
| `ms_level` | `ms_level` | `anyOf [$ref Parameter, null]`, required | `$ref Parameter`, required | JSON Schema nullable |
| `id_confidence_measure` | `id_confidence_measure` | `anyOf [array of number\|null, null]` | `array of number (double)`, default `[]` | JSON Schema allows null items; OpenAPI does not |
| `rank` | `rank` | `anyOf [integer, null]`, required, value_constraint: positive-integer | `integer (int32)`, minimum: 1, default: 1, required | JSON Schema nullable; OpenAPI has `minimum: 1` and `default: 1` |
| `opt` | `opt` | `anyOf [array of $ref OptColumnMapping, null]` | `array of $ref OptColumnMapping`, default `[]` | JSON Schema nullable |
| `comment` | `comment` | `anyOf [array of $ref Comment, null]`, ignore: true | `array of $ref Comment`, default `[]` | JSON Schema nullable |

#### `required` differences

OpenAPI: `required: [sme_id, evidence_input_id, database_identifier, exp_mass_to_charge, charge, theoretical_mass_to_charge, spectra_ref, identification_method, ms_level, rank]`.

JSON Schema: all of the above are required via validation_policy, plus `spectra_ref` has `minimum: 1`.

**Discrepancy**: OpenAPI requires `spectra_ref` but does not set `minItems`. JSON Schema requires it with `minimum: 1` (at least one entry).

---

### 2.27 `StringList` (OpenAPI only)

```yaml
StringList:
  type: array
  default: []
  description: A typed list of strings.
  items:
    type: string
```

This is a utility type in OpenAPI with no direct equivalent in the JSON Schema. It appears to be defined but not widely referenced within the OpenAPI schema itself.

---

### 2.28 `Error` (OpenAPI only)

```yaml
Error:
  type: object
  required: [code, message]
  properties:
    code:
      type: integer
      format: int32
    message:
      type: string
```

This is an API-level error type for HTTP error responses. No equivalent in JSON Schema (which only covers the data model).

---

### 2.29 `ValidationMessage` (OpenAPI only)

```yaml
ValidationMessage:
  type: object
  required: [code, category, message]
  properties:
    code:
      type: string
    category:
      enum: [format, logical, cross_check]
      default: format
    message_type:
      enum: [error, warn, info]
      default: info
    message:
      type: string
    line_number:
      type: integer
      format: int64
```

This is an API-level type for validation results. No equivalent in JSON Schema.

---

## 3. Enum Value Differences

### 3.1 `Comment.prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | `string`, pattern `"COM"` | Pattern match, not strictly an enum |
| OpenAPI | `string`, enum | `["COM"]` |

### 3.2 `Metadata.prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | `anyOf [string, null]`, pattern `"MTD"` | Pattern match |
| OpenAPI | `string`, enum | `["MTD"]` |

### 3.3 `SmallMoleculeSummary.prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | pattern `"SML"`, ignore: true | Pattern match |
| OpenAPI | `string`, enum, readOnly | `["SML"]` |

### 3.4 `SmallMoleculeSummary.header_prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | pattern `"SMH"`, ignore: true | Pattern match |
| OpenAPI | `string`, enum, readOnly | `["SMH"]` |

### 3.5 `SmallMoleculeFeature.prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | pattern `"SMF"` | Pattern match |
| OpenAPI | `string`, enum, readOnly | `["SMF"]` |

### 3.6 `SmallMoleculeFeature.header_prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | pattern `"SFH"` | Pattern match |
| OpenAPI | `string`, enum, readOnly | `["SFH"]` |

### 3.7 `SmallMoleculeEvidence.prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | pattern `"SME"` | Pattern match |
| OpenAPI | `string`, enum, readOnly | `["SME"]` |

### 3.8 `SmallMoleculeEvidence.header_prefix`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | pattern `"SEH"` | Pattern match |
| OpenAPI | `string`, enum, readOnly | `["SEH"]` |

### 3.9 `PublicationItem.type`

| Schema | Type | Values |
|---|---|---|
| JSON Schema | `anyOf [string, null]`, pattern `doi|pubmed|uri` | Pattern match, nullable |
| OpenAPI | `string`, enum, default `doi` | `["doi", "pubmed", "uri"]` |

### 3.10 `StudyVariableGroup.datatype`

| Schema | Type | Allowed values |
|---|---|---|
| JSON Schema | `anyOf [enum string, null]` | `xsd:string`, `xsd:integer`, `xsd:decimal`, `xsd:boolean`, `xsd:date`, `xsd:time`, `xsd:dateTime`, `xsd:anyURI` |
| OpenAPI | `string` (no enum constraint) | Any string value |

**This is a significant enum gap**: the JSON Schema enforces a closed set of 8 XSD datatypes; OpenAPI imposes no constraint.

### 3.11 `ValidationMessage.category` (OpenAPI only)

Enum values: `["format", "logical", "cross_check"]`.

### 3.12 `ValidationMessage.message_type` (OpenAPI only)

Enum values: `["error", "warn", "info"]`.

---

## 4. Structural Differences

### 4.1 Nullable fields

The JSON Schema systematically uses `anyOf [<type>, {"type": "null"}]` to express nullable fields. OpenAPI 3.1.1 supports this natively (as it is based on JSON Schema 2020-12), but the OpenAPI file does not use nullability for most fields — most OpenAPI properties are non-nullable strings, integers, or `$ref` types.

This means JSON Schema is more permissive (accepts null where OpenAPI would reject it at the schema validation level).

### 4.2 $ref patterns and reference style

| Aspect | JSON Schema | OpenAPI |
|---|---|---|
| Reference prefix | `#/$defs/TypeName` | `#/components/schemas/TypeName` |
| Foreign key vs embedded object | Uses integer IDs for cross-references (e.g., `sample_ref: integer`, `ms_run: integer`, `assay_refs: [integer]`) | Embeds full objects (e.g., `sample_ref: $ref Sample`, `ms_run_ref: [MsRun]`, `assay_refs: [Assay]`) |

The foreign key vs. embedded object difference is systematic and affects many cross-reference fields:

| Field | JSON Schema | OpenAPI |
|---|---|---|
| `Assay.sample_ref` | `integer` (refers to sample id) | `$ref Sample` |
| `Assay.ms_run_ref` | `array of integer` | `array of $ref MsRun` |
| `MsRun.instrument_ref` | `integer` | `$ref Instrument` |
| `StudyVariable.assay_refs` | `array of integer` | `array of $ref Assay` |
| `StudyVariable.group_ref` | `group_refs: array of integer` | `group_ref: $ref StudyVariableGroup` |
| `SpectraReference.ms_run` | `integer` | `$ref MsRun` |

### 4.3 allOf / oneOf / anyOf usage

- **JSON Schema**: Uses `anyOf` extensively for nullable fields (`anyOf [<type>, {"type": "null"}]`). No `allOf` or `oneOf` is used.
- **OpenAPI**: Does not use `anyOf`, `allOf`, or `oneOf` for any type definitions. All types are defined as direct `object` or scalar types with `$ref` references.

### 4.4 additionalProperties

Neither schema defines `additionalProperties: false` on any type. Both allow additional properties by default.

### 4.5 JSON Schema-specific extension fields

The JSON Schema contains many custom extension fields on each property that have no OpenAPI equivalent:
- `allow_multiple`, `ignore`, `list_concatenation_str`, `mztab_example`, `non_indexed_list_value`, `object_level_value`, `referenced_field_name`, `validation_policy`, `column_value_field`, `multiple_columns`, `referenced_section`

These are implementation-specific metadata used by the mzTab-M parser/validator and are not part of standard JSON Schema. OpenAPI uses `x-mztab-example` and `x-mztab-serialize-by-id` as extension properties.

### 4.6 Column-level vs object-level field naming

For table section rows (`SmallMoleculeSummary`, `SmallMoleculeFeature`, `SmallMoleculeEvidence`), the JSON Schema uses **uppercase column names** as they appear in mzTab TSV files (`SML_ID`, `SMF_ID`, `SME_ID`, `SMF_ID_REFS`, `SME_ID_REFS`, `SME_ID_REF_ambiguity_code`). The OpenAPI uses lowercase with underscores (`sml_id`, `smf_id`, `sme_id`, `smf_id_refs`, `sme_id_refs`, `sme_id_ref_ambiguity_code`).

### 4.7 `SampleProcessing` inner array naming

| Schema | Property name |
|---|---|
| JSON Schema | `sample_processing` (snake_case, `object_level_value: true`) |
| OpenAPI | `sampleProcessing` (camelCase) |

### 4.8 `Publication.publicationItems` naming

| Schema | Property name |
|---|---|
| JSON Schema | `publication_items` |
| OpenAPI | `publicationItems` |

---

## 5. Missing Features in OpenAPI (from JSON Schema 2.1.0-M)

The following features present in `mztabm.schema-2.1.0-M.json` are entirely absent from `mzTab_m_openapi.yml`:

1. **`Protocol` type** — A new top-level type representing experimental protocols, with fields `name` (required), `type` ($ref Parameter), `description`, and `parameters` (array of ExtendedParameter).

2. **`Metadata.protocol`** — The array of `Protocol` objects in `Metadata`. This field is present in JSON Schema but not in the OpenAPI `Metadata` schema.

3. **`ExtendedParameter` type** — A variant of `Parameter` where `value` can itself be a `Parameter` object. Used by `Assay.parameters`, `MsRun.parameters`, and `Protocol.parameters`.

4. **`Assay.parameters`** — Array of `ExtendedParameter` for additional assay parameters.
   
5. **`Assay.protocol_refs`** — Integer array referencing protocols.

6. **`MsRun.parameters`** — Array of `ExtendedParameter` for additional ms_run parameters.

7. **`StudyVariable.ms_run_refs`** — Integer array referencing ms_runs associated with a study variable.

8. **`StudyVariable.factors`** — Array of `Parameter` for factor level information.

9. **`StudyVariable.group_refs` (plural)** — JSON Schema allows a study variable to reference multiple groups (array of integers). OpenAPI allows only one (`group_ref: $ref StudyVariableGroup`).

10. **`StudyVariableGroup.datatype` enum constraint** — The OpenAPI version accepts any string; JSON Schema constrains to 8 specific XSD datatypes.

11. **`StudyVariableGroup.name` vs `parameter` naming** — The CV/parameter defining a study variable group is called `name` (of type `$ref Parameter`) in JSON Schema and `parameter` in OpenAPI.

12. **`SME_ID_REF_ambiguity_code` range constraint** — JSON Schema enforces minimum: 1, maximum: 3. OpenAPI has no such constraint.

13. **`SmallMoleculeFeature.charge` as required** — JSON Schema marks `charge` as required; OpenAPI's required list only includes `smf_id` and `exp_mass_to_charge`.

---

## 6. Items in OpenAPI Not Present or Differing from JSON Schema

1. **`Metadata.fileDescription`** — Listed in OpenAPI `Metadata.required` but not defined as a property in either schema. This appears to be a stale entry in the `required` list.

2. **`StringList`** — A simple reusable array type defined in OpenAPI but unused and absent from JSON Schema.

3. **`Error` and `ValidationMessage`** — API-level types for HTTP responses, not part of the data model. No equivalent in JSON Schema.

4. **`OpenAPI version`** — The OpenAPI file declares `version: 2.0.0` in the info section; the JSON Schema is explicitly `2.1.0-M`. The OpenAPI needs a version bump.

5. **`SmallMoleculeFeature.adduct_ion` pattern** — OpenAPI applies the adduct ion regex pattern to `SmallMoleculeFeature.adduct_ion`; the JSON Schema does not include the pattern for this specific field (pattern is present in SME and in SML `adduct_ions` items but not in SMF `adduct_ion`). This is likely a JSON Schema oversight.

---

## 7. Summary: Changes Needed

### 7.1 Changes to `mzTab_m_openapi.yml` to align with JSON Schema 2.1.0-M

#### Critical / Breaking

| Change | Description |
|---|---|
| Bump version | Update `info.version` from `2.0.0` to `2.1.0` |
| Add `Protocol` schema | Define a new `Protocol` object with `id`, `name` (required), `type` ($ref Parameter), `description`, `parameters` (array of $ref Parameter or ExtendedParameter) |
| Add `Metadata.protocol` | Add `protocol: array of $ref Protocol` to the `Metadata` schema |
| Add `ExtendedParameter` schema | Define `ExtendedParameter` with `id`, `cv_label`, `cv_accession`, `name`, `value` (string or Parameter) |
| Add `Assay.parameters` | Add `parameters: array of $ref ExtendedParameter` to Assay |
| Add `Assay.protocol_refs` | Add `protocol_refs: array of $ref Protocol` (or integer array) |
| Add `MsRun.parameters` | Add `parameters: array of $ref ExtendedParameter` to MsRun |
| Rename `StudyVariableGroup.parameter` | Rename from `parameter` to `name` (to match JSON Schema), or document the intentional difference |
| Add `StudyVariable.ms_run_refs` | Add `ms_run_refs: array of $ref MsRun` to StudyVariable |
| Add `StudyVariable.factors` | Add `factors: array of $ref Parameter` to StudyVariable |
| Fix `StudyVariable.group_refs` | Change from singular `group_ref: $ref StudyVariableGroup` to plural `group_refs: array of $ref StudyVariableGroup` (or keep singular and document the intentional simplification) |
| Add `StudyVariableGroup.datatype` enum | Restrict `datatype` to `[xsd:string, xsd:integer, xsd:decimal, xsd:boolean, xsd:date, xsd:time, xsd:dateTime, xsd:anyURI]` |
| Add `SME_ID_REF_ambiguity_code` range | Add `minimum: 1, maximum: 3` to `SmallMoleculeFeature.sme_id_ref_ambiguity_code` |
| Add `charge` to `SmallMoleculeFeature.required` | JSON Schema marks `charge` as required in SMF |
| `spectra_ref` minItems | Add `minItems: 1` to `SmallMoleculeEvidence.spectra_ref` |
| Remove `fileDescription` from required | Remove `fileDescription` from `Metadata.required` (it is not defined as a property in either schema) |

#### Minor / Non-breaking

| Change | Description |
|---|---|
| `SampleProcessing` field name | Reconcile `sampleProcessing` (OpenAPI) vs `sample_processing` (JSON Schema) — align on one convention |
| `Publication` field name | Reconcile `publicationItems` (OpenAPI) vs `publication_items` (JSON Schema) |
| `Parameter.cv_accession` CURIE constraint | Consider adding a CURIE format or pattern constraint to `cv_accession` in OpenAPI to match JSON Schema's `value_constraint: curie` |
| `Parameter` nullable fields | JSON Schema allows `cv_label`, `cv_accession`, `name`, `value` to be null; OpenAPI marks `name` and `value` as required non-null. Decide on the authoritative rule. |
| Add `uri` format annotations | JSON Schema uses `value_constraint: any-url`; OpenAPI uses `format: uri`. Both are present in many places but not uniformly. |
| `nullable` fields policy | Decide whether OpenAPI fields should use `nullable: true` (OAS 3.0 style) or `anyOf [type, null]` (OAS 3.1 style) to match JSON Schema |
| Add `SmallMoleculeFeature.adduct_ion` pattern | The adduct ion regex is present in OpenAPI for SMF but absent in JSON Schema — add it to JSON Schema for consistency |

### 7.2 Changes to JSON Schema to align with OpenAPI

| Change | Description |
|---|---|
| Add `SmallMoleculeFeature.adduct_ion` pattern | Add pattern `^\[\d*M([+-][\w\d]+)*\]\d*[+-]$` to `SmallMoleculeFeature.adduct_ion` (JSON Schema currently has no pattern for this field) |
| Review `MsRun.id` required status | OpenAPI requires `id` in `MsRun`; JSON Schema has `ignore: true` for `id`. Consider whether the serialized form should mandate `id`. |
| Review `StudyVariable.id` required status | Same issue as MsRun — OpenAPI requires `id`; JSON Schema ignores it. |
| Review `StudyVariableGroup.id` required status | Same as above. |

---

## 8. Notable Observations

1. **Embedded objects vs. foreign keys**: The OpenAPI schema takes an ORM-like approach where cross-references use embedded full objects (e.g., `Assay.sample_ref` is `$ref Sample`). The JSON Schema takes a database-like foreign key approach (integer IDs). This is a fundamental architectural difference that affects how the two schemas are used: OpenAPI is suitable for REST API serialization; JSON Schema is closer to a tabular/flat representation that mirrors the mzTab file format.

2. **mzTab-M 2.1.0 vs 2.0.0**: The JSON Schema is explicitly version 2.1.0-M with new features (`Protocol`, `StudyVariableGroup`, `ExtendedParameter`, `group_refs`, `ms_run_refs`, `factors`). The OpenAPI YAML is based on 2.0.0 and partially incorporates 2.1.0 features (`StudyVariableGroup` is present) but is not yet fully updated.

3. **Column name casing**: The mzTab format uses uppercase for column headers (`SML_ID`, `SMF_ID`, etc.). The JSON Schema preserves this uppercase naming in property names for table rows, while OpenAPI normalizes to lowercase. This is a representation choice: the JSON Schema property names map directly to mzTab column headers; the OpenAPI property names use API-friendly casing.

4. **`Metadata.fileDescription`**: The presence of `fileDescription` in OpenAPI's `Metadata.required` list without a corresponding property definition in either schema suggests it is a stale artifact that should be removed from the required list.

5. **`StringList` in OpenAPI**: This utility type is defined but appears to be unused in the OpenAPI schema itself — it may be a leftover or intended for future use.

6. **Extension metadata**: The JSON Schema contains rich implementation metadata (`ignore`, `multiple_columns`, `column_value_field`, `validation_policy`, `list_concatenation_str`, etc.) that drives parser behavior. This information has no equivalent in OpenAPI and would need to be incorporated as `x-` extension properties if needed in the OpenAPI representation.
