# OpenAPI Integration Plan: mztabm.schema-2.1.0-M → mzTab_m_openapi.yml

**Goal:** Bring `mzTab_m_openapi.yml` (currently at model version 2.0.0) into alignment with
`mztabm.schema-2.1.0-M.json` by adding missing types, missing fields, correcting naming
differences, and tightening validation constraints.

**Out of scope:** `StringList`, `Error`, `ValidationMessage` (API-level types, intentionally
kept only in OpenAPI).

**Approach note — embedded objects vs. integer foreign keys:**  
The JSON Schema uses integer IDs for cross-references; the OpenAPI embeds full objects. That
architectural difference is intentional and is **not** changed here. New fields that are
cross-references (e.g., `Assay.protocol_refs`) therefore follow the OpenAPI convention of
embedding full `$ref` objects rather than integer arrays.

---

## Phase 1 — Add new type definitions

### 1.1 Add `ExtendedParameter` to `components/schemas`

`ExtendedParameter` is identical to `Parameter` except `value` may itself be a `Parameter`
object (to represent nested/compound CV parameters). It is used by `Assay.parameters`,
`MsRun.parameters`, and `Protocol.parameters`.

**Location:** insert after the `Parameter` definition (around line 1718 in the current file).

```yaml
    ExtendedParameter:
      description: >
        An extended parameter that allows the value field to hold either a plain string or a
        nested Parameter object. Used where a CV-parameterized value is itself a CV term
        (e.g. instrument acquisition parameters).

        Parameters are always reported as [CV label, accession, name, value]. Any field that
        is not available MUST be left empty.
      x-mztab-example: |
        [MS, MS:1000031, instrument model, [MS, MS:1000449, LTQ Orbitrap,]]
        [,,A user parameter, The value]
      type: object
      properties:
        id:
          type: integer
          format: int32
          minimum: 1
        cv_label:
          type: string
          default: ""
        cv_accession:
          type: string
          default: ""
        name:
          type: string
        value:
          description: >
            The parameter value. May be a plain string or a nested Parameter object when
            the value is itself a controlled vocabulary term.
          oneOf:
            - type: string
            - $ref: "#/components/schemas/Parameter"
```

**Notes:**
- No `required` list: none of `cv_label`, `cv_accession`, `name`, `value` are mandatory at the
  schema level (mirrors JSON Schema validation_policy where none are required).
- `oneOf` cleanly expresses the two valid types without admitting `null` (OpenAPI convention).

---

### 1.2 Add `Protocol` to `components/schemas`

**Location:** insert after `ExtendedParameter`.

```yaml
    Protocol:
      description: >
        A protocol describing one or more steps of an experimental procedure, such as sample
        preparation, data acquisition or data processing. Protocols are referenced from
        Assay objects. Added in mzTab-M 2.1.
      x-mztab-example: |
        MTD	protocol[1]	extraction
        MTD	protocol[1]-type	[MSIO, MSIO:0000141, metabolite extraction,]
        MTD	protocol[1]-description	Extraction using 80% methanol
        MTD	protocol[1]-parameter[1]	[MSIO, MSIO:0000107, quenching, [MSIO, MSIO:0000109, liquid nitrogen,]]
      x-mztab-serialize-by-id: "true"
      type: object
      required:
        - name
        - type
      properties:
        id:
          type: integer
          format: int32
          minimum: 1
        name:
          type: string
          description: The protocol name (serves as its plain-text identifier in the MTD section).
        type:
          $ref: "#/components/schemas/Parameter"
          description: The protocol type, as a CV or user parameter.
        description:
          type: string
          description: A free-text description of the protocol.
        parameters:
          type: array
          default: []
          description: >
            Parameters that further describe the protocol. Each parameter may carry a
            plain-string value or a nested Parameter (ExtendedParameter).
          items:
            $ref: "#/components/schemas/ExtendedParameter"
```

**Notes:**
- `name` and `type` are required (matching `validation_policy.required: true` in JSON Schema).
- `description` and `parameters` are optional.

---

## Phase 2 — Add missing fields to existing types

### 2.1 `Metadata` — add `protocol` array

**Location:** inside `Metadata.properties`, after the `colunit-small_molecule_evidence` block
(before the closing of the `Metadata` schema, around line 872).

```yaml
        protocol:
          type: array
          description: >
            Experimental protocols referenced by assays. Each protocol describes one or
            more steps of the experimental procedure (e.g. sample preparation, data
            acquisition). Protocols are numbered [1-n] and referenced from assay objects
            via protocol_refs. Added in mzTab-M 2.1.
          default: []
          items:
            $ref: "#/components/schemas/Protocol"
          x-mztab-example: |
            MTD	protocol[1]	extraction
            MTD	protocol[1]-type	[MSIO, MSIO:0000141, metabolite extraction,]
            MTD	protocol[2]	acquisition
            MTD	protocol[2]-type	[MSIO, MSIO:0000031, mass spectrometry,]
```

