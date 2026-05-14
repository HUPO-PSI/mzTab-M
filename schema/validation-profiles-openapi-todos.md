# Validation Profile Support — OpenAPI Design Options

## Context

The `/validate` and `/validatePlain` endpoints each consume the entire request body
for the mzTab payload. Adding an optional `validation_profile` alongside requires
a deliberate design choice because a second payload cannot simply be appended.

---

## Option A — Multipart form-data (Recommended)

Add `multipart/form-data` as an **additional** content type on both endpoints.
Existing `application/json`, `application/xml`, and `text/tab-separated-values`
callers are unaffected; callers that want a profile switch to multipart.

**Request shape (`/validate`):**

```
POST /validate
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="mztab"
Content-Type: application/json
{ ... MzTab object ... }

--boundary
Content-Disposition: form-data; name="validation_profile"
Content-Type: application/json   (or application/xml)
{ "name": "metabolights-strict", "checks": [...] }
--boundary--
```

**Request shape (`/validatePlain`):**

```
POST /validatePlain
Content-Type: multipart/form-data

--boundary
Content-Disposition: form-data; name="mztab"
Content-Type: text/tab-separated-values
MTD  mzTab-version  2.1.0-M
...

--boundary
Content-Disposition: form-data; name="validation_profile"
Content-Type: application/json
{ "name": "default" }
--boundary--
```

**Trade-offs:**

| | |
|---|---|
| ✅ | Fully backward compatible — existing content types unchanged |
| ✅ | Standard HTTP pattern for multi-payload POSTs |
| ✅ | Profile can be arbitrary JSON or XML (not limited to server-side catalogue) |
| ⚠️ | Slightly more complex client code |
| ⚠️ | Some OpenAPI code generators handle multipart less cleanly than pure JSON bodies |

**OpenAPI changes required:**

- Add `multipart/form-data` entry to `requestBody.content` on `/validate` and `/validatePlain`
- Add `ValidationProfile` to `components/schemas`

---

## Option B — Named profile as a query parameter

Add an optional `validationProfile` string query parameter referencing a
server-registered named profile. No body change needed.

```
POST /validate?validationProfile=metabolights-strict
Content-Type: application/json
{ ... MzTab object ... }
```

**Trade-offs:**

| | |
|---|---|
| ✅ | Dead simple, zero client migration |
| ✅ | Fully backward compatible |
| ✅ | Works identically for both `/validate` and `/validatePlain` |
| ❌ | Profile must be pre-registered server-side; clients cannot upload custom profiles |
| ❌ | No schema validation of the profile itself |

**OpenAPI changes required:**

- Add `validationProfile` query parameter to `/validate` and `/validatePlain`

---

## Option C — Wrapper request body (breaking)

Replace the `/validate` body with a new `ValidatedMzTab` wrapper schema:

```json
{
  "mztab": { "...MzTab object..." },
  "validation_profile": { "...ValidationProfile object..." }
}
```

**Trade-offs:**

| | |
|---|---|
| ✅ | Clean single-body design |
| ✅ | Full schema validation of both payloads |
| ❌ | Breaking change — all existing `/validate` clients must be updated |
| ❌ | `/validatePlain` still needs a separate solution (multipart or query param) |

**OpenAPI changes required:**

- New `ValidatedMzTab` wrapper schema in `components/schemas`
- Replace `requestBody` on `/validate` with the wrapper schema
- Separate solution still needed for `/validatePlain`

---

## Recommendation

**Implement Option A** (multipart) as the primary mechanism, and **also add Option B**
(query parameter) for the common case of selecting a well-known named profile.
This gives clients maximum flexibility without any breaking changes:

- Simple use case: `?validationProfile=default`
- Custom profile: multipart body with a `validation_profile` part

---

## Enforcement vs. Level — Two Orthogonal Axes

Every check has two independent severity fields:

| Field | Role | Required |
|---|---|---|
| `enforcement` | RFC 2119 condition from the mzTab-M specification. Determines the **default** report level. | yes |
| `level` | Profile override. When present, **replaces** the default level derived from `enforcement`. | no |

**Default level derived from `enforcement`:**

