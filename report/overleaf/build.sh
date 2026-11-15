#!/usr/bin/env bash
# Build main.tex (or another document: ./build.sh template_demo) with
#   * pdflatex + bibtex, if both are installed, otherwise
#   * tectonic (runs bibtex itself).
# Output: build/<name>.pdf, copied to ./<name>.pdf.
# Exits non-zero if the engine fails or if the log contains an
# "Overfull \hbox" wider than LIMIT points (default 5); every such box is printed.
set -u
cd "$(dirname "$0")"
NAME="${1:-main}"; NAME="${NAME%.tex}"
LIMIT="${OVERFULL_LIMIT:-5}"
OUT=build
mkdir -p "$OUT"

if command -v pdflatex >/dev/null 2>&1 && command -v bibtex >/dev/null 2>&1; then
  ENGINE="pdflatex+bibtex"
  export BIBINPUTS=".:" BSTINPUTS=".:" TEXINPUTS=".:"
  tex() { pdflatex -interaction=nonstopmode -halt-on-error -file-line-error \
            -output-directory="$OUT" "$NAME.tex" >"$OUT/$NAME.stdout" 2>&1; }
  fail() { echo "build failed ($ENGINE); last lines of the log:"; tail -n 40 "$OUT/$NAME.stdout"; exit 1; }
  tex || fail
  if grep -q '^\\citation' "$OUT/$NAME.aux" 2>/dev/null; then
    bibtex "$OUT/$NAME" >"$OUT/$NAME.bibtex.stdout" 2>&1 || { cat "$OUT/$NAME.bibtex.stdout"; echo "bibtex failed"; exit 1; }
    tex || fail
    tex || fail
  else
    echo "note: no \\cite commands found, skipping bibtex"
    tex || fail
  fi
elif command -v tectonic >/dev/null 2>&1; then
  ENGINE="tectonic"
  tectonic -o "$OUT" --keep-logs "$NAME.tex" >"$OUT/$NAME.stdout" 2>&1 || {
    echo "build failed ($ENGINE); last lines of the output:"; tail -n 40 "$OUT/$NAME.stdout"; exit 1; }
else
  echo "error: neither pdflatex+bibtex nor tectonic found (see README_OVERLEAF.md)"; exit 1
fi

cp "$OUT/$NAME.pdf" "./$NAME.pdf"
LOG="$OUT/$NAME.log"
echo "built $NAME.pdf with $ENGINE"

# undefined references / citations (informational)
grep -E "LaTeX Warning: (Citation|Reference).*undefined" "$LOG" | sort -u | sed 's/^/warning: /'

# overfull boxes wider than LIMIT pt are errors; smaller ones are only listed
bad=0
while IFS= read -r line; do
  w=$(printf '%s' "$line" | sed -E 's/^Overfull \\hbox \(([0-9.]+)pt too wide\).*/\1/')
  if awk -v w="$w" -v l="$LIMIT" 'BEGIN{exit !(w+0 > l+0)}'; then
    echo "OVERFULL (> ${LIMIT}pt): $line"; bad=1
  else
    echo "note: small overfull box ($w pt): $line"
  fi
done < <(grep -E '^Overfull \\hbox \([0-9.]+pt too wide\)' "$LOG")
if [ "$bad" -ne 0 ]; then echo "build FAILED: overfull boxes wider than ${LIMIT} pt"; exit 1; fi
echo "OK: no overfull box wider than ${LIMIT} pt"
