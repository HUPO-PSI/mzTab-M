#!/usr/bin/env bash
# Validate mzTab-M files locally with the same jmzTab-m validators and rules as
# the CI workflows (.github/workflows/validate-mztab-*.yml). The per-file logic
# is shared with CI via .github/scripts/validate-examples.sh.
#
#   stable    released jmzTab-m CLI jar from Maven Central (needs Java),
#             mzTab-M 2.0; warnings fail a file.
#   snapshot  jmzTab-m 'dev-latest' pre-release (2.1.0-SNAPSHOT) native binary,
#             mzTab-M 2.1; only errors fail a file. Falls back to the CLI jar
#             (needs Java) on platforms without a native binary.
#
# Validators are cached in build/validator/.
set -uo pipefail

JMZTABM_VERSION="${JMZTABM_VERSION:-1.0.6}"
JMZTABM_REPO="${JMZTABM_REPO:-lifs-tools/jmzTab-m}"
JMZTABM_TAG="${JMZTABM_TAG:-dev-latest}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${ROOT}/build/validator"
VALIDATE="${ROOT}/.github/scripts/validate-examples.sh"

usage() {
  cat <<EOF
Usage: ./validate.sh [options] [FILE|PATTERN ...]

Without FILE arguments, validates all example files like CI does:
  stable:   examples/2.0/*
  snapshot: examples/2.1/*.mztab and examples/2.0/* (backward compatibility)

With FILE arguments (or quoted glob patterns), validates only those files.
*.json files are validated with --fromJson automatically.

Options:
  -v, --validator stable|snapshot|all
                       Validator to use (default: all without FILE
                       arguments, snapshot with FILE arguments).
  -f, --fail-on warn|error
                       Fail a file on warnings or only on errors
                       (default: warn for stable, error for snapshot, as in CI).
      --refresh        Re-download the validators even if cached.
      --offline        Only use cached validators, never download.
  -h, --help           Show this help.

Environment:
  JMZTABM_VERSION      Stable jmzTab-m CLI version (default: ${JMZTABM_VERSION}).
  JMZTABM_TAG          jmzTab-m release tag for snapshot (default: ${JMZTABM_TAG}).
EOF
}

die() { echo "Error: $*" >&2; exit 2; }

download() {
  local url="$1" dest="$2"
  echo "Downloading ${url}"
  curl -fL --progress-bar -o "${dest}.part" "$url" || { rm -f "${dest}.part"; return 1; }
  mv "${dest}.part" "$dest"
}

sha256() {
  if command -v sha256sum > /dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1
}

require_java() {
  command -v java > /dev/null || die "the $1 validator needs Java on the PATH."
}

# Sets VALIDATOR to the command running the stable jmzTab-m CLI.
setup_stable() {
  local jar="${CACHE_DIR}/jmztabm-cli-${JMZTABM_VERSION}.jar"
  require_java stable
  if [ ! -f "$jar" ] || $REFRESH; then
    $OFFLINE && die "${jar} is not cached; run without --offline."
    download "https://repo1.maven.org/maven2/de/isas/mztab/jmztabm-cli/${JMZTABM_VERSION}/jmztabm-cli-${JMZTABM_VERSION}.jar" "$jar" \
      || die "failed to download jmzTab-m CLI ${JMZTABM_VERSION}."
  fi
  VALIDATOR="java -jar ${jar}"
}

# Name of the native validator asset for this platform, or empty if there is none.
native_asset() {
  case "$(uname -s)/$(uname -m)" in
    Darwin/arm64)                   echo "jmztabm-validator-aarch64-macos" ;;
    Linux/x86_64)                   echo "jmztabm-validator-amd64-linux" ;;
    MINGW*/x86_64 | MSYS*/x86_64 | CYGWIN*/x86_64) echo "jmztabm-validator-amd64-windows.exe" ;;
  esac
}