| `enforcement` | RFC 2119 meaning | Default `level` reported on violation |
|---|---|---|
| `MUST` | Unconditional requirement | `error` |
| `SHOULD` | Strong recommendation; hints provided on violation | `warn` |
| `MAY` | Optional; violation hints at improving semantic richness | `info` |

A profile that sets `enforcement: "SHOULD"` with no `level` reports violations as
`warn`. A stricter profile can add `"level": "error"` to upgrade that same check
to `error` without changing the underlying RFC condition.

`"level": "skip"` disables the check entirely regardless of `enforcement`.

---

## Check Types

The `checks` array is a **discriminated union** keyed on `check_type`. Every item
carries these common fields:

| Common field | Required | Description |
|---|---|---|
| `check_type` | yes | Discriminator: `"structural"`, `"type_constraint"`, or `"semantic_cv"` |
| `check_id` | yes | Unique identifier for this check within the profile |
| `enforcement` | yes | RFC 2119 condition: `"MUST"` \| `"SHOULD"` \| `"MAY"` |
| `level` | no | Profile severity override: `"info"` \| `"warn"` \| `"error"` \| `"skip"` |
| `json_path` | yes | RFC 9535 JSONPath array scoping this check to specific document nodes |

---

### Check Type 1 — Structural (`check_type: "structural"`)

Tests **presence or absence** of document nodes selected by `json_path`.

For compound checks (`operator` + `operands`), `enforcement` belongs on the
**check as a whole** — not on individual operands. Operands only specify *what*
to test (`json_path` + `presence`), never *how severely* to report it. The single
`enforcement` (or `level` override) on the enclosing check determines the severity
of the entire expression.

#### Trigger logic

| `operator` | The check fires (reports a violation) when… |
|---|---|
| *(none — simple leaf)* | The `presence` condition on `json_path` is not satisfied |
| `AND` | **Any** operand condition is not satisfied |
| `OR` | **All** operand conditions are not satisfied |
| `XOR` | The number of satisfied operand conditions is **not exactly 1** |

The validator emits **one message per check evaluation**, at the resolved level
(`level` if set, otherwise the default from `enforcement`). For AND failures it
SHOULD list the unsatisfied operand paths in the message to aid diagnosis.

#### Worked example — `database_or_protocol`

```
enforcement: SHOULD  →  default level: warn

OR
├── AND
│   ├── $.metadata.database[*]      present?  → true/false
│   └── $.metadata.database[*].uri  present?  → true/false
└── $.metadata.protocol[*]          present?  → true/false
```

| database present | database.uri present | protocol present | OR result | Reported? |
|---|---|---|---|---|
| yes | yes | — | ✅ AND branch satisfied | no |
| yes | no | — | ❌ AND branch fails; OR continues… | |
| yes | no | yes | ✅ protocol branch satisfied | no |
| yes | no | no | ❌ all branches fail | **warn** |
| no | — | yes | ✅ protocol branch satisfied | no |
| no | — | no | ❌ all branches fail | **warn** |

A profile that needs this to be mandatory instead of a recommendation adds
`"level": "error"`, upgrading violations from `warn` to `error`.

#### Schema — `StructuralCheck`

```json
"StructuralCheck": {
  "type": "object",
  "required": ["check_type", "check_id", "enforcement", "json_path"],
  "properties": {
    "check_type":  { "const": "structural" },
    "check_id":    { "type": "string" },
    "enforcement": { "type": "string", "enum": ["MUST", "SHOULD", "MAY"] },
    "level":       { "type": "string", "enum": ["info", "warn", "error", "skip"],
                     "description": "Overrides the default level derived from enforcement." },
    "json_path":   { "$ref": "#/components/schemas/JsonPathList" },
    "presence":    { "type": "string", "enum": ["present", "absent"],
                     "description": "Required for simple (non-compound) checks." },
    "operator":    { "type": "string", "enum": ["AND", "OR", "XOR"],
                     "description": "Required for compound checks." },
    "operands": {
      "type": "array",
      "minItems": 2,
      "description": "Sub-conditions. Each operand specifies what to test, not how to report it.",
      "items": { "$ref": "#/components/schemas/StructuralOperand" }
    }
  }
}
```

#### Schema — `StructuralOperand` (recursive, no enforcement)

