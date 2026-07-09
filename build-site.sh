#!/bin/bash
# Build and optionally preview the mzTab-M Antora documentation site using Docker.
#
# Usage:
#   ./build-site.sh          # build only
#   ./build-site.sh --serve  # build and start a local HTTP server for preview
#   ./build-site.sh --clean  # remove node_modules before building (force reinstall)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/build/site"
ANTORA_IMAGE="antora/antora:3.1.14"
SERVE=false
CLEAN=false

for arg in "$@"; do
  case "$arg" in
    --serve) SERVE=true ;;
    --clean) CLEAN=false && rm -rf "${SCRIPT_DIR}/node_modules" ;;
    --help|-h)
      echo "Usage: $0 [--serve] [--clean]"
      echo "  --serve  Start a local HTTP server after building (requires Python 3)"
      echo "  --clean  Remove node_modules and reinstall before building"
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
