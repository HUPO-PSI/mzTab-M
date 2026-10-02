#!/usr/bin/env bash
# Validate mzTab-M example files with the jmzTab-m CLI and report the results as
# GitHub Actions annotations and a job summary table.
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
# shellcheck disable=SC2206 # the pattern is meant to be glob-expanded
FILES=($PATTERN)
if [ ${#FILES[@]} -eq 0 ]; then
  echo "::warning title=No files found::No files matching '${PATTERN}' were found."
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

  echo "::group::Validating ${file}"
  "${VALIDATOR_CMD[@]}" -c "$file" ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"} -l Info > "$OUTPUT" 2>&1
  EXIT_CODE=$?
  cat "$OUTPUT"
  echo "::endgroup::"

  ERRORS=$(grep -c '^\[Error-' "$OUTPUT")
  WARNS=$(grep -c '^\[Warn-' "$OUTPUT")
  INFOS=$(grep -c '^\[Info-' "$OUTPUT")
  annotate "$file" "$OUTPUT"

  RESULT="✅ passed"
  if [ "$ERRORS" -gt 0 ] || { [ "$FAIL_ON" = "warn" ] && [ "$WARNS" -gt 0 ]; }; then
    RESULT="❌ failed"
  elif [ "$EXIT_CODE" -ne 0 ] && [ "$ERRORS" -eq 0 ] && [ "$WARNS" -eq 0 ]; then
    RESULT="❌ failed (exit code ${EXIT_CODE})"
    echo "::error file=${file},title=Validator failed::Validator exited with code ${EXIT_CODE} without reporting validation messages, see the log for details."
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
  echo "::error title=Validation summary::${FAIL_COUNT} of ${#FILES[@]} file(s) matching '${PATTERN}' failed validation."
  exit 1
fi
echo "✅ All ${#FILES[@]} file(s) matching '${PATTERN}' validated successfully."