```json
"StructuralOperand": {
  "type": "object",
  "required": ["json_path"],
  "properties": {
    "json_path": { "$ref": "#/components/schemas/JsonPathList" },
    "presence":  { "type": "string", "enum": ["present", "absent"],
                   "description": "Required for leaf operands." },
    "operator":  { "type": "string", "enum": ["AND", "OR", "XOR"],
                   "description": "Required for nested sub-combinations." },
    "operands": {
      "type": "array", "minItems": 2,
      "items": { "$ref": "#/components/schemas/StructuralOperand" }
    }
  }
}
```

#### Examples

```json
// Simple leaf: software MUST be present (default level: error)
{
  "check_type": "structural",
  "check_id": "software_required",
  "enforcement": "MUST",
  "json_path": ["$.metadata.software[*]"],
  "presence": "present"
}

// AND: fires if software OR instrument is absent (default level: error)
{
  "check_type": "structural",
  "check_id": "instrument_and_software_required",
  "enforcement": "MUST",
  "json_path": ["$"],
  "operator": "AND",
  "operands": [
    { "json_path": ["$.metadata.software[*]"],   "presence": "present" },
    { "json_path": ["$.metadata.instrument[*]"], "presence": "present" }
  ]
}

// XOR: fires if both SMF and SME are present, or if neither is present
// (exactly one must be present; default level: warn)
{
  "check_type": "structural",
  "check_id": "smf_xor_sme_evidence",
  "enforcement": "SHOULD",
  "json_path": ["$"],
  "operator": "XOR",
  "operands": [
    { "json_path": ["$.smallMoleculeFeature[*]"],  "presence": "present" },
    { "json_path": ["$.smallMoleculeEvidence[*]"], "presence": "present" }
  ]
}

// OR: fires only when NEITHER branch is satisfied (default level: warn)
// A strict profile can add "level": "error" to upgrade to error.
{
  "check_type": "structural",
  "check_id": "database_or_protocol",
  "enforcement": "SHOULD",
  "json_path": ["$"],
  "operator": "OR",
  "operands": [
    {
      "json_path": ["$"],
      "operator": "AND",
      "operands": [
        { "json_path": ["$.metadata.database[*]"],     "presence": "present" },
        { "json_path": ["$.metadata.database[*].uri"], "presence": "present" }
      ]
    },
    { "json_path": ["$.metadata.protocol[*]"], "presence": "present" }
  ]
}
```

---

### Check Type 2 — Type Constraint (`check_type: "type_constraint"`)

Validates the **data type and format** of matched nodes against a base type
(JSON Schema primitive, XSD type, ISO date/time, URI, or a custom regex pattern).

**Supported `base_type` values:**

| `base_type` | Validated against |
|---|---|
| `string` | JSON string; optional `pattern` (regex) |
| `integer` | JSON integer |
| `number` | JSON number |
| `boolean` | JSON boolean |
| `date` | ISO 8601 date (`YYYY-MM-DD`) |
| `datetime` | ISO 8601 date-time |
| `timestamp` | Unix epoch (integer seconds) |
| `uri` | RFC 3986 URI syntax |
| `json_schema` | Full JSON Schema at `schema_ref` |
| `xsd` | XSD built-in type named by `xsd_type` |

**Schema — `TypeConstraintCheck`:**

```json
"TypeConstraintCheck": {
  "type": "object",
  "required": ["check_type", "check_id", "enforcement", "json_path", "base_type"],
  "properties": {
    "check_type":  { "const": "type_constraint" },
    "check_id":    { "type": "string" },
    "enforcement": { "type": "string", "enum": ["MUST", "SHOULD", "MAY"] },
    "level":       { "type": "string", "enum": ["info", "warn", "error", "skip"],
                     "description": "Overrides the default level derived from enforcement." },
    "json_path":   { "$ref": "#/components/schemas/JsonPathList" },
    "base_type": {
      "type": "string",
      "enum": ["string", "integer", "number", "boolean",
               "date", "datetime", "timestamp", "uri",
               "json_schema", "xsd"]
    },
    "pattern": {
      "type": "string",
      "description": "ECMA-262 regular expression applied when base_type is 'string'."
    },
    "schema_ref": {
      "type": "string", "format": "uri",
      "description": "URI of an external JSON Schema document. Required when base_type is 'json_schema'."
    },
    "xsd_type": {
      "type": "string",
      "description": "XSD built-in type name, e.g. 'xsd:decimal', 'xsd:date'. Required when base_type is 'xsd'.",
      "examples": ["xsd:decimal", "xsd:date", "xsd:anyURI", "xsd:positiveInteger"]
    }
  }
}
```

