#!/usr/bin/env bash
# From the pptx the user saved last to a new version: copy -> patch -> LibreOffice PDF + 300 dpi PNG (+ before/after sheet,
# new thumbnail) -> grayscale / deuteranopia sheet -> audit. Never writes to the saved deck (it may be open in an editor).
#   bash make_from_saved.sh <saved pptx> <patch script> <output stem> [--redo] [--archive DIR]
#   bash make_from_saved.sh --check      which Pythons and programs are found, and what is missing
#     writes <stem>.pptx .pdf .png and <stem>_vs_before.png; the QA sheet goes to $FIG_DIR/qa/<name>_gray_deuteranopia.png
#     --redo     delete my earlier files with that stem first: only a .pptx this script wrote and nobody has saved since
#                (checked against $FIG_DIR/qa/pipeline_outputs.sha1), never the saved deck, never one open in an editor
#     --archive  also copy the outputs, the patch script and the base deck (as user_saved_<name>_<HHMM>.pptx) into DIR
# Settings come from $FIG_DIR/figure.env (every variable in it is exported): FIG_PAGE (page size in pt, WIDTHxHEIGHT such as
#   300x180), FIG_SIZES (allowed text sizes in pt, such as 6,7,8), FIG_MAX_MB, FIG_MIN_PPI (default 300), FIG_FORBID (more words, comma separated, the attribution
#   scan rejects), FIG_INK, FIG_FONT, LATEX_PREAMBLE, LATEX_CACHE. Unset FIG_PAGE / FIG_SIZES / FIG_MAX_MB = not checked.
#   FIG_DIR is the figure folder: the first folder at or above the patch script that holds figure.env or assets/.
#   PY_PATCH (python with python-pptx + lxml; default: the first of figgenie's venvs, python3, python that imports them),
#   PY_SYS (python with PyMuPDF, Pillow, numpy; default python). Windows paths are fine in Git Bash.
set -eu
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
usage() { sed -n '2,15p' "$0"; exit 2; }
SK="$(cd "$(dirname "$0")" && pwd)"
. "$SK/_env.sh"

if [ "${1:-}" = "--check" ]; then
  pick_python
  rc=0
  echo "PY_PATCH = ${PY_PATCH:-<none found: set PY_PATCH to a Python with python-pptx and lxml>}"
  echo "PY_SYS   = $PY_SYS"
  echo
  if [ -n "$PY_PATCH" ]; then "$PY_PATCH" "$(w "$SK/check_env.py")" --role patch || rc=1; else rc=1; fi
  echo
  "$PY_SYS" "$(w "$SK/check_env.py")" --role sys || rc=1
  echo
  "$PY_SYS" "$(w "$SK/check_env.py")" --role programs || rc=1
  exit $rc
fi

[ $# -ge 3 ] || usage
SAVED="$1"; PATCH="$2"; STEM="$3"; shift 3
REDO=0; ARCHIVE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --redo) REDO=1; shift ;;
    --archive) [ $# -ge 2 ] || usage; ARCHIVE="$2"; shift 2 ;;
    *) usage ;;
  esac
