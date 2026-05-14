#!/bin/bash
# Regenerate AsciiDoc documentation partials for the Antora documentation site.
#
# Run this script whenever:
#   - schema/mzTab_2_1-M.json is updated (regenerates the field reference)
#   - specification_documents/mzTab_format_specification_2_1-M.adoc is updated
#
# Usage:
#   ./gen-docs.sh           # regenerate both schema and spec partials
#   ./gen-docs.sh --schema  # regenerate schema field reference only
#   ./gen-docs.sh --spec    # regenerate spec partial only
#   ./gen-docs.sh --help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCHEMA_PY="${SCRIPT_DIR}/schema/generate_schema_adoc.py"
SCHEMA_JSON="${SCRIPT_DIR}/schema/mzTab_2_1-M.json"
PARTIALS_DIR="${SCRIPT_DIR}/docs/mztabm/modules/developers/partials"
SCHEMA_PARTIAL="${PARTIALS_DIR}/mzTab_m_schema.adoc"

SPEC_SRC="${SCRIPT_DIR}/specification_documents/mzTab_format_specification_2_1-M.adoc"
SPEC_PARTIAL="${PARTIALS_DIR}/mzTab_format_specification.adoc"

DO_SCHEMA=true
DO_SPEC=true

for arg in "$@"; do
  case "$arg" in
    --schema) DO_SCHEMA=true; DO_SPEC=false ;;
    --spec)   DO_SCHEMA=false; DO_SPEC=true ;;
    --help|-h)
      echo "Usage: $0 [--schema] [--spec]"
      echo ""
      echo "Regenerates AsciiDoc partials consumed by the Antora documentation site."
      echo "Run from the repository root after editing the JSON schema or specification."
      echo ""
      echo "Options:"
      echo "  --schema  Regenerate only the JSON schema → AsciiDoc field reference"
      echo "  --spec    Regenerate only the headless specification partial"
      echo ""
      echo "Output files:"
      echo "  ${SCHEMA_PARTIAL}"
      echo "  ${SPEC_PARTIAL}"
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

  echo "    Done."
  CHANGED+=("${SCHEMA_PARTIAL}")
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

echo ""
echo "==> Complete. Stage and commit the updated partials:"
for f in "${CHANGED[@]}"; do
  echo "    git add ${f}"
done
echo "    git commit -m 'docs: regenerate Antora partials'"