**Examples:**

```json
// mzTab-version MUST match the version pattern (default level: error)
{
  "check_type": "type_constraint",
  "check_id": "version_format",
  "enforcement": "MUST",
  "json_path": ["$.metadata.mzTab-version"],
  "base_type": "string",
  "pattern": "^\\d+\\.\\d+\\.\\d+-[A-Z]+$"
}

// database URI MUST be a valid URI (default level: error)
{
  "check_type": "type_constraint",
  "check_id": "database_uri_format",
  "enforcement": "MUST",
  "json_path": ["$.metadata.database[*].uri"],
  "base_type": "uri"
}

// exp_mass_to_charge MUST be an xsd:decimal (default level: error)
{
  "check_type": "type_constraint",
  "check_id": "mass_to_charge_decimal",
  "enforcement": "MUST",
  "json_path": [
    "$.smallMoleculeFeature[*].exp_mass_to_charge",
    "$.smallMoleculeEvidence[*].theoretical_mass_to_charge"
  ],
  "base_type": "xsd",
  "xsd_type": "xsd:decimal"
}

// confidence value SHOULD conform to external schema (default level: warn)
// A strict profile can add "level": "error" to upgrade violations.
{
  "check_type": "type_constraint",
  "check_id": "confidence_value_schema",
  "enforcement": "SHOULD",
  "json_path": ["$.smallMoleculeEvidence[*].best_id_confidence_value"],
  "base_type": "json_schema",
  "schema_ref": "https://example.org/schemas/confidence_value.json"
}
```

---

### Check Type 3 — Semantic CV (`check_type: "semantic_cv"`)

Validates that matched nodes contain an `ExtendedParameter` whose CV accession is
drawn from a permitted set of terms or term roots. The CV itself MUST be declared
in the mzTab-M `MTD cv[n]` metadata section.

**Term scope options:**

| Option | Meaning |
|---|---|
| neither flag | Only the exact accession is allowed |
| `allow_children: true` | The accession and its direct children are allowed |
| `allow_descendants: true` | The accession and all transitive descendants are allowed |

Compound constraints combine multiple `CVTermConstraint` operands with `AND`,
`OR`, or `XOR`.

**Schema — `SemanticCVCheck`:**

```json
"SemanticCVCheck": {
  "type": "object",
  "required": ["check_type", "check_id", "enforcement", "json_path", "constraint"],
  "properties": {
    "check_type":  { "const": "semantic_cv" },
    "check_id":    { "type": "string" },
    "enforcement": { "type": "string", "enum": ["MUST", "SHOULD", "MAY"] },
    "level":       { "type": "string", "enum": ["info", "warn", "error", "skip"],
                     "description": "Overrides the default level derived from enforcement." },
    "json_path":  { "$ref": "#/components/schemas/JsonPathList" },
    "constraint": {
      "oneOf": [
        { "$ref": "#/components/schemas/CVTermConstraint" },
        { "$ref": "#/components/schemas/CVCombinationConstraint" }
      ]
    }
  }
}
```

**Schema — `CVTermConstraint`:**

```json
"CVTermConstraint": {
  "type": "object",
  "required": ["cv_ref", "allowed_terms"],
  "properties": {
    "cv_ref": {
      "type": "string",
      "description": "Label of the CV as declared in MTD cv[n]-label, e.g. 'MS', 'CHEBI', 'BTO'."
    },
    "allowed_terms": {
      "type": "array",
      "minItems": 1,
      "description": "One or more permitted term roots. An empty allowed_terms list means no term from this CV is acceptable.",
      "items": {
        "type": "object",
        "required": ["accession"],
        "properties": {
          "accession": {
            "type": "string",
            "description": "CV term accession, e.g. 'MS:1000031'."
          },
          "allow_children": {
            "type": "boolean", "default": false,
            "description": "Also accept direct child terms of this accession."
          },
          "allow_descendants": {
            "type": "boolean", "default": false,
            "description": "Also accept all transitive descendant terms."
          }
        }
      }
    }
  }
}
```

