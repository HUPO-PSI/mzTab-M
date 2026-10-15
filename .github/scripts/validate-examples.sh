#!/usr/bin/env bash
# Validate mzTab-M example files with the jmzTab-m CLI. On GitHub Actions the
# results are reported as annotations and a job summary table; elsewhere (e.g.
# when called from validate.sh) the validator output and per-file results are
# printed to the console only.
#
# Usage: validate-examples.sh <glob pattern> [extra validator args...]
#
# Environment:
#   VALIDATOR  Command that runs the jmzTab-m CLI, e.g. "java -jar jmztabm-cli-1.0.6.jar"
#              or "./jmztabm-validator".
#   FAIL_ON    "warn" (default): [Warn-…] and [Error-…] messages fail a file.
#              "error": only [Error-…] messages fail a file; warnings are annotated.
#
# A non-zero validator exit code that is not explained by reported messages
# (e.g. a parser crash) always fails the file.
set -uo pipefail

PATTERN="${1:?usage: validate-examples.sh <glob pattern> [extra validator args...]}"
shift
EXTRA_ARGS=("$@")
FAIL_ON="${FAIL_ON:-warn}"
read -r -a VALIDATOR_CMD <<< "${VALIDATOR:?VALIDATOR must be set}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/null}"
GHA=false
[ "${GITHUB_ACTIONS:-}" = "true" ] && GHA=true

# Print a workflow command on GitHub Actions; elsewhere print the message only
# (or nothing, if no fallback message is given).
workflow_cmd() {
  if $GHA; then
    echo "$1"
  elif [ $# -gt 1 ]; then
    echo "$2" >&2
  fi
}

# Escape a string for use as a workflow command message.
escape() {
  local s="${1//'%'/'%25'}"
  s="${s//$'\r'/'%0D'}"
  echo "${s//$'\n'/'%0A'}"
}

# Emit one annotation per validator message, attached to the file (and line, if known).
annotate() {
  local file="$1" output="$2" level command line_arg msg
  while IFS= read -r msg; do
    msg="${msg%$'\r'}"
    level="${msg:1:4}"
    case "$level" in
      Erro) command=error ;;
      Warn) command=warning ;;
      *)    command=notice ;;
    esac
    line_arg=""
    if [[ "$msg" =~ \]\ line\ ([0-9]+): ]]; then
      line_arg=",line=${BASH_REMATCH[1]}"
    fi
    echo "::${command} file=${file}${line_arg},title=jmzTab-m ${level/Erro/Error}::$(escape "$msg")"
  done < <(grep -E '^\[(Info|Warn|Error)-' "$output")
  return 0
}

shopt -s nullglob
# Split only on newlines, so that paths containing spaces survive.
IFS=$'\n'
# shellcheck disable=SC2206 # the pattern is meant to be glob-expanded
MATCHES=($PATTERN)
unset IFS
# Skip mzTab files written by earlier --fromJson runs, unless asked for explicitly.
FILES=()
for file in ${MATCHES[@]+"${MATCHES[@]}"}; do
  [[ "$file" == *.json.mztab && "$file" != "$PATTERN" ]] || FILES+=("$file")
done
if [ ${#FILES[@]} -eq 0 ]; then
  workflow_cmd "::warning title=No files found::No files matching '${PATTERN}' were found." \
    "Warning: no files matching '${PATTERN}' were found."
  exit 0
fi

{
  echo "### Validation of \`${PATTERN}\`"
  echo
  echo "| File | Result | Errors | Warnings | Infos |"
  echo "|------|--------|-------:|---------:|------:|"
} >> "$SUMMARY"

FAIL_COUNT=0
OUTPUT=$(mktemp)
trap 'rm -f "$OUTPUT"' EXIT

for file in "${FILES[@]}"; do
  [ -f "$file" ] || continue

  workflow_cmd "::group::Validating ${file}"
  $GHA || echo "==> Validating ${file}"
  "${VALIDATOR_CMD[@]}" -c "$file" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} -l Info > "$OUTPUT" 2>&1
  EXIT_CODE=$?
  cat "$OUTPUT"
  workflow_cmd "::endgroup::"

  ERRORS=$(grep -c '^\[Error-' "$OUTPUT")
  WARNS=$(grep -c '^\[Warn-' "$OUTPUT")
  INFOS=$(grep -c '^\[Info-' "$OUTPUT")
  $GHA && annotate "$file" "$OUTPUT"

  RESULT="✅ passed"
  if [ "$ERRORS" -gt 0 ] || { [ "$FAIL_ON" = "warn" ] && [ "$WARNS" -gt 0 ]; }; then
    RESULT="❌ failed"
  elif [ "$EXIT_CODE" -ne 0 ] && [ "$ERRORS" -eq 0 ] && [ "$WARNS" -eq 0 ]; then
    RESULT="❌ failed (exit code ${EXIT_CODE})"
    workflow_cmd "::error file=${file},title=Validator failed::Validator exited with code ${EXIT_CODE} without reporting validation messages, see the log for details."
  fi

  if [[ "$RESULT" == ❌* ]]; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "${file}: ${RESULT} (${ERRORS} errors, ${WARNS} warnings, ${INFOS} infos)"
  else
    echo "${file}: ${RESULT} (${WARNS} warnings, ${INFOS} infos)"
  fi
  echo "| \`${file}\` | ${RESULT} | ${ERRORS} | ${WARNS} | ${INFOS} |" >> "$SUMMARY"
done

echo "" >> "$SUMMARY"
if [ "$FAIL_COUNT" -ne 0 ]; then
  workflow_cmd "::error title=Validation summary::${FAIL_COUNT} of ${#FILES[@]} file(s) matching '${PATTERN}' failed validation." \
    "❌ ${FAIL_COUNT} of ${#FILES[@]} file(s) matching '${PATTERN}' failed validation."
  exit 1
fi
echo "✅ All ${#FILES[@]} file(s) matching '${PATTERN}' validated successfully."