**Notes:**
- Do **not** add `protocol` to `Metadata.required` — it is optional (`validation_policy.required`
  is `null` in JSON Schema).

---

### 2.2 `Assay` — add `protocol_refs` and `parameters`

**Location:** inside `Assay.properties`, after the existing `ms_run_ref` field.

```yaml
        protocol_refs:
          type: array
          default: []
          description: >
            References to the protocols that were applied in this assay. Multiple protocols
            may be referenced. Each entry must correspond to a protocol defined in the
            metadata section. Added in mzTab-M 2.1.
          items:
            $ref: "#/components/schemas/Protocol"
          x-mztab-example: |
            MTD	assay[1]-protocol_ref	protocol[1]| protocol[2]
        parameters:
          type: array
          default: []
          description: >
            Additional parameters describing this assay (e.g. acquisition parameters). Each
            parameter's value may itself be a CV term (ExtendedParameter). Added in
            mzTab-M 2.1.
          items:
            $ref: "#/components/schemas/ExtendedParameter"
          x-mztab-example: |
            MTD	assay[1]-parameter[1]	[MS, MS:1000031, instrument model, [MS, MS:1000449, LTQ Orbitrap,]]
```

**Notes:**
- Neither field is added to `Assay.required` — both have `validation_policy.required: null`
  in the JSON Schema.

---

### 2.3 `MsRun` — add `parameters`

**Location:** inside `MsRun.properties`, after `hash_method`.

```yaml
        parameters:
          type: array
          default: []
          description: >
            Additional parameters describing this MS run (e.g. acquisition mode, ion
            mobility settings). Each parameter's value may itself be a CV term
            (ExtendedParameter). Added in mzTab-M 2.1.
          items:
            $ref: "#/components/schemas/ExtendedParameter"
          x-mztab-example: |
            MTD	ms_run[1]-parameter[1]	[MS, MS:1000031, instrument model, [MS, MS:1000449, LTQ Orbitrap,]]
```

**Notes:**
- Not added to `MsRun.required` — `validation_policy.required: null`.

---

### 2.4 `StudyVariable` — add `ms_run_refs`

**Location:** inside `StudyVariable.properties`, after the existing `description` field.

```yaml
        ms_run_refs:
          type: array
          default: []
          description: >
            References to the MS runs directly associated with this study variable, in
            addition to those reachable via assay_refs. Added in mzTab-M 2.1.
          items:
            $ref: "#/components/schemas/MsRun"
          x-mztab-example: |
            MTD	study_variable[1]-ms_run_ref	ms_run[1]| ms_run[2]
```

**Notes:**
- `ms_run_refs` is not added to `StudyVariable.required`.
- `factors` was present in `mztabm.schema-2.1.0-M.json` but was removed from the mzTab-M
  2.1 specification prior to finalisation. The JSON Schema has not yet been updated to
  reflect this removal. Do **not** add `factors` to the OpenAPI definition.

---

## Phase 3 — Naming alignment

### 3.1 `StudyVariable.group_ref` → `group_refs` (singular → plural array)

**Current OpenAPI:** `group_ref: $ref StudyVariableGroup` (single object).  
**JSON Schema:** `group_refs: array of integer` (multiple groups).

**Decision required — two options:**

| Option | Change | Impact |
|---|---|---|
| **A — align with JSON Schema** | Rename `group_ref` to `group_refs`, change type to `array of $ref StudyVariableGroup` | Breaking change; generator code and existing JSON files using `group_ref` must be updated |
| **B — document intentional simplification** | Keep `group_ref` (single object), add an `x-mztab-note` explaining the simplification | No breaking change; JSON Schema diverges intentionally |

**Recommendation:** Choose **Option A**. The JSON Schema is the authoritative data model.
Multi-group membership is a valid 2.1.0-M feature. Code-generators can handle the rename.

**Change to make (Option A):**

In `StudyVariable.properties`, replace:
```yaml
        group_ref:
          $ref: "#/components/schemas/StudyVariableGroup"
          description: Reference to the study_variable_group that this study variable belongs to. This field is mandatory if study_variable_group(s) are defined.
```
with:
```yaml
        group_refs:
          type: array
          default: []
          description: >
            References to the study_variable_group(s) that this study variable belongs to.
            A study variable may belong to more than one group in multi-factorial designs.
            This field is mandatory if study_variable_group(s) are defined.
          items:
            $ref: "#/components/schemas/StudyVariableGroup"
          x-mztab-example: |
            MTD	study_variable[1]-group_ref	study_variable_group[1]| study_variable_group[2]
```

---

