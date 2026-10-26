#!/usr/bin/env bash
# The from-scratch chain for one figure folder: build -> spec check -> formula check -> lint -> fonts -> PDF -> 300 dpi PNG ->
# PPTX -> checks -> audit -> grayscale / colour-blind sheet.
#   bash make_draft.sh <figure folder> [--build tools/build_<name>.py]
# The figure folder holds figure.env (FIG_PAGE and FIG_SIZES are needed by the build script) and tools/build_<name>.py (copy
# templates/build_figure.py); the build script writes fig.svg and spec.json there. Output in the figure folder: fig.final.svg,
# .pdf, .png, .pptx and qa/. A step marked must stops the run when it fails; the others are reported and the run goes on.
# FIG_LATIN (figure.env) is the font svg2pptx puts in the deck for Latin text (default Arial; without --latin it picks a font by
# what is installed). Same settings, PY_PATCH and PY_SYS as make_from_saved.sh.
set -u
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
SK="$(cd "$(dirname "$0")" && pwd)"
. "$SK/_env.sh"
[ $# -ge 1 ] || { sed -n '2,9p' "$0"; exit 2; }
FIG="$(absp "$1")"; shift
BUILD=""
while [ $# -gt 0 ]; do
  case "$1" in --build) BUILD="$2"; shift 2 ;; *) sed -n '2,9p' "$0"; exit 2 ;; esac
done
[ -d "$FIG" ] || { echo "no such figure folder: $FIG"; exit 1; }
cd "$FIG" || exit 1
if [ -z "$BUILD" ]; then
  set -- tools/build_*.py
  [ $# -eq 1 ] && [ -f "$1" ] || { echo "give --build tools/build_<name>.py (found: $*)"; exit 1; }
  BUILD="$1"
fi
export FIG_DIR="$(w "$FIG")"
load_fig_env "$FIG" || exit 1
[ -n "${FIG_PAGE:-}" ] && [ -n "${FIG_SIZES:-}" ] || { echo "the from-scratch route needs FIG_PAGE and FIG_SIZES in $FIG/figure.env"; exit 1; }
pick_python
[ -n "$PY_PATCH" ] || { echo "no Python with python-pptx and lxml found: set PY_PATCH (bash make_from_saved.sh --check)"; exit 1; }
FG="$("$PY_PATCH" -c "import sys; sys.path.insert(0, r'$(w "$SK")'); import _paths; print(_paths.figgenie_scripts() or '')")"
[ -n "$FG" ] || { echo "figgenie-paper-diagram/scripts not found: set FIGGENIE_SCRIPTS"; exit 1; }
export FIGGENIE_SCRIPTS="$FG" FIGURE_ITERATION_SCRIPTS="$(w "$SK")"
S="$(w "$SK")"
mkdir -p qa
FAILED=()
summary() { echo; if [ ${#FAILED[@]} -eq 0 ]; then echo "ALL STEPS OK"; else echo "FAILED STEPS: ${FAILED[*]}"; fi; }
step() {   # step <must|advise> <name> command...
  local mode="$1" name="$2" rc=0; shift 2
  echo; echo "=== $name"
  "$@" || rc=$?
  if [ $rc -ne 0 ]; then
    echo "=== $name FAILED (rc=$rc)"; FAILED+=("$name")
    if [ "$mode" = must ]; then echo "stopping: $name must pass"; summary; exit 1; fi
  fi
}
AUDIT=(--svg fig.final.svg --pdf fig.final.pdf --pptx fig.final.pptx --png fig.final.png)
while IFS= read -r a; do [ -z "$a" ] || AUDIT+=("$a"); done < <(audit_args)
step must   build         "$PY_PATCH" "$BUILD"
step must   spec_validate "$PY_PATCH" "$FG/spec_validate.py" spec.json
step advise latex_check   "$PY_PATCH" "$S/latex_check.py" fig.svg
step must   lint          "$PY_PATCH" "$FG/check.py" fig.svg --spec spec.json
step must   embed_fonts   "$PY_PATCH" "$FG/embed_fonts.py" fig.svg -o fig.final.svg
step must   export_pdf    "$PY_PATCH" "$FG/export_pdf.py" fig.final.svg
step must   pdf_clean     "$PY_SYS" "$S/pdf_clean.py" fig.final.pdf
step must   render_png    "$PY_PATCH" "$FG/render.py" fig.final.svg --scale 4.1667 -o fig.final.png
step advise pdf_text      "$PY_SYS" "$S/pdf_text_width_check.py" fig.final.pdf
step must   svg2pptx      "$PY_PATCH" "$FG/svg2pptx.py" fig.final.svg --spec spec.json --latin "${FIG_LATIN:-Arial}" --force
step must   strip_style   "$PY_PATCH" "$S/pptx_strip_style.py" fig.final.pptx
step advise pptx_check    "$PY_PATCH" "$FG/pptx_check.py" fig.final.pptx --svg fig.final.svg
step advise lo_check      "$PY_SYS" "$S/render_pptx.py" fig.final.pptx qa/lo_check --thumbnail
step must   audit         "$PY_SYS" "$S/audit_outputs.py" "${AUDIT[@]}"
step advise qa_sheets     "$PY_SYS" "$S/qa_sheets.py" fig.final.png qa/gray_deuteranopia.png
summary
[ ${#FAILED[@]} -eq 0 ]
