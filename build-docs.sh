#!/bin/bash
# Build HTML5, PDF and DOCX versions of an AsciiDoc specification document.
#
# HTML and PDF are produced with asciidoctor / asciidoctor-pdf from the
# asciidoctor Docker image; DOCX is produced via DocBook + pandoc (local
# pandoc if installed, otherwise the pandoc/core Docker image).
set -euo pipefail

NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASCIIDOCTOR_IMAGE="${ASCIIDOCTOR_IMAGE:-asciidoctor/docker-asciidoctor:1}"
PANDOC_IMAGE="${PANDOC_IMAGE:-pandoc/core:3.5}"
HELP_STRING="Usage: $NAME -i <input_dir> -o <output_dir> -c <commit_hash> -d <build_date> -f <adoc_file> [-r] [-h]
  -r  remove leftover docker containers from a previous run
All options except -r and -h are mandatory.
The PDF uses the theme in <input_dir>/pdf-theme/mztabm-theme.yml and the DOCX
the files in <input_dir>/docx-theme/ (reference.docx, docbook-numbering.rb,
postprocess_docx.py, which needs python3) when present."

INPUT_DIR=""; OUTPUT_DIR=""; COMMIT_HASH=""; BUILD_DATE=""; ADOC_FILE=""
while getopts ":i:o:c:d:f:rh" opt; do
  case $opt in
    i) INPUT_DIR="$OPTARG" ;;
    o) OUTPUT_DIR="$OPTARG" ;;
    c) COMMIT_HASH="$OPTARG" ;;
    d) BUILD_DATE="$OPTARG" ;;
    f) ADOC_FILE="$OPTARG" ;;
    r) docker rm asciidoc-to-html asciidoc-to-pdf asciidoc-to-docbook >/dev/null 2>&1 || true ;;
    h) echo "$HELP_STRING"; exit 0 ;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; echo "$HELP_STRING" >&2; exit 1 ;;
  esac
done

if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ] || [ -z "$COMMIT_HASH" ] || [ -z "$BUILD_DATE" ] || [ -z "$ADOC_FILE" ]; then
  echo "$HELP_STRING" >&2
  exit 1
fi

INPUT_DIR="$(cd "$INPUT_DIR" && pwd)"
BUILD_DIR="$INPUT_DIR/output"   # asciidoctor writes here (inside the mounted volume)
mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
BASENAME="${ADOC_FILE%.*}"

ADOC_ATTRS=(-a "commit-hash=$COMMIT_HASH" -a "build-date=$BUILD_DATE")
PDF_ATTRS=()
if [ -f "$INPUT_DIR/pdf-theme/mztabm-theme.yml" ]; then
  PDF_ATTRS=(-a pdf-themesdir=/documents/pdf-theme -a pdf-theme=mztabm)
fi

run_asciidoctor() {
  docker run --rm -u "$(id -u):$(id -g)" -v "$INPUT_DIR:/documents/" -w /documents \
    "$ASCIIDOCTOR_IMAGE" "$@"
}

echo "==> Building HTML5: $ADOC_FILE"
run_asciidoctor asciidoctor -d book "${ADOC_ATTRS[@]}" -D /documents/output "$ADOC_FILE"

echo "==> Building PDF: $ADOC_FILE"
# asciidoctor-pdf reports truncated table cells (content lost) as ERROR but
# still exits 0, so fail the build explicitly when that happens.
PDF_LOG="$(mktemp)"
trap 'rm -f "$PDF_LOG"' EXIT
run_asciidoctor asciidoctor-pdf -d book "${ADOC_ATTRS[@]}" ${PDF_ATTRS[@]+"${PDF_ATTRS[@]}"} \
  -D /documents/output "$ADOC_FILE" 2>&1 | tee "$PDF_LOG"
if grep -q "has been truncated" "$PDF_LOG"; then
  echo "ERROR: the PDF lost content (table cells taller than one page). Shorten or split those cells." >&2
  exit 1
fi

echo "==> Building DocBook: $ADOC_FILE"
DOCX_THEME="$INPUT_DIR/docx-theme"
DOCBOOK_EXT=()
if [ -f "$DOCX_THEME/docbook-numbering.rb" ]; then
  # Section/caption numbers and xref text as in the PDF (pandoc ignores DocBook numbering).
  DOCBOOK_EXT=(-r /documents/docx-theme/docbook-numbering.rb)
fi
run_asciidoctor asciidoctor -d book --backend docbook ${DOCBOOK_EXT[@]+"${DOCBOOK_EXT[@]}"} "${ADOC_ATTRS[@]}" -D /documents/output "$ADOC_FILE"

echo "==> Converting DocBook to DOCX with pandoc"
mkdir -p "$BUILD_DIR/img"
cp -R "$INPUT_DIR/img/." "$BUILD_DIR/img/"
# Two TOC levels, as in the PDF.
PANDOC_ARGS=(--from docbook --to docx --toc --toc-depth=2 --output "$BASENAME.docx")
if [ -f "$DOCX_THEME/reference.docx" ]; then
  # Sans-serif body/headings, monospace code (see docx-theme/make_reference_docx.py).
  cp "$DOCX_THEME/reference.docx" "$BUILD_DIR/mztabm-reference.docx"
  PANDOC_ARGS+=(--reference-doc mztabm-reference.docx)
fi
if command -v pandoc >/dev/null 2>&1; then
  (cd "$BUILD_DIR" && pandoc "${PANDOC_ARGS[@]}" "$BASENAME.xml")
else
  docker run --rm -u "$(id -u):$(id -g)" -v "$BUILD_DIR:/data" -w /data "$PANDOC_IMAGE" \
    "${PANDOC_ARGS[@]}" "$BASENAME.xml"
fi
# Do not leave the template next to the outputs (CI uploads output/*.docx).
rm -f "$BUILD_DIR/mztabm-reference.docx"

if [ -f "$DOCX_THEME/postprocess_docx.py" ]; then
  echo "==> Adding title page, footer and table of contents to the DOCX"
  DOC_VERSION="$(sed -n 's/^:document-version:[[:space:]]*//p' "$INPUT_DIR/$ADOC_FILE" | head -n 1)"
  python3 "$DOCX_THEME/postprocess_docx.py" "$BUILD_DIR/$BASENAME.docx" "$BUILD_DIR/$BASENAME.docx.tmp" \
    --logo "$INPUT_DIR/pdf-theme/mzTab-M-logo.png" --version "${DOC_VERSION:-}"
  mv "$BUILD_DIR/$BASENAME.docx.tmp" "$BUILD_DIR/$BASENAME.docx"
fi

if [ "$BUILD_DIR" != "$OUTPUT_DIR" ]; then
  mkdir -p "$OUTPUT_DIR/img"
  cp "$BUILD_DIR/$BASENAME".{html,pdf,docx} "$OUTPUT_DIR/"
  cp -R "$BUILD_DIR/img/." "$OUTPUT_DIR/img/"
fi

echo "==> Done: $OUTPUT_DIR/$BASENAME.{html,pdf,docx}"