# Sets VALIDATOR to the command running the snapshot jmzTab-m validator.
setup_snapshot() {
  local asset dest release digest="" cached=""
  asset="$(native_asset)"
  if [ -z "$asset" ]; then
    echo "No native jmzTab-m validator for $(uname -s)/$(uname -m), using the CLI jar."
    require_java snapshot
    asset="jmztabm-cli-bin.zip"
  fi
  dest="${CACHE_DIR}/${JMZTABM_TAG}/${asset}"
  mkdir -p "$(dirname "$dest")"

  # The tag moves with every jmzTab-m push: compare the cached file against the
  # release asset digest and show which build is used (needs jq).
  if ! $OFFLINE && command -v jq > /dev/null \
    && release="$(curl -fsSL ${GH_TOKEN:+-H "Authorization: Bearer ${GH_TOKEN}"} \
      "https://api.github.com/repos/${JMZTABM_REPO}/releases/tags/${JMZTABM_TAG}")"; then
    digest="$(jq -r --arg a "$asset" '.assets[] | select(.name == $a) | .digest' <<< "$release")"
    echo "jmzTab-m ${JMZTABM_TAG}:"
    jq -r .body <<< "$release" | grep -E '^- (Version|Commit|Built):' || true
  fi
  [ -f "$dest" ] && cached="sha256:$(sha256 "$dest")"

  if [ ! -f "$dest" ] || $REFRESH || { [ -n "$digest" ] && [ "$digest" != "$cached" ]; }; then
    $OFFLINE && die "${dest} is not cached; run without --offline."
    download "https://github.com/${JMZTABM_REPO}/releases/download/${JMZTABM_TAG}/${asset}" "$dest" \
      || die "failed to download ${asset} from ${JMZTABM_REPO}@${JMZTABM_TAG}."
    if [ "$asset" = "jmztabm-cli-bin.zip" ]; then
      rm -rf "${dest%/*}/jmztabm-cli"
      unzip -q -o "$dest" -d "${dest%/*}" || die "failed to unzip ${dest}."
    fi
  elif [ -z "$digest" ]; then
    echo "Using cached ${dest} (could not check for updates, use --refresh to force)."
  fi

  if [ "$asset" = "jmztabm-cli-bin.zip" ]; then
    local jar
    jar="$(ls "${dest%/*}"/jmztabm-cli/jmztabm-cli-*.jar 2> /dev/null | head -n 1)"
    [ -n "$jar" ] || die "no jmztabm-cli jar found in ${dest}."
    VALIDATOR="java -jar ${jar}"
  else
    chmod +x "$dest"
    VALIDATOR="$dest"
  fi
}

# Runs validate-examples.sh for one pattern. Usage: run <validator> <pattern> [extra args...]
run() {
  local name="$1" pattern="$2" fail_on validator
  shift 2
  if [ -n "$FAIL_ON_OPT" ]; then
    fail_on="$FAIL_ON_OPT"
  elif [ "$name" = "stable" ]; then
    fail_on="warn"
  else
    fail_on="error"
  fi
  echo
  echo "################################################################################"
  echo "# ${name} validator (fail on ${fail_on}): ${pattern}"
  echo "################################################################################"
  if [ "$name" = "stable" ]; then validator="$STABLE_VALIDATOR"; else validator="$SNAPSHOT_VALIDATOR"; fi
  if ! VALIDATOR="$validator" FAIL_ON="$fail_on" "$VALIDATE" "$pattern" "$@"; then
    FAILED+=("${name}: ${pattern}")
  fi
}

VALIDATOR_OPT=""
FAIL_ON_OPT=""
REFRESH=false
OFFLINE=false
FILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    -v | --validator) VALIDATOR_OPT="${2:-}"; shift ;;
    -f | --fail-on)   FAIL_ON_OPT="${2:-}"; shift ;;
    --refresh)        REFRESH=true ;;
    --offline)        OFFLINE=true ;;
    -h | --help)      usage; exit 0 ;;
    --)               shift; FILES+=("$@"); break ;;
    -*)               usage >&2; die "unknown option $1" ;;
    *)                FILES+=("$1") ;;
  esac
  shift
done

case "$VALIDATOR_OPT" in
  "") if [ ${#FILES[@]} -eq 0 ]; then NAMES=(stable snapshot); else NAMES=(snapshot); fi ;;
  stable | snapshot) NAMES=("$VALIDATOR_OPT") ;;
  all) NAMES=(stable snapshot) ;;
  *) die "--validator must be stable, snapshot or all." ;;
esac
case "$FAIL_ON_OPT" in
  "" | warn | error) ;;
  *) die "--fail-on must be warn or error." ;;
esac
$REFRESH && $OFFLINE && die "--refresh and --offline are mutually exclusive."

mkdir -p "$CACHE_DIR"
for name in "${NAMES[@]}"; do
  "setup_${name}"
  if [ "$name" = "stable" ]; then STABLE_VALIDATOR="$VALIDATOR"; else SNAPSHOT_VALIDATOR="$VALIDATOR"; fi
done

FAILED=()
if [ ${#FILES[@]} -eq 0 ]; then
  cd "$ROOT" || exit 2
  # Mirrors the matrices of validate-mztab-stable.yml and validate-mztab-snapshot.yml.
  for name in "${NAMES[@]}"; do
    [ "$name" = "snapshot" ] && run snapshot "examples/2.1/*.mztab"
    run "$name" "examples/2.0/*.mz[Tt]ab"
    run "$name" "examples/2.0/*.json" --fromJson
  done
else
  for name in "${NAMES[@]}"; do
    for file in "${FILES[@]}"; do
      if [[ "$file" == *.[Jj][Ss][Oo][Nn] ]]; then
        run "$name" "$file" --fromJson
      else
        run "$name" "$file"
      fi
    done
  done
fi

echo
echo "################################################################################"
if [ ${#FAILED[@]} -ne 0 ]; then
  echo "# Validation failed for:"
  printf '#   %s\n' "${FAILED[@]}"
  echo "################################################################################"
  exit 1
fi
echo "# All validations successful."
echo "################################################################################"