**Schema — `CVCombinationConstraint`** (recursive):

```json
"CVCombinationConstraint": {
  "type": "object",
  "required": ["operator", "operands"],
  "properties": {
    "operator": { "type": "string", "enum": ["AND", "OR", "XOR"] },
    "operands": {
      "type": "array", "minItems": 2,
      "items": {
        "oneOf": [
          { "$ref": "#/components/schemas/CVTermConstraint" },
          { "$ref": "#/components/schemas/CVCombinationConstraint" }
        ]
      }
    }
  }
}
```

**Examples:**

```json
// Instrument name MUST be an MS:1000031 (instrument model) or any child term
// (default level: error)
{
  "check_type": "semantic_cv",
  "check_id": "instrument_model_cv",
  "enforcement": "MUST",
  "json_path": ["$.metadata.instrument[*].name"],
  "constraint": {
    "cv_ref": "MS",
    "allowed_terms": [
      { "accession": "MS:1000031", "allow_children": true }
    ]
  }
}

// Fragmentation method SHOULD be CID, HCD, or ETD (exact terms)
// (default level: warn; a strict profile can add "level": "error")
{
  "check_type": "semantic_cv",
  "check_id": "fragmentation_method_allowed",
  "enforcement": "SHOULD",
  "json_path": ["$.metadata.ms_run[*].fragmentation_method[*]"],
  "constraint": {
    "cv_ref": "MS",
    "allowed_terms": [
      { "accession": "MS:1000133" },
      { "accession": "MS:1000422" },
      { "accession": "MS:1000598" }
    ]
  }
}

// Sample MUST carry both a species term (NCBITaxon) AND a tissue term (BTO)
// AND fires when either cv_ref constraint is not satisfied (default level: error)
{
  "check_type": "semantic_cv",
  "check_id": "sample_species_and_tissue",
  "enforcement": "MUST",
  "json_path": ["$.metadata.sample[*]"],
  "constraint": {
    "operator": "AND",
    "operands": [
      {
        "cv_ref": "NCBITaxon",
        "allowed_terms": [
          { "accession": "NCBITaxon:1", "allow_descendants": true }
        ]
      },
      {
        "cv_ref": "BTO",
        "allowed_terms": [
          { "accession": "BTO:0000000", "allow_descendants": true }
        ]
      }
    ]
  }
}

// Quantification unit SHOULD come from exactly one of UO or CHEBI (XOR)
// XOR fires if both CVs are used simultaneously, or if neither matches
// (default level: warn)
{
  "check_type": "semantic_cv",
  "check_id": "quant_unit_cv",
  "enforcement": "SHOULD",
  "json_path": [
    "$.metadata.small_molecule-quantification_unit",
    "$.metadata.small_molecule_feature-quantification_unit"
  ],
  "constraint": {
    "operator": "XOR",
    "operands": [
      {
        "cv_ref": "UO",
        "allowed_terms": [
          { "accession": "UO:0000000", "allow_descendants": true }
        ]
      },
      {
        "cv_ref": "CHEBI",
        "allowed_terms": [
          { "accession": "CHEBI:24431", "allow_descendants": true }
        ]
      }
    ]
  }
}
```

---

## Shared Sub-Schema — `JsonPathList`

Used by all three check types:

```json
"JsonPathList": {
  "type": "array",
  "minItems": 1,
  "description": "One or more RFC 9535 JSONPath expressions evaluated against the root MzTab JSON document. Multiple expressions are ORed: the check is applied to every node matched by any expression.",
  "items": {
    "type": "string",
    "examples": [
      "$",
      "$.metadata.mzTab-version",
      "$.metadata.software[*]",
      "$.metadata.instrument[*]",
      "$.metadata.sample[*]",
      "$.metadata.ms_run[*].fragmentation_method[*]",
      "$.metadata.database[*].uri",
      "$.metadata.small_molecule-quantification_unit",
      "$.smallMoleculeSummary[*].database_identifier",
      "$.smallMoleculeFeature[*].exp_mass_to_charge",
      "$.smallMoleculeEvidence[*].spectra_ref",
      "$.smallMoleculeEvidence[*].best_id_confidence_value"
    ]
  }
}
```