### 3.2 `StudyVariableGroup.parameter` → `name`

**Current OpenAPI:** property is called `parameter` (type `$ref Parameter`), listed in `required`.  
**JSON Schema:** property is called `name` (type `$ref Parameter`), `validation_policy.required: true`.

Both schemas hold the same concept: the CV or user parameter that defines the group (e.g.
`[PATO, PATO:0000383, sex, ]`). The names differ.

The mzTab-M MTD line reads: `MTD study_variable_group[1] [PATO, PATO:0000383, sex, ]` — the
group is defined by a parameter that acts as a *name*. JSON Schema's choice of `name` is more
aligned with the serialization format.

**Decision required — two options:**

| Option | Change | Impact |
|---|---|---|
| **A — rename to `name`** | Replace `parameter` with `name` in properties and required list | Breaking change for code-generators and existing JSON files |
| **B — keep `parameter`** | Add `x-mztab-note` documenting the name difference | No breaking change; permanent divergence from JSON Schema |

**Recommendation:** Choose **Option A**. The JSON Schema is authoritative and `name` better
reflects the serialization semantics (it is the top-level value of the MTD entry).

**Change to make (Option A):**

In `StudyVariableGroup`, replace:
```yaml
      required:
        - id
        - parameter
        - description
      properties:
        ...
        parameter:
          $ref: "#/components/schemas/Parameter"
          description: A CV or user parameter defining the study variable group.
```
with:
```yaml
      required:
        - id
        - name
        - description
      properties:
        ...
        name:
          $ref: "#/components/schemas/Parameter"
          description: >
            A CV or user parameter defining the study variable group (e.g.
            [PATO, PATO:0000383, sex, ]). Corresponds to the top-level value of
            the MTD study_variable_group[n] line.
```

Also update the `Metadata.study_variable_group` description block where it mentions
`(empty) parameter:` — change that to `(empty) name:` to stay consistent.

---

## Phase 4 — Validation constraint corrections

### 4.1 `StudyVariableGroup.datatype` — add enum constraint

**Current OpenAPI:** `type: string` (unconstrained).  
**JSON Schema:** enforces exactly 8 XSD datatypes.

**Change:** replace the plain `type: string` for `datatype` with a constrained enum:

```yaml
        datatype:
          type: string
          description: >
            The datatype of the group variable, used to disambiguate how the associated
            values are encoded and parsed in mzTab-M files. Optional, but producers of
            mzTab-M 2.1.0 SHOULD provide a value. Date, time and dateTime values MUST be
            encoded in ISO 8601 format.
          enum:
            - xsd:string
            - xsd:integer
            - xsd:decimal
            - xsd:boolean
            - xsd:date
            - xsd:time
            - xsd:dateTime
            - xsd:anyURI
```

---

### 4.2 `SmallMoleculeFeature.sme_id_ref_ambiguity_code` — add range constraint

**Current OpenAPI:** `type: integer, format: int32` (no bounds).  
**JSON Schema:** `minimum: 1, maximum: 3`.

The ambiguity code encodes three distinct states: 1 = no ambiguity, 2 = ambiguous removal
of a redundant row, 3 = ambiguous ms2 spectra. Values outside 1–3 are meaningless.

**Change:** add `minimum` and `maximum` to `sme_id_ref_ambiguity_code`:

```yaml
        sme_id_ref_ambiguity_code:
          type: integer
          format: int32
          minimum: 1
          maximum: 3
          description: >
            ...existing description...
```

---

### 4.3 `SmallMoleculeFeature` — add `charge` to `required`

**Current OpenAPI:** `required: [smf_id, exp_mass_to_charge]`.  
**JSON Schema:** `charge` has `validation_policy.required: true`.

`charge` is an essential property for any measured MS feature (it defines the charge state).

**Change:** update `SmallMoleculeFeature.required`:

```yaml
      required:
        - smf_id
        - exp_mass_to_charge
        - charge
```

---

### 4.4 `SmallMoleculeEvidence.spectra_ref` — add `minItems: 1`

**Current OpenAPI:** `type: array, default: []` (no minimum count constraint).  
**JSON Schema:** `minimum: 1` on the `spectra_ref` array.

`spectra_ref` is required (`required: [... spectra_ref ...]`) and must have at least one
entry, because evidence without any spectral reference is not valid.

**Change:** add `minItems: 1` to `SmallMoleculeEvidence.spectra_ref`:

```yaml
        spectra_ref:
          type: array
          minItems: 1
          ...existing items/description...
```

---

### 4.5 `MzTab.smallMoleculeFeature` and `MzTab.smallMoleculeEvidence` — add `minItems: 1`

**Current OpenAPI:** `smallMoleculeSummary` has `minItems: 1`; the other two tables do not.  
**JSON Schema:** all three table arrays are `required: true`.

