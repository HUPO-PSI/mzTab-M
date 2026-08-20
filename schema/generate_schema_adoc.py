#!/usr/bin/env python3
"""Generate mzTab_m_schema.adoc from mztabm.schema-2.1.0-M.json

Produces an AsciiDoc reference document describing mzTab-M format elements,
hierarchically ordered by mzTab-M section and element.

Usage:
    python3 generate_schema_adoc.py [--output OUTPUT_FILE]
"""

import json
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SCHEMA_FILE = SCRIPT_DIR / 'mzTab_2_1-M.json'
DEFAULT_OUTPUT = SCRIPT_DIR / 'mzTab_2_1-M_schema.adoc'

# Explicit sub-field ordering for nested objects where schema order
# does not match the specification document order.
# Keys are the $defs names; values are lists of property names in spec order.
# Properties not listed here are appended after in schema order.
SUB_FIELD_ORDER = {
    'Sample': ['name', 'species', 'tissue', 'cell_type', 'disease', 'description', 'custom'],
    'StudyVariable': ['name', 'assay_refs', 'ms_run_refs', 'description',
                      'average_function', 'variation_function'],
    'StudyVariableGroup': ['name', 'description', 'type', 'datatype', 'unit',
                           'study_variable_refs'],
    'MsRun': ['location', 'instrument_ref', 'format', 'id_format',
              'fragmentation_method', 'scan_polarity', 'hash', 'hash_method', 'parameters'],
    'Assay': ['name', 'custom', 'external_uri', 'sample_ref', 'ms_run_ref',
              'protocol_refs', 'parameters'],
}

# Display name overrides for fields whose schema names differ from mzTab column names
DISPLAY_NAME_OVERRIDES = {
    # SML
    'sml_id': 'SML_ID',
    'smf_id_refs': 'SMF_ID_REFS',
    # SMF
    'smf_id': 'SMF_ID',
    'sme_id_refs': 'SME_ID_REFS',
    'sme_id_ref_ambiguity_code': 'SME_ID_REF_ambiguity_code',
    # SME
    'sme_id': 'SME_ID',
    # Optional column
    'opt': 'opt_{identifier}_*',
}

# Fields in SML/SMF/SME that are NOT nullable despite having anyOf with null
NON_NULLABLE_FIELDS = {
    'sml_id', 'smf_id', 'sme_id',
    'exp_mass_to_charge', 'charge', 'theoretical_mass_to_charge',
    'spectra_ref', 'identification_method', 'ms_level', 'rank',
    'evidence_input_id', 'best_id_confidence_value',
}


def load_schema(schema_file: Path) -> dict:
    with open(schema_file) as f:
        return json.load(f)
    return None


def make_anchor(name: str) -> str:
    """Convert a field name to an AsciiDoc anchor (lowercase, no brackets)."""
    anchor = name.replace('[1-n]', '1-n')
    anchor = anchor.replace('[', '').replace(']', '')
    anchor = anchor.replace('{', '').replace('}', '')
    anchor = anchor.replace('*', '')
    return anchor.lower().rstrip('-_')


def get_type_string(prop: dict) -> str:
    """Determine the human-readable type string for a property."""
    vp = prop.get('validation_policy', {})
    value_constraint = vp.get('value_constraint', '')
    anyof = prop.get('anyOf', [])

    # Direct $ref (not inside anyOf)
    if '$ref' in prop:
        return ref_to_type(prop['$ref'].split('/')[-1])

    # Check anyOf for array type first (to detect lists)
    for a in anyof:
        if a.get('type') == 'array':
            items = a.get('items', {})
            return array_items_to_type(items, vp)

    # Direct $ref inside anyOf
    for a in anyof:
        if '$ref' in a:
            return ref_to_type(a['$ref'].split('/')[-1])

    # Simple scalar types inside anyOf (skip null entries)
    for a in anyof:
        t = a.get('type')
        if t == 'null':
            continue
        if t == 'string':
            pattern = vp.get('pattern') or a.get('pattern') or prop.get('pattern', '')
            if value_constraint == 'any-url':
                return 'URI'
            if pattern:
                return 'Regex'
            return 'String'
        elif t == 'integer':
            return 'Integer'
        elif t == 'number':
            return 'Double'
        elif t == 'boolean':
            return 'Boolean'

    return 'String'


