#!/bin/bash
# Build and optionally preview the mzTab-M Antora documentation site using Docker.
#
# Usage:
#   ./build-site.sh          # build only
#   ./build-site.sh --serve  # build and start a local HTTP server for preview
#   ./build-site.sh --clean  # remove node_modules before building (force reinstall)
#   ./build-site.sh --with-spec  # also build the spec PDF/DOCX and publish them
#                                # as Antora attachments (Quick access downloads)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/build/site"
ANTORA_IMAGE="antora/antora:3.1.14"
SERVE=false
WITH_SPEC=false
SPEC_FILE="mzTab_format_specification_2_1-M.adoc"
ATTACHMENTS_DIR="${SCRIPT_DIR}/docs/mztabm/modules/ROOT/attachments"

for arg in "$@"; do
  case "$arg" in
    --serve) SERVE=true ;;
    --clean) rm -rf "${SCRIPT_DIR}/node_modules" ;;
    --with-spec) WITH_SPEC=true ;;
    --help|-h)
      echo "Usage: $0 [--serve] [--clean] [--with-spec]"
      echo "  --serve      Start a local HTTP server after building (requires Python 3)"
      echo "  --clean      Remove node_modules and reinstall before building"
      echo "  --with-spec  Build the specification PDF/DOCX and add them as site downloads"
      exit 0
      ;;
  esac
done

echo "==> Checking for Docker..."
if ! command -v docker &>/dev/null; then
  echo "ERROR: Docker is not installed or not on PATH." >&2
  exit 1
fi

# Install Antora + extensions via npm inside the Antora Docker image.
# The antora/antora image ships with Node.js and npm; we override the entrypoint
# to run npm so both steps use the same Node version.
if [ ! -d "${SCRIPT_DIR}/node_modules" ]; then
  echo "==> Installing Antora dependencies (first run)..."
  docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "${SCRIPT_DIR}:/antora" \
    -w /antora \
    --entrypoint npm \
    "${ANTORA_IMAGE}" \
    install --cache /antora/.npm-cache
  echo "    Done. Commit package-lock.json to enable reproducible builds (npm ci)."
else
  echo "==> node_modules present, skipping npm install (use --clean to force reinstall)."
fi

if [ "${WITH_SPEC}" = true ]; then
  echo "==> Building specification PDF/DOCX..."
  SPEC_TMP="$(mktemp -d)"
  trap 'rm -rf "${SPEC_TMP}"' EXIT
  # Build from a copy so build-docs.sh's output/ folder stays out of the repo.
  mkdir -p "${SPEC_TMP}/src"
  cp -R "${SCRIPT_DIR}/specification_documents/." "${SPEC_TMP}/src/"
  rm -rf "${SPEC_TMP}/src/output"
  "${SCRIPT_DIR}/build-docs.sh" -i "${SPEC_TMP}/src" -o "${SPEC_TMP}/out" \
    -c "$(git -C "${SCRIPT_DIR}" rev-parse --short HEAD 2>/dev/null || echo local)" \
    -d "$(date -u +'%Y-%m-%d %H:%M:%S UTC')" -f "${SPEC_FILE}"
  mkdir -p "${ATTACHMENTS_DIR}"
  cp "${SPEC_TMP}/out/${SPEC_FILE%.adoc}".{pdf,docx} "${ATTACHMENTS_DIR}/"
  echo "    Copied PDF/DOCX to ${ATTACHMENTS_DIR}"
elif ! ls "${ATTACHMENTS_DIR}/${SPEC_FILE%.adoc}".pdf &>/dev/null; then
  echo "==> NOTE: spec PDF/DOCX not found in ${ATTACHMENTS_DIR};"
  echo "    download links will be broken. Use --with-spec to build them."
fi

ANTORA_EDIT_BRANCH="${ANTORA_EDIT_BRANCH:-$(git -C "${SCRIPT_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo HEAD)}"

echo "==> Building Antora site..."
docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "${SCRIPT_DIR}:/antora" \
  -w /antora \
  -e ANTORA_EDIT_BRANCH \
  "${ANTORA_IMAGE}" \
  --cache-dir /antora/.cache/antora \
  antora-playbook.yml

echo ""
echo "==> Site built at: ${OUTPUT_DIR}"

if [ "${SERVE}" = true ]; then
  echo ""
  echo "==> Starting local preview server at http://localhost:8080 ..."
  echo "    Press Ctrl+C to stop."
  python3 -m http.server 8080 --directory "${OUTPUT_DIR}"
else
  echo ""
  echo "To preview the site, run one of:"
  echo "  ./build-site.sh --serve"
  echo "  python3 -m http.server 8080 --directory '${OUTPUT_DIR}'"
fi