done
SAVED="$(absp "$SAVED")"; PATCH="$(absp "$PATCH")"; STEM="$(absp "$STEM")"
if [ -n "$ARCHIVE" ]; then ARCHIVE="$(absp "$ARCHIVE")"; fi
[ -f "$SAVED" ] || { echo "no such deck: $SAVED"; exit 1; }
[ -f "$PATCH" ] || { echo "no such patch script: $PATCH"; exit 1; }
PATCH_DIR="$(cd "$(dirname "$PATCH")" && pwd)"
[ -d "$(dirname "$STEM")" ] || { echo "output folder does not exist: $(dirname "$STEM")"; exit 1; }
if [ -z "${FIG_DIR:-}" ]; then FIG_DIR="$(find_fig_dir "$PATCH_DIR")"; fi
load_fig_env "$FIG_DIR" || exit 1
pick_python
[ -n "$PY_PATCH" ] || { echo "no Python with python-pptx and lxml found: set PY_PATCH (bash make_from_saved.sh --check)"; exit 1; }
"$PY_SYS" -c 'import fitz, PIL, numpy' >/dev/null 2>&1 || { echo "PY_SYS ($PY_SYS) needs PyMuPDF, Pillow and numpy: set PY_SYS to a Python that has them (bash make_from_saved.sh --check)"; exit 1; }
NAME="$(basename "$STEM")"
LEDGER="$FIG_DIR/qa/pipeline_outputs.sha1"
here() { printf '%s/%s' "$(cd "$(dirname "$1")" && pwd)" "$(basename "$1")"; }
if is_open "$STEM.pptx"; then echo "$STEM.pptx is open in an editor (lock file): pick another output name"; exit 1; fi
if [ "$REDO" = 1 ]; then
  if [ -e "$STEM.pptx" ]; then
    if [ "$(here "$STEM.pptx")" = "$(here "$SAVED")" ]; then
      echo "--redo: $STEM.pptx is the base deck itself: not deleting it. Give an output name different from the saved deck."; exit 1
    fi
    if ! grep -qxsF "$(sha "$STEM.pptx")  $(w "$STEM.pptx")" "$LEDGER" 2>/dev/null; then
      echo "--redo: $STEM.pptx was not written by this script, or it has been saved by someone since: not deleting it."
      echo "        Delete it yourself if you are sure, or pick another output name."; exit 1
    fi
  fi
  rm -f "$STEM.pptx" "$STEM.pdf" "$STEM.png" "${STEM}_vs_before.png"
fi
for f in "$STEM.pptx" "$STEM.pdf" "$STEM.png"; do
  if [ -e "$f" ]; then echo "$f exists: pick a new output name, or --redo for a file this script wrote"; exit 1; fi
done
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
echo "base: $SAVED (saved $(mtime_fmt "$SAVED" '%Y-%m-%d %H:%M'))   figure folder: $FIG_DIR"
cp "$SAVED" "$TMP/saved.pptx"
(cd "$PATCH_DIR" && FIG_DIR="$(w "$FIG_DIR")" PYTHONPATH="$(w "$SK")" FIGURE_ITERATION_SCRIPTS="$(w "$SK")" \
  "$PY_PATCH" "$(basename "$PATCH")" "$(w "$TMP/saved.pptx")" "$(w "$STEM.pptx")")
if ! "$PY_SYS" "$(w "$SK/render_pptx.py")" "$(w "$STEM.pptx")" "$(w "$STEM")" --before "$(w "$TMP/saved.pptx")" --thumbnail > "$TMP/render.log" 2>&1; then
  cat "$TMP/render.log"; echo "render failed"; exit 1
fi
grep -v -E "MuPDF|^$" "$TMP/render.log" || true
mkdir -p "$FIG_DIR/qa"
printf '%s  %s\n' "$(sha "$STEM.pptx")" "$(w "$STEM.pptx")" >> "$LEDGER"
"$PY_SYS" "$(w "$SK/qa_sheets.py")" "$(w "$STEM.png")" "$(w "$FIG_DIR/qa/${NAME}_gray_deuteranopia.png")"
AUDIT=(--pdf "$(w "$STEM.pdf")" --pptx "$(w "$STEM.pptx")" --png "$(w "$STEM.png")" --forbid-authors-of "$(w "$TMP/saved.pptx")")
while IFS= read -r a; do [ -z "$a" ] || AUDIT+=("$a"); done < <(audit_args)
set +e; "$PY_SYS" "$(w "$SK/audit_outputs.py")" "${AUDIT[@]}"; RC=$?; set -e
if [ -n "$ARCHIVE" ]; then
  mkdir -p "$ARCHIVE"
  cp "$STEM.pptx" "$STEM.pdf" "$STEM.png" "$ARCHIVE/"
  if [ -e "${STEM}_vs_before.png" ]; then cp "${STEM}_vs_before.png" "$ARCHIVE/"; fi
  cp "$PATCH" "$ARCHIVE/"
  cp "$SAVED" "$ARCHIVE/user_saved_$(basename "$SAVED" .pptx)_$(mtime_fmt "$SAVED" '%H%M').pptx"
  echo "archived in $ARCHIVE"
fi
exit $RC