def array_items_to_type(items: dict, vp: dict) -> str:
    """Determine the type string for an array by examining its items' schema."""
    if '$ref' in items:
        ref_name = items['$ref'].split('/')[-1]
        if ref_name == 'OptColumnMapping':
            return 'Optional Column'
        if ref_name == 'SpectraReference':
            return 'String List'
        base = ref_to_type(ref_name)
        return f'{base} List'

    item_type = items.get('type')
    pattern = items.get('pattern') or vp.get('pattern', '')

    if item_type == 'integer':
        return 'Integer List'
    if item_type == 'number':
        return 'Double List'
    if item_type == 'string':
        return 'Regex List' if pattern else 'String List'

    # items itself has anyOf (e.g., [{type: number}, {type: null}])
    for sub in items.get('anyOf', []):
        sub_t = sub.get('type')
        if sub_t == 'number':
            return 'Double List'
        if sub_t == 'integer':
            return 'Integer List'
        if sub_t == 'string':
            return 'Regex List' if sub.get('pattern') or pattern else 'String List'

    return 'String List'


def ref_to_type(ref_name: str) -> str:
    """Map a JSON $defs reference name to a human-readable type label."""
    mapping = {
        'Parameter': 'Parameter',
        'ExtendedParameter': 'Parameter',
        'CV': 'CV',
        'Assay': 'Assay',
        'Contact': 'Contact',
        'Database': 'Database',
        'Instrument': 'Instrument',
        'MsRun': 'MS Run',
        'Sample': 'Sample',
        'Software': 'Software',
        'Protocol': 'Protocol',
        'SampleProcessing': 'Parameter List',
        'StudyVariable': 'Study Variable',
        'StudyVariableGroup': 'Study Variable Group',
        'Publication': 'Publication',
        'PublicationItem': 'String',
        'Uri': 'URI',
        'ColumnParameterMapping': 'Column Parameter Mapping',
        'SpectraReference': 'String',
        'OptColumnMapping': 'Optional Column',
    }
    return mapping.get(ref_name, ref_name)


def is_mandatory(prop: dict) -> bool:
    """Return True if the field's validation_policy marks it as required."""
    return prop.get('validation_policy', {}).get('required') is True


def field_is_nullable(prop: dict, prop_name: str) -> bool:
    """Determine nullability for SML/SMF/SME fields."""
    if prop_name in NON_NULLABLE_FIELDS:
        return False
    anyof = prop.get('anyOf', [])
    return any(a.get('type') == 'null' for a in anyof)


def get_description(prop: dict) -> str:
    """Return the property description, cleaned up."""
    desc = prop.get('description', '').strip()
    return desc or '_No description available._'


def get_regex_pattern(prop: dict) -> str:
    """Return a regex pattern for the property, checking validation_policy and array items."""
    # Check validation_policy first
    vp_pattern = prop.get('validation_policy', {}).get('pattern', '') or ''
    if vp_pattern:
        return vp_pattern

    # Check inside anyOf for array items pattern
    for a in prop.get('anyOf', []):
        if a.get('type') == 'array':
            items = a.get('items', {})
            item_pattern = items.get('pattern', '') or ''
            if item_pattern:
                return item_pattern
        # Also check direct string entries with pattern
        if a.get('type') == 'string':
            p = a.get('pattern', '') or ''
            if p:
                return p

    return ''


def _is_preformatted(ex: str) -> bool:
    """Return True if the example is already a fully formatted section line.

    Pre-formatted examples start with a recognised section prefix followed by a
    tab character (e.g. 'MTD\t', 'SML\t') and MUST be emitted verbatim.
    """
    prefixes = ('MTD\t', 'SML\t', 'SMH\t', 'SMF\t', 'SFH\t', 'SME\t', 'SEH\t', 'COM\t')
    return any(ex.startswith(p) for p in prefixes)