---

## Updated `ValidationProfile` Schema

```json
"ValidationProfile": {
  "type": "object",
  "description": "Overrides or extends the default rule set applied during mzTab-M validation.",
  "required": ["name"],
  "properties": {
    "name": {
      "type": "string",
      "description": "Identifier for this profile, e.g. 'metabolights-strict'."
    },
    "description": {
      "type": "string",
      "description": "Human-readable description of the profile's intent."
    },
    "level": {
      "type": "string",
      "enum": ["info", "warn", "error"],
      "default": "info",
      "description": "Fallback report level for checks not matched by any entry in 'checks'."
    },
    "required_sections": {
      "type": "array",
      "description": "mzTab-M sections that MUST be present for this profile to pass.",
      "items": { "type": "string", "enum": ["MTD", "SML", "SMF", "SME"] }
    },
    "checks": {
      "type": "array",
      "description": "Ordered list of typed validation checks.",
      "items": {
        "oneOf": [
          { "$ref": "#/components/schemas/StructuralCheck" },
          { "$ref": "#/components/schemas/TypeConstraintCheck" },
          { "$ref": "#/components/schemas/SemanticCVCheck" }
        ],
        "discriminator": {
          "propertyName": "check_type",
          "mapping": {
            "structural":       "#/components/schemas/StructuralCheck",
            "type_constraint":  "#/components/schemas/TypeConstraintCheck",
            "semantic_cv":      "#/components/schemas/SemanticCVCheck"
          }
        }
      }
    }
  }
}
```

---

## Full Example Profile

```json
{
  "name": "metabolights-strict",
  "description": "MetaboLights submission profile — enforces instrument annotation, species/tissue ontology terms, version format, and evidence linkage.",
  "level": "warn",
  "required_sections": ["MTD", "SML", "SMF", "SME"],
  "checks": [
    {
      "check_type": "structural",
      "check_id": "software_and_instrument_required",
      "enforcement": "MUST",
      "json_path": ["$"],
      "operator": "AND",
      "operands": [
        { "json_path": ["$.metadata.software[*]"],   "presence": "present" },
        { "json_path": ["$.metadata.instrument[*]"], "presence": "present" }
      ]
    },
    {
      "check_type": "structural",
      "check_id": "spectra_ref_present_in_sme",
      "enforcement": "MUST",
      "json_path": ["$.smallMoleculeEvidence[*].spectra_ref"],
      "presence": "present"
    },
    {
      "check_type": "structural",
      "check_id": "database_or_protocol",
      "enforcement": "SHOULD",
      "json_path": ["$"],
      "operator": "OR",
      "operands": [
        {
          "json_path": ["$"],
          "operator": "AND",
          "operands": [
            { "json_path": ["$.metadata.database[*]"],     "presence": "present" },
            { "json_path": ["$.metadata.database[*].uri"], "presence": "present" }
          ]
        },
        { "json_path": ["$.metadata.protocol[*]"], "presence": "present" }
      ]
    },
    {
      "check_type": "type_constraint",
      "check_id": "version_pattern",
      "enforcement": "MUST",
      "json_path": ["$.metadata.mzTab-version"],
      "base_type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+-[A-Z]+$"
    },
    {
      "check_type": "type_constraint",
      "check_id": "database_uri_valid",
      "enforcement": "MUST",
      "json_path": ["$.metadata.database[*].uri"],
      "base_type": "uri"
    },
    {
      "check_type": "type_constraint",
      "check_id": "mass_to_charge_decimal",
      "enforcement": "MUST",
      "json_path": [
        "$.smallMoleculeFeature[*].exp_mass_to_charge",
        "$.smallMoleculeEvidence[*].theoretical_mass_to_charge"
      ],
      "base_type": "xsd",
      "xsd_type": "xsd:decimal"
    },
    {
      "check_type": "semantic_cv",
      "check_id": "instrument_model_ms_cv",
      "enforcement": "MUST",
      "json_path": ["$.metadata.instrument[*].name"],
      "constraint": {
        "cv_ref": "MS",
        "allowed_terms": [
          { "accession": "MS:1000031", "allow_children": true }
        ]
      }
    },
    {
      "check_type": "semantic_cv",
      "check_id": "sample_species_and_tissue",
      "enforcement": "MUST",
      "json_path": ["$.metadata.sample[*]"],
      "constraint": {
        "operator": "AND",
        "operands": [
          {
            "cv_ref": "NCBITaxon",
            "allowed_terms": [{ "accession": "NCBITaxon:1", "allow_descendants": true }]
          },
          {
            "cv_ref": "BTO",
            "allowed_terms": [{ "accession": "BTO:0000000", "allow_descendants": true }]
          }
        ]
      }
    },
    {
      "check_type": "semantic_cv",
      "check_id": "fragmentation_method_allowed",
      "enforcement": "SHOULD",
      "json_path": ["$.metadata.ms_run[*].fragmentation_method[*]"],
      "constraint": {
        "cv_ref": "MS",
        "allowed_terms": [
          { "accession": "MS:1000133" },
          { "accession": "MS:1000422" },
          { "accession": "MS:1000598" }
        ]
      }
    }
  ]
}
```

