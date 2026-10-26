# Shared helpers for make_from_saved.sh and make_draft.sh (sourced, not run).

w() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi; }

# a relative path made absolute against the current folder (the scripts cd into other folders)
absp() { case "$1" in /*|[A-Za-z]:[/\\]*) printf '%s' "$1" ;; *) printf '%s/%s' "$PWD" "$1" ;; esac; }

# modification time of a file in a strftime format: GNU date -r first, then BSD stat (macOS)
mtime_fmt() { date -r "$1" "+$2" 2>/dev/null || stat -f '%Sm' -t "$2" "$1"; }

sha() { if command -v sha1sum >/dev/null 2>&1; then sha1sum "$1" | cut -d' ' -f1; else shasum -a 1 "$1" | cut -d' ' -f1; fi; }

# sets PY_PATCH (python with python-pptx and lxml: the first of figgenie's venvs, python3, python that imports them) and PY_SYS
pick_python() {
  if [ -z "${PY_PATCH:-}" ]; then
    local c p
    for c in "$HOME"/.codex/skills/figgenie-paper-diagram/.venv/Scripts/python.exe \
             "$HOME"/.codex/skills/figgenie-paper-diagram/.venv/bin/python \
             "$HOME"/.claude/skills/figgenie-paper-diagram/.venv/Scripts/python.exe \
             "$HOME"/.claude/skills/figgenie-paper-diagram/.venv/bin/python \
             "$HOME"/.agents/skills/figgenie-paper-diagram/.venv/bin/python python3 python; do
      p="$c"; [ -x "$p" ] || p="$(command -v "$c" 2>/dev/null || true)"
      if [ -n "$p" ] && "$p" -c 'import pptx, lxml' >/dev/null 2>&1; then PY_PATCH="$p"; break; fi
    done
  fi
  PY_PATCH="${PY_PATCH:-}"
  if [ -z "${PY_SYS:-}" ]; then
    local c
    for c in python3 python; do
      if "$c" -c 'import fitz, PIL, numpy' >/dev/null 2>&1; then PY_SYS="$c"; break; fi
    done
  fi
  PY_SYS="${PY_SYS:-python}"
}

# open in an editor: ~$<name> (WPS / Office, which drops up to two leading characters of a long name) or .~lock.<name># (LibreOffice)
is_open() {
  local d n f rest
  d="$(dirname "$1")"; n="$(basename "$1")"
  [ -e "$d/.~lock.$n#" ] && return 0
  for f in "$d"/'~$'*; do
    [ -e "$f" ] || continue
    rest="$(basename "$f")"; rest="${rest#\~\$}"
    case "$n" in *"$rest") [ $(( ${#n} - ${#rest} )) -le 2 ] && return 0 ;; esac
  done
  return 1
}

# the first folder at or above $1 that holds figure.env or assets/ (else $1 itself)
find_fig_dir() {
  local d="$1" p
  while [ -n "$d" ] && [ "$d" != "/" ] && [ "$d" != "." ]; do
    if [ -f "$d/figure.env" ] || [ -d "$d/assets" ]; then printf '%s' "$d"; return; fi
    p="$(dirname "$d")"; [ "$p" = "$d" ] && break; d="$p"
  done
  printf '%s' "$1"
}

# sources $1/figure.env (every variable in it is exported) and checks the values; returns 1 on a malformed one
load_fig_env() {
  if [ -f "$1/figure.env" ]; then
    set -a; . "$1/figure.env"; set +a
    echo "figure.env: $1/figure.env"
  else
    echo "figure.env: none in $1 (copy templates/figure.env there and set FIG_PAGE and FIG_SIZES from the paper's profile)"
  fi
  if [ -n "${FIG_PAGE:-}" ] && ! printf '%s' "$FIG_PAGE" | grep -Eq '^[0-9]+(\.[0-9]+)?x[0-9]+(\.[0-9]+)?$'; then
    echo "FIG_PAGE must be WIDTHxHEIGHT in pt, like 300x180 (got: $FIG_PAGE): fix $1/figure.env"; return 1
  fi
  if [ -n "${FIG_SIZES:-}" ] && ! printf '%s' "$FIG_SIZES" | grep -Eq '^[0-9]+(\.[0-9]+)?(,[0-9]+(\.[0-9]+)?)*$'; then
    echo "FIG_SIZES must be comma separated sizes in pt, like 6,7,8 (got: $FIG_SIZES): fix $1/figure.env"; return 1
  fi
  if [ -n "${FIG_MIN_PPI:-}" ] && ! printf '%s' "$FIG_MIN_PPI" | grep -Eq '^[0-9]+(\.[0-9]+)?$'; then
    echo "FIG_MIN_PPI must be a number (got: $FIG_MIN_PPI): fix $1/figure.env"; return 1
  fi
  if [ -n "${FIG_MAX_MB:-}" ] && ! printf '%s' "$FIG_MAX_MB" | grep -Eq '^[0-9]+(\.[0-9]+)?$'; then
    echo "FIG_MAX_MB must be a number of megabytes (got: $FIG_MAX_MB): fix $1/figure.env"; return 1
  fi
  [ -n "${FIG_PAGE:-}" ] || echo "note: FIG_PAGE is not set, so the page size is not checked"
  [ -n "${FIG_SIZES:-}" ] || echo "note: FIG_SIZES is not set, so the text sizes are not checked"
  return 0
}

# extra arguments for audit_outputs.py from the figure.env values, one per line
audit_args() {
  [ -z "${FIG_PAGE:-}" ] || printf '%s\n%s\n' --page "$FIG_PAGE"
  [ -z "${FIG_SIZES:-}" ] || printf '%s\n%s\n' --sizes "$FIG_SIZES"
  [ -z "${FIG_MAX_MB:-}" ] || printf '%s\n%s\n' --max-mb "$FIG_MAX_MB"
  [ -z "${FIG_MIN_PPI:-}" ] || printf '%s\n%s\n' --min-ppi "$FIG_MIN_PPI"
  [ -z "${FIG_FORBID:-}" ] || printf '%s\n%s\n' --forbid "$FIG_FORBID"
  return 0
}