def _normalize_example(raw) -> str:
    """Convert a raw example value to a display string.

    Nested lists represent multi-value (bar-separated) fields:
      [2, 3, 11]  →  '2|3|11'

    '{BAR}' is the portable placeholder for a literal pipe character in
    schema example strings.  It is replaced with a bare '|' here; pipe
    escaping for AsciiDoc output is handled separately by _escape_pipes()
    at the point where lines are written to the example block.
    Any legacy '\\|' AsciiDoc escaping in the raw data is also normalised
    to bare '|' for the same reason.
    """
    if isinstance(raw, list):
        return '|'.join(_normalize_example(v) for v in raw)
    if isinstance(raw, float):
        # Show without trailing zeros where possible
        return f'{raw:g}'
    result = str(raw)
    result = result.replace('{BAR}', '|').replace('\\|', '|')
    return result


def _escape_pipes(text: str) -> str:
    r"""Escape bare pipe characters as \| for AsciiDoc table cell content.

    Asciidoctor pre-processes \| → | at the table structure level before
    block content is parsed, so this escape is effective inside both ----
    listing blocks and .... passthrough blocks within a| table cells.
    """
    return text.replace('|', '\\|')


def get_examples(prop: dict) -> list:
    """Return up to two normalised example value strings."""
    raw_examples = prop.get('examples') or []
    result = []
    for raw in raw_examples[:2]:
        result.append(_normalize_example(raw))
    return result


def insert_example_blocks(lines: list, examples: dict):
    """Insert example blocks before the closing table delimiter for selected fields."""
    for field_name, example in examples.items():
        marker = f'==== {field_name}'
        start_idx = None
        for idx, line in enumerate(lines):
            if line == marker:
                start_idx = idx
                break
        if start_idx is None:
            continue

        delim_count = 0
        insert_idx = None
        for idx in range(start_idx + 1, len(lines)):
            if lines[idx].strip() == '|============================================================':
                delim_count += 1
                if delim_count == 2:
                    insert_idx = idx
                    break
        if insert_idx is None:
            continue

        block = [
            '|*Example* a|',
            '----',
            example,
            '----',
        ]
        lines[insert_idx:insert_idx] = block


def write_field_entry(
    lines: list,
    field_name: str,
    prop: dict,
    section_prefix: str,
    schema_defs: dict,
    show_nullable: bool = False,
    prop_key: str = '',
    anchor_prefix: str = '',
):
    """Append the AsciiDoc block for a single field to *lines*."""
    anchor = (anchor_prefix + '-' if anchor_prefix else '') + make_anchor(field_name)
    desc = get_description(prop)
    type_str = get_type_string(prop)
    mandatory = is_mandatory(prop)
    pattern = get_regex_pattern(prop)
    examples = get_examples(prop)
    nullable = field_is_nullable(prop, prop_key or field_name)

    lines.append(f'[[{anchor}]]')
    lines.append(f'==== {field_name}')
    lines.append('')
    lines.append('[cols="20,80",]')
    lines.append('|============================================================')

    # Description: use 'a|' literal block if multi-line
    if '\n' in desc:
        lines.append('|*Description* a|')
        lines.append(desc)
    else:
        lines.append(f'|*Description* |{desc}')

    # Type: show regex pattern in a listing block when applicable.
    # Use ---- (listing block) rather than .... (literal block) so that any
    # pipe characters in the pattern are not mis-parsed as table cell
    # separators by Asciidoctor.js inside an "a"| table cell.
    if pattern and 'Regex' in type_str:
        lines.append(f'|*Type* a|{type_str}')
        lines.append('----')
        lines.append(pattern)
        lines.append('----')
    else:
        lines.append(f'|*Type* |{type_str}')

    # Mandatory
    lines.append(f'|*Mandatory* |{"True" if mandatory else "False"}')

    # Nullable (SML/SMF/SME sections only)
    if show_nullable:
        lines.append(f'|*Is Nullable:* |{"*TRUE*" if nullable else "*FALSE*"}')

    # Example
    if examples:
        key = field_name.replace('[1-n]', '[1]').replace('{identifier}', 'global').replace('*', 'cv_value')
        lines.append('|*Example* a|')
        # Use ---- (listing block) rather than .... (literal block): Asciidoctor.js
        # correctly protects pipe characters from being interpreted as table cell
        # separators only inside listing/source blocks within a| cells, not inside
        # passthrough literal blocks.
        lines.append('----')
        # For table sections (SML/SMF/SME) emit the column header ONCE before all
        # value rows.  The previous code emitted one header per example, which
        # produced duplicate SMH/SFH/SEH lines when a field has multiple examples.
        non_preformatted = [ex for ex in examples if not _is_preformatted(ex)]
        if section_prefix != 'MTD' and non_preformatted:
            hdr = section_prefix.replace('SML', 'SMH').replace('SMF', 'SFH').replace('SME', 'SEH')
            lines.append(_escape_pipes(f'{hdr}\t...\t{key}\t...'))
        for ex in examples:
            if _is_preformatted(ex):
                # Already a full section line (possibly multi-line): emit with pipes escaped.
                for line in ex.split('\n'):
                    if line.strip():
                        lines.append(_escape_pipes(line))
            elif section_prefix == 'MTD':
                lines.append(_escape_pipes(f'MTD\t{key}\t{ex}'))
            else:
                lines.append(_escape_pipes(f'{section_prefix}\t...\t{ex}\t...'))
        lines.append('----')

    lines.append('|============================================================')
    lines.append('')