---

## TODO

**API integration**
- [ ] **Option A** — Add `multipart/form-data` to `/validate` and `/validatePlain` request bodies
- [ ] **Option B** — Add `validationProfile` query parameter to `/validate` and `/validatePlain`
- [ ] Add all new schemas (`ValidationProfile`, `StructuralCheck`, `TypeConstraintCheck`, `SemanticCVCheck`, `StructuralOperand`, `CVTermConstraint`, `CVCombinationConstraint`, `JsonPathList`) to `components/schemas` in `mzTab_2_1-M_openapi.json`
- [ ] Decide whether the `validation_profile` multipart part accepts `application/xml` in addition to `application/json`

**Profile catalogue**
- [ ] Define built-in named profiles (e.g. `default`, `metabolights-strict`, `minimal`)
- [ ] Document how server-side named profiles relate to the inline `ValidationProfile` schema (same structure? a named subset?)
- [ ] Update `ValidationMessage` to include `check_id` and `json_path_match` fields so callers can correlate messages back to the specific check and the matched node

**Structural checks**
- [ ] Confirm RFC 2119 keyword set is `MUST` / `SHOULD` / `MAY` (replacing earlier draft's `CAN`)
- [ ] Define short-circuit evaluation order for `AND`/`OR`/`XOR` operands
- [ ] Specify whether AND failure reports one aggregated message or one message per failing operand (current proposal: one message, unsatisfied paths listed diagnostically)
- [ ] Decide maximum nesting depth for `StructuralOperand` recursion (prevent abuse)
- [ ] Clarify whether `presence: "absent"` on a wildcard path (e.g. `$.metadata.protocol[*]`) means zero matches required or that the path itself must not exist

**Type constraint checks**
- [ ] Enumerate the exact XSD built-in types that must be supported (`xsd:decimal`, `xsd:date`, `xsd:anyURI`, `xsd:positiveInteger`, …)
- [ ] Define how `json_schema` validation is performed — inline schema embedding vs. URI fetch with caching
- [ ] Decide handling of `null` values in matched nodes: skip the check, always pass, or always fail

**Semantic CV checks**
- [ ] Specify how the validator resolves `cv_ref` to an ontology: require the label to match exactly one `MTD cv[n]-label`, or allow fuzzy matching
- [ ] Define the ontology lookup mechanism (OLS API, local cache, bundled OBO files) for `allow_children`/`allow_descendants` resolution
- [ ] Decide behaviour when a `cv_ref` is not declared in the document's `MTD cv[n]` section: error, skip, or warn
- [ ] Clarify whether `CVCombinationConstraint` operands are evaluated against the same matched node or independently scoped

**JSONPath evaluation**
- [ ] Decide RFC 9535 strict vs. lax mode (missing intermediate nodes = skip check vs. report error)
- [ ] Clarify whether `json_path` expressions are evaluated against the JSON representation only, or also mapped to the TSV section/column structure for `/validatePlain`
- [ ] Define the maximum number of JSONPath expressions allowed per check to prevent performance abuse
