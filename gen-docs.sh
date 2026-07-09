#!/bin/bash
# Regenerate AsciiDoc documentation partials for the Antora documentation site.
#
# Run this script whenever:
#   - schema/mzTab_2_1-M.json is updated (regenerates the field reference)
#   - specification_documents/mzTab_format_specification_2_1-M.adoc is updated
#   - specification_documents/mzTab_m_2_0_schema.adoc or mzTab_m_2_1_schema.adoc
#     is updated (regenerates the v2.0→v2.1 changes document)
#
# Usage:
#   ./gen-docs.sh            # regenerate schema, spec, and changes documents
#   ./gen-docs.sh --schema   # regenerate schema field reference only
#   ./gen-docs.sh --spec     # regenerate spec partial only
#   ./gen-docs.sh --changes  # regenerate v2.0→v2.1 changes document only
#   ./gen-docs.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCHEMA_PY="${SCRIPT_DIR}/schema/generate_schema_adoc.py"
SCHEMA_JSON="${SCRIPT_DIR}/schema/mzTab_2_1-M.json"
PARTIALS_DIR="${SCRIPT_DIR}/docs/mztabm/modules/developers/partials"
SCHEMA_PARTIAL="${PARTIALS_DIR}/mzTab_m_2_1_schema.adoc"
SCHEMA_SPEC_COPY="${SCRIPT_DIR}/specification_documents/mzTab_m_2_1_schema.adoc"

SPEC_SRC="${SCRIPT_DIR}/specification_documents/mzTab_format_specification_2_1-M.adoc"
SPEC_PARTIAL="${PARTIALS_DIR}/mzTab_format_specification_2_1-M.adoc"

CHANGES_PY="${SCRIPT_DIR}/compare_adoc_specs.py"
CHANGES_OLD="${SCRIPT_DIR}/specification_documents/mzTab_m_2_0_schema.adoc"
CHANGES_NEW="${SCHEMA_PARTIAL}"
CHANGES_OUT="${SCRIPT_DIR}/specification_documents/mzTab_m_2_0_to_2_1_changes.adoc"
CHANGES_PARTIAL="${PARTIALS_DIR}/mzTab_m_2_0_to_2_1_changes.adoc"

DO_SCHEMA=true
DO_SPEC=true
DO_CHANGES=true

for arg in "$@"; do
  case "$arg" in
    --schema)  DO_SCHEMA=true;  DO_SPEC=false;  DO_CHANGES=false ;;
    --spec)    DO_SCHEMA=false; DO_SPEC=true;   DO_CHANGES=false ;;
    --changes) DO_SCHEMA=false; DO_SPEC=false;  DO_CHANGES=true  ;;
    --help|-h)
      echo "Usage: $0 [--schema] [--spec] [--changes]"
      echo ""
      echo "Regenerates AsciiDoc documents consumed by the Antora documentation site."
      echo "Run from the repository root after editing the JSON schema or specification."
      echo ""
      echo "Options:"
      echo "  --schema   Regenerate only the JSON schema → AsciiDoc field reference"
      echo "  --spec     Regenerate only the headless specification partial"
      echo "  --changes  Regenerate only the v2.0→v2.1 element comparison document"
      echo ""
      echo "Output files:"
      echo "  ${SCHEMA_PARTIAL}"
      echo "  ${SCHEMA_SPEC_COPY}"
      echo "  ${SPEC_PARTIAL}"
      echo "  ${CHANGES_OUT}"
      echo "  ${CHANGES_PARTIAL}"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

CHANGED=()

# --- Schema partial -----------------------------------------------------------
if [ "${DO_SCHEMA}" = true ]; then
  echo "==> Generating schema AsciiDoc field reference..."
  echo "    Input:  ${SCHEMA_JSON}"
  echo "    Output: ${SCHEMA_PARTIAL}"

  if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required but not found on PATH." >&2
    exit 1
  fi

  TMPFILE="$(mktemp /tmp/mztabm_schema_XXXXXX.adoc)"
  trap 'rm -f "${TMPFILE}"' EXIT

  python3 "${SCHEMA_PY}" --schema "${SCHEMA_JSON}" --output "${TMPFILE}"

  # The generator emits a standalone document header (= title, :toc:, etc.)
  # that is incompatible with Antora include:: directives.  Strip everything
  # before the first section heading so only content is included.
  awk '/^== /{found=1} found{print}' "${TMPFILE}" > "${SCHEMA_PARTIAL}"

  # Also copy the headless schema into specification_documents/ so that
  # mzTab_format_specification_2_1-M.adoc's include::mzTab_m_2_1_schema.adoc[]
  # resolves correctly when building the standalone document.
  cp "${SCHEMA_PARTIAL}" "${SCHEMA_SPEC_COPY}"

  echo "    Done."
  CHANGED+=("${SCHEMA_PARTIAL}" "${SCHEMA_SPEC_COPY}")
fi

# --- Spec partial -------------------------------------------------------------
if [ "${DO_SPEC}" = true ]; then
  echo "==> Generating headless specification partial..."
  echo "    Input:  ${SPEC_SRC}"
  echo "    Output: ${SPEC_PARTIAL}"

  # Strip the AsciiDoc document header (= title, :attribute: lines, ifdef
  # blocks, etc.) so the file is safe for Antora include:: directives.
  # The document body starts at the first [preface] block attribute.
  awk '/^\[preface\]/{found=1} found{print}' "${SPEC_SRC}" > "${SPEC_PARTIAL}"

  echo "    Done."
  CHANGED+=("${SPEC_PARTIAL}")
fi

# --- Changes document ---------------------------------------------------------
if [ "${DO_CHANGES}" = true ]; then
  echo "==> Generating v2.0→v2.1 element comparison document..."
  echo "    Old spec: ${CHANGES_OLD}"
  echo "    New spec: ${CHANGES_NEW}"
  echo "    Output:   ${CHANGES_OUT}"

  if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 is required but not found on PATH." >&2
    exit 1
  fi

  if [ ! -f "${CHANGES_OLD}" ]; then
    echo "ERROR: old spec not found: ${CHANGES_OLD}" >&2
    exit 1
  fi
  if [ ! -f "${CHANGES_NEW}" ]; then
    echo "ERROR: new spec not found: ${CHANGES_NEW}" >&2
    exit 1
  fi

  python3 "${CHANGES_PY}" \
    --old "${CHANGES_OLD}" \
    --new "${CHANGES_NEW}" \
    --out "${CHANGES_OUT}"

  # Strip the standalone document header so the file is usable as an
  # Antora include:: partial (same treatment as the schema and spec partials).
  awk '/^== /{found=1} found{print}' "${CHANGES_OUT}" > "${CHANGES_PARTIAL}"
  echo "    Antora partial: ${CHANGES_PARTIAL}"

  echo "    Done."
  CHANGED+=("${CHANGES_OUT}" "${CHANGES_PARTIAL}")
fi

echo ""
echo "==> Complete. Stage and commit the updated files:"
for f in "${CHANGED[@]}"; do
  echo "    git add ${f}"
done
echo "    git commit -m 'docs: regenerate Antora partials'"