def process_nested_object(
    lines: list,
    meta_field_name: str,
    meta_prop: dict,
    ref_def: dict,
    schema_defs: dict,
):
    """Process a metadata field that expands to a complex indexed object.

    When the object has an ``object_level_value`` property, that property becomes
    the top-level entry (e.g., ``sample[1-n]`` for the sample name).  When no
    such property exists (e.g., Instrument, MsRun), no top-level entry is written
    and only sub-fields are emitted.
    """
    ref_name = ref_def.get('title', '')
    ref_props = ref_def.get('properties', {})

    # Identify the object-level value field (the field that IS the top-level entry)
    obj_level = [
        (n, p) for n, p in ref_props.items()
        if p.get('object_level_value', False) and not p.get('ignore', False)
    ]

    if obj_level:
        sub_name, sub_prop = obj_level[0]
        # Build a merged property: description/type/examples from sub_prop, fallback to meta_prop.
        # The object-level `examples` on ref_def (multi-line MTD block) take priority over
        # any individual sub-property example because they show the complete picture.
        merged = dict(meta_prop)
        if sub_prop.get('description'):
            merged['description'] = sub_prop['description']
        if sub_prop.get('anyOf'):
            merged['anyOf'] = sub_prop['anyOf']
        # Prefer the object-level example block; fall back to the sub-property's own examples.
        if ref_def.get('examples'):
            merged['examples'] = ref_def['examples']
        elif sub_prop.get('examples'):
            merged['examples'] = sub_prop['examples']
        merged['validation_policy'] = sub_prop.get(
            'validation_policy', meta_prop.get('validation_policy', {})
        )
        write_field_entry(
            lines, f'{meta_field_name}[1-n]', merged, 'MTD', schema_defs,
            prop_key=meta_field_name,
        )
    elif ref_def.get('description'):
        # No indexed top-level value (e.g. Instrument, MsRun): emit the object description
        # as a section preamble so readers know what the sub-fields belong to.
        lines.append(ref_def['description'])
        lines.append('')

    # Determine sub-field iteration order: use explicit spec order if defined,
    # otherwise fall back to schema property order.
    explicit_order = SUB_FIELD_ORDER.get(ref_name, [])
    if explicit_order:
        # Yield props in explicit order first, then any remaining schema props
        ordered_names = explicit_order + [
            n for n in ref_props if n not in explicit_order
        ]
    else:
        ordered_names = list(ref_props.keys())

    for sub_name in ordered_names:
        sub_prop = ref_props.get(sub_name)
        if sub_prop is None:
            continue
        if sub_prop.get('ignore', False):
            continue
        if sub_prop.get('object_level_value', False):
            continue

        # If the sub-field is a genuinely indexed list (e.g. species[1],
        # scan_polarity[1], custom[1]), add a [1-n] suffix. Bar-separated value
        # lists (list_concatenation_str set, e.g. assay_refs, ms_run_refs,
        # study_variable_refs) are a single field whose value is the "|"-joined
        # list, so they must NOT get a trailing [1-n].
        is_sub_list = any(
            a.get('type') == 'array' for a in sub_prop.get('anyOf', [])
        )
        if is_sub_list and not sub_prop.get('list_concatenation_str'):
            sub_field_name = f'{meta_field_name}[1-n]-{sub_name}[1-n]'
        else:
            sub_field_name = f'{meta_field_name}[1-n]-{sub_name}'

        write_field_entry(
            lines, sub_field_name, sub_prop, 'MTD', schema_defs,
            prop_key=sub_name,
        )