Both `smallMoleculeFeature` and `smallMoleculeEvidence` are listed in `MzTab.required`. If
they are required to be present, they should also require at least one row.

**Change:** add `minItems: 1` to both:

```yaml
        smallMoleculeFeature:
          type: array
          default: []
          minItems: 1
          ...
        smallMoleculeEvidence:
          type: array
          default: []
          minItems: 1
          ...
```

---

## Phase 5 — Housekeeping

### 5.1 Remove `fileDescription` from `Metadata.required`

`fileDescription` appears in `Metadata.required` but is defined as a property in neither
the JSON Schema nor the OpenAPI schema. It is a stale entry with no backing definition.

**Change:** remove `- fileDescription` from `Metadata.required`. The list becomes:

```yaml
      required:
        - prefix
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

---

### 5.2 Bump `info.version` to `2.1.0-M`

**Change:**
```yaml
info:
  version: 2.1.0-M
```

---

### 5.3 Update `mzTab-version` example in `Metadata`

The current `x-mztab-example` for `Metadata.mzTab-version` shows only `2.0.0-M` and
`2.0.1-M`. Add `2.1.0-M`.

---

## Phase 6 — Deferred / needs decision

These items require an explicit design decision before they can be implemented.

| Item | Current state | JSON Schema state | Recommendation |
|---|---|---|---|
| `StudyVariable.group_ref` vs `group_refs` | singular `$ref` | plural integer array | Change to `group_refs: array` (Phase 3.1 above — confirm first) |
| `StudyVariableGroup.parameter` vs `name` | field called `parameter` | field called `name` | Rename to `name` (Phase 3.2 above — confirm first) |
| `Parameter.name` + `Parameter.value` required | both in `required` | neither in `required` | Keep OpenAPI's stricter rule (more consistent API contracts); do not loosen |
| `MsRun.id` in `required` | yes | `ignore: true` | Keep in OpenAPI `required` — `id` is needed for embedded-object round-tripping |
| `Database.prefix` + `Database.uri` enforcement | both required | enforcement_level: recommended | Keep required in OpenAPI — stricter but safer for API consumers |
| `SampleProcessing.sampleProcessing` vs `sample_processing` | camelCase | snake_case | Intentional divergence; annotate with `x-mztab-field-name: sample_processing` |
| `Publication.publicationItems` vs `publication_items` | camelCase | snake_case | Same as above |

---

## Summary checklist

| # | Phase | Change | Breaking? |
|---|---|---|---|
| 1 | Types | Add `ExtendedParameter` schema | No |
| 2 | Types | Add `Protocol` schema | No |
| 3 | Fields | Add `Metadata.protocol` (array of Protocol) | No |
| 4 | Fields | Add `Assay.protocol_refs` (array of Protocol) | No |
| 5 | Fields | Add `Assay.parameters` (array of ExtendedParameter) | No |
| 6 | Fields | Add `MsRun.parameters` (array of ExtendedParameter) | No |
| 7 | Fields | Add `StudyVariable.ms_run_refs` (array of MsRun) | No |
| 8 | Naming | Rename `StudyVariable.group_ref` → `group_refs` (array) | **Yes** |
| 9 | Naming | Rename `StudyVariableGroup.parameter` → `name` | **Yes** |
| 10 | Naming | Update `Metadata` description: `(empty) parameter:` → `(empty) name:` | No |
| 11 | Validation | Add `StudyVariableGroup.datatype` enum (8 XSD types) | No |
| 12 | Validation | Add `minimum: 1, maximum: 3` to `SmallMoleculeFeature.sme_id_ref_ambiguity_code` | No |
| 13 | Validation | Add `charge` to `SmallMoleculeFeature.required` | No |
| 14 | Validation | Add `minItems: 1` to `SmallMoleculeEvidence.spectra_ref` | No |
| 15 | Validation | Add `minItems: 1` to `MzTab.smallMoleculeFeature` | No |
| 16 | Validation | Add `minItems: 1` to `MzTab.smallMoleculeEvidence` | No |
| 17 | Housekeeping | Remove `fileDescription` from `Metadata.required` | No |
| 18 | Housekeeping | Bump `info.version` to `2.1.0-M` | No |
| 19 | Housekeeping | Update `mzTab-version` example to include `2.1.0-M` | No |

Items 8 and 9 are the only **breaking changes** and should be implemented together in a
single commit once the renaming decision is confirmed.

> **Note — `factors` in JSON Schema:** `StudyVariable.factors` appears in
> `mztabm.schema-2.1.0-M.json` but was removed from the mzTab-M 2.1 specification before
> finalisation. The JSON Schema has not yet been updated. It must **not** be added to the
> OpenAPI definition and should be removed from the JSON Schema in a follow-up cleanup.