# ---------------------------------------------------------------------------
# Section writers
# ---------------------------------------------------------------------------

def write_mtd_section(lines: list, schema: dict):
    """Write the Metadata (MTD) section."""
    defs = schema['$defs']
    meta_props = defs['Metadata']['properties']

    lines.append('[[metadata-section]]')
    lines.append('=== Metadata Section')
    lines.append('')
    lines.append(
        'The metadata section provides additional information about the dataset(s) '
        'reported in the mzTab file. All fields in the metadata section are optional '
        'apart from those noted as mandatory. The fields in the metadata section MUST '
        'be reported in the order listed below. The field name and value MUST be '
        'separated by a tab character.'
    )
    lines.append('')

    # Explicit ordering to match the specification document section order.
    # Each entry is either:
    #   ('direct', field_name)              – a plain scalar/parameter field
    #   ('direct_list', field_name)         – a plain repeatable field using [1-n]
    #   ('nested', field_name, def_name)    – expands to indexed sub-fields
    #   ('noindex', field_name)             – repeatable but NOT indexed (colunit-*)
    mtd_order = [
        # Core metadata
        ('direct',      'mzTab-version'),
        ('direct',      'mzTab-ID'),
        ('direct',      'title'),
        ('direct',      'description'),
        # Sample processing
        ('nested',      'sample_processing',    'SampleProcessing'),
        # Instrument
        ('nested',      'instrument',           'Instrument'),
        # Software
        ('nested',      'software',             'Software'),
        # Publication
        ('nested',      'publication',          'Publication'),
        # Contact
        ('nested',      'contact',              'Contact'),
        # URIs
        ('nested',      'uri',                  'Uri'),
        ('nested',      'external_study_uri',   'Uri'),
        # Quantification method
        ('direct',      'quantification_method'),
        # Sample
        ('nested',      'sample',               'Sample'),
        # MS runs
        ('nested',      'ms_run',               'MsRun'),
        # Assay
        ('nested',      'assay',                'Assay'),
        # Study variable
        ('nested',      'study_variable',       'StudyVariable'),
        # Study variable group
        ('nested',      'study_variable_group', 'StudyVariableGroup'),
        # Protocol
        ('nested',      'protocol',             'Protocol'),
        # Custom metadata
        ('direct_list', 'custom'),
        # Controlled vocabularies
        ('nested',      'cv',                   'CV'),
        # Databases
        ('nested',      'database',             'Database'),
        # Derivatization agents
        ('direct_list', 'derivatization_agent'),
        # Quantification / identification units
        ('direct',      'small_molecule-quantification_unit'),
        ('direct',      'small_molecule_feature-quantification_unit'),
        ('direct',      'small_molecule-identification_reliability'),
        # Identification confidence measures
        ('direct_list', 'id_confidence_measure'),
        # Column unit mappings (non-indexed, repeatable)
        ('noindex',     'colunit-small_molecule'),
        ('noindex',     'colunit-small_molecule_feature'),
        ('noindex',     'colunit-small_molecule_evidence'),
    ]

    for entry in mtd_order:
        kind = entry[0]
        field_name = entry[1]

        if field_name not in meta_props:
            continue
        prop = meta_props[field_name]
        if prop.get('ignore', False):
            continue

        if kind == 'direct':
            write_field_entry(lines, field_name, prop, 'MTD', defs, prop_key=field_name)

        elif kind == 'direct_list':
            write_field_entry(
                lines, f'{field_name}[1-n]', prop, 'MTD', defs, prop_key=field_name
            )

        elif kind == 'noindex':
            write_field_entry(lines, field_name, prop, 'MTD', defs, prop_key=field_name)

        elif kind == 'nested':
            def_name = entry[2]
            if def_name in defs:
                process_nested_object(lines, field_name, prop, defs[def_name], defs)
            else:
                write_field_entry(
                    lines, f'{field_name}[1-n]', prop, 'MTD', defs, prop_key=field_name
                )


def write_table_section(
    lines: list,
    anchor_name: str,
    section_title: str,
    def_name: str,
    row_prefix: str,
    schema: dict,
    intro: str,
):
    """Write a table-based section (SML, SMF, or SME)."""
    defs = schema['$defs']
    obj_props = defs[def_name]['properties']
    # Use lowercase row_prefix as anchor namespace to avoid cross-section duplicates
    section_anchor = row_prefix.lower()

    lines.append(f'[[{anchor_name}]]')
    lines.append(f'=== {section_title}')
    lines.append('')
    lines.append(intro)
    lines.append('')
    if row_prefix == 'SML':
        lines.append('A minimal example row looks like this:')
        lines.append('')
        lines.append('----')
        lines.append('SMH\tSML_ID\tdatabase_identifier\tchemical_name\treliability\tabundance_assay[1]')
        lines.append('SML\t1\tCHEBI:15377\tProline\t[,,high,]\t123.4')
        lines.append('----')
        lines.append('')
    elif row_prefix == 'SMF':
        lines.append('A minimal example row looks like this:')
        lines.append('')
        lines.append('----')
        lines.append('SFH\tSMF_ID\tSME_ID_REFS\texp_mass_to_charge\tcharge\tretention_time_in_seconds')
        lines.append('SMF\t1\t1\t123.45\t1\t420')
        lines.append('----')
        lines.append('')
    elif row_prefix == 'SME':
        lines.append('A minimal example row looks like this:')
        lines.append('')
        lines.append('----')
        lines.append('SEH\tSME_ID\tevidence_input_id\tchemical_name\texp_mass_to_charge\tcharge')
        lines.append('SME\t1\tScan=12345\tProline\t123.45\t1')
        lines.append('----')
        lines.append('')
    lines.append(
        'The order of columns MUST follow the order specified below. '
        'All table columns MUST be Tab separated. '
        'There MUST NOT be any empty cells. '
        'Missing values MUST be reported using "null".'
    )
    lines.append('')

    for prop_name, prop in obj_props.items():
        if prop.get('ignore', False):
            continue

        # Resolve display name
        display_name = DISPLAY_NAME_OVERRIDES.get(prop_name, prop_name)

        write_field_entry(
            lines,
            display_name,
            prop,
            row_prefix,
            defs,
            show_nullable=True,
            prop_key=prop_name,
            anchor_prefix=section_anchor,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--output', '-o',
        default=str(DEFAULT_OUTPUT),
        help='Output AsciiDoc file (default: %(default)s)',
    )
    parser.add_argument(
        '--schema',
        default=str(SCHEMA_FILE),
        help='Input JSON schema file (default: %(default)s)',
    )
    args = parser.parse_args()

    schema = load_schema(Path(args.schema))
    lines = []

    # Document header
    lines += [
        '= mzTab-M Schema Reference',
        ':toc: left',
        ':toclevels: 3',
        ':numbered:',
        '',
        '== Field Reference',
        '',
        'This document provides a reference for all fields defined in the mzTab-M format, '
        'organised by section and ordered by mzTab-M section hierarchy. '
        'Each field entry includes a description, type, mandatory status, and example usage.',
        '',
        'To read this reference quickly, keep the following conventions in mind:',
        '',
        '* `[1-n]` indicates a repeatable field with an index that should be replaced with a concrete number such as `[1]`.',
        '* `Parameter` values follow the mzTab syntax `[CV label, accession, name, value]` and empty fields stay empty.',
        '* Mandatory means the field MUST be present in a conforming mzTab file; optional fields MAY be omitted.',
        '* In the table-based sections, missing values SHOULD be represented as `null`.',
        '',
        '[[sections]]',
        '=== Sections',
        '',
        'The mzTab-M format consists of four cross-referenced data tables: '
        'metadata (MTD), Small Molecule (SML), Small Molecule Feature (SMF), '
        'and Small Molecule Evidence (SME). '
        'The MTD and SML tables are mandatory. '
        'SMF and SME sections SHOULD also be included to capture full identification evidence. '
        'Each table section is introduced by a header line and each row is tab-separated.',
        '',
    ]

    write_mtd_section(lines, schema)

    write_table_section(
        lines,
        anchor_name='small-molecule-section',
        section_title='Small Molecule (SML) Section',
        def_name='SmallMoleculeSummary',
        row_prefix='SML',
        schema=schema,
        intro=(
            'The small molecule section is table-based. '
            'It MUST always come after the metadata section. '
            'Each row reports one final quantified molecule result. '
            'All columns are MANDATORY except for "opt_" columns.'
        ),
    )

    write_table_section(
        lines,
        anchor_name='small-molecule-feature-section',
        section_title='Small Molecule Feature (SMF) Section',
        def_name='SmallMoleculeFeature',
        row_prefix='SMF',
        schema=schema,
        intro=(
            'The small molecule feature section is table-based, representing individual MS regions '
            '(generally the elution profile for all isotopomers from a single charge state). '
            'It MUST always come after the Small Molecule Section. '
            'All columns are MANDATORY except for "opt_" columns.'
        ),
    )

    write_table_section(
        lines,
        anchor_name='small-molecule-evidence-section',
        section_title='Small Molecule Evidence (SME) Section',
        def_name='SmallMoleculeEvidence',
        row_prefix='SME',
        schema=schema,
        intro=(
            'The small molecule evidence section is table-based, representing identification '
            'evidence for small molecules or features (e.g., database search results). '
            'It MUST always come after the Small Molecule Feature Section. '
            'All columns are MANDATORY except for "opt_" columns.'
        ),
    )

    examples = {
        'instrument[1-n]-name': 'MTD\tinstrument[1]-name\t[MS, MS:1000121, Q Exactive, ]',
        'instrument[1-n]-source': 'MTD\tinstrument[1]-source\t[MS, MS:1000073, electrospray ionization, ]',
        'instrument[1-n]-analyzer[1-n]': 'MTD\tinstrument[1]-analyzer[1]\t[MS, MS:1000285, Orbitrap, ]',
        'instrument[1-n]-detector': 'MTD\tinstrument[1]-detector\t[MS, MS:1000253, electron multiplier, ]',
        'software[1-n]-setting[1-n]': 'MTD\tsoftware[1]-setting[1]\tMass tolerance = 5 ppm',
        'contact[1-n]-name': 'MTD\tcontact[1]-name\tJane D. Doe',
        'contact[1-n]-affiliation': 'MTD\tcontact[1]-affiliation\tUniversity of Example',
        'contact[1-n]-email': 'MTD\tcontact[1]-email\tjane.doe@example.org',
        'contact[1-n]-orcid': 'MTD\tcontact[1]-orcid\t0000-0002-1825-0097',
        'quantification_method': 'MTD\tquantification_method\t[MS, MS:1001838, label-free quantification, ]',
        'sample[1-n]-species[1-n]': 'MTD\tsample[1]-species[1]\t[NCBITaxon, NCBITaxon:9606, Homo sapiens, ]',
        'sample[1-n]-tissue[1-n]': 'MTD\tsample[1]-tissue[1]\t[BTO, BTO:0000141, blood plasma, ]',
        'sample[1-n]-cell_type[1-n]': 'MTD\tsample[1]-cell_type[1]\t[CL, CL:0000084, T cell, ]',
        'sample[1-n]-disease[1-n]': 'MTD\tsample[1]-disease[1]\t[DOID, DOID:9351, diabetes mellitus type 2, ]',
        'sample[1-n]-description': 'MTD\tsample[1]-description\tHuman plasma sample from a healthy control donor',
        'sample[1-n]-custom[1-n]': 'MTD\tsample[1]-custom[1]\tSample preparation batch A',
        'ms_run[1-n]-location': 'MTD\tms_run[1]-location\tfile:///data/run01.mzML',
        'ms_run[1-n]-instrument_ref': 'MTD\tms_run[1]-instrument_ref\tinstrument[1]',
        'ms_run[1-n]-format': 'MTD\tms_run[1]-format\t[MS, MS:1000584, mzML file, ]',
        'ms_run[1-n]-id_format': 'MTD\tms_run[1]-id_format\t[MS, MS:1001530, mzML unique identifier, ]',
        'ms_run[1-n]-fragmentation_method[1-n]': 'MTD\tms_run[1]-fragmentation_method[1]\t[MS, MS:1000133, CID, ]',
        'ms_run[1-n]-scan_polarity[1-n]': 'MTD\tms_run[1]-scan_polarity[1]\t[MS, MS:1000130, positive scan, ]',
        'ms_run[1-n]-hash': 'MTD\tms_run[1]-hash\tsha256:34f2d1f2f0e7c5d8a3b6c4d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7',
        'ms_run[1-n]-hash_method': 'MTD\tms_run[1]-hash_method\t[MS, MS:1000569, SHA-256, ]',
        'assay[1-n]-custom[1-n]': 'MTD\tassay[1]-custom[1]\ttechnical replicate 1',
        'assay[1-n]-external_uri': 'MTD\tassay[1]-external_uri\thttps://example.org/assays/001',
        'assay[1-n]-sample_ref': 'MTD\tassay[1]-sample_ref\tsample[1]',
        'assay[1-n]-ms_run_ref[1-n]': 'MTD\tassay[1]-ms_run_ref[1]\tms_run[1]',
        'study_variable[1-n]-assay_refs[1-n]': 'MTD\tstudy_variable[1]-assay_refs\tassay[1]|assay[2]',
        'study_variable[1-n]-description': 'MTD\tstudy_variable[1]-description\tFemale subjects at day 0',
        'study_variable[1-n]-average_function': 'MTD\tstudy_variable[1]-average_function\t[STATO, STATO:0000467, arithmetic mean, ]',
        'study_variable[1-n]-variation_function': 'MTD\tstudy_variable[1]-variation_function\t[STATO, STATO:0000256, standard deviation, ]',
        'study_variable_group[1-n]-description': 'MTD\tstudy_variable_group[1]-description\tBiological sex of the donor',
        'study_variable_group[1-n]-type': 'MTD\tstudy_variable_group[1]-type\t[STATO, STATO:0000252, categorical variable, ]',
        'study_variable_group[1-n]-unit': 'MTD\tstudy_variable_group[1]-unit\t[UO, UO:0000033, day, ]',
        'protocol[1-n]-name': 'MTD\tprotocol[1]-name\tSample preparation',
        'protocol[1-n]-type': 'MTD\tprotocol[1]-type\t[MSIO, MSIO:0000141, metabolite extraction, ]',
        'protocol[1-n]-description': 'MTD\tprotocol[1]-description\tProteins were precipitated with cold methanol and the supernatant was collected.',
        'protocol[1-n]-parameters[1-n]': 'MTD\tprotocol[1]-parameters[1]\t[MSIO, MSIO:0000442, solvent composition, methanol:water 8:2]',
        'cv[1-n]-label': 'MTD\tcv[1]-label\tMS',
        'cv[1-n]-full_name': 'MTD\tcv[1]-full_name\tPSI-MS controlled vocabulary',
        'cv[1-n]-version': 'MTD\tcv[1]-version\t4.1.195',
        'cv[1-n]-uri': 'MTD\tcv[1]-uri\thttps://github.com/HUPO-PSI/psi-ms-CV',
        'database[1-n]-prefix': 'MTD\tdatabase[1]-prefix\tCHEBI',
        'database[1-n]-version': 'MTD\tdatabase[1]-version\t2025-04-17',
        'database[1-n]-uri': 'MTD\tdatabase[1]-uri\thttps://www.ebi.ac.uk/chebi/'
    }
    insert_example_blocks(lines, examples)

    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')

    print(f'Generated: {output_path}')


if __name__ == '__main__':
    main()
