#!/usr/bin/env python3
"""Preflight: which modules and programs the figure-iteration scripts need are found on this machine, and what to set for a missing one.

  python check_env.py [--role patch|sys|programs|all]
Run it with each Python the pipeline uses (make_from_saved.sh --check runs both):
  patch     PY_PATCH: runs the patch script and the figgenie scripts (python-pptx, lxml, Pillow, figgenie's fonttools)
  sys       PY_SYS:   renders, audits, extracts assets (PyMuPDF, Pillow, numpy)
  programs  LibreOffice, LaTeX (compiles a formula), Arial; looked up the way the scripts look them up
Exit 1 if something required for the chosen role is missing; optional items only print a note.
"""
import argparse
import glob
import importlib
import importlib.metadata as md
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _paths  # noqa: E402

bad = 0


def line(tag, text):
    print(f'[{tag:4}] {text}')


def module(import_name, dist, why, required=True):
    global bad
    try:
        importlib.import_module(import_name)
        try:
            ver = md.version(dist)
        except Exception:
            ver = '?'
        line('ok', f'{dist} {ver}')
    except Exception as e:
        line('MISS' if required else 'note', f'{dist} (import {import_name}): {type(e).__name__}  -> pip install {dist}   [{why}]')
        bad += required


def program(label, path, fix, why, required=True):
    global bad
    if path:
        line('ok', f'{label}: {path}')
    else:
        line('MISS' if required else 'note', f'{label} not found  -> {fix}   [{why}]')
        bad += required


def latex_works():
    """Compile one formula through latex_math (needs latex, dvisvgm and the packages the preamble loads)."""
    global bad
    try:
        import latex_math
        r = latex_math.typeset([('x_t', 7)])[('x_t', 7)]
        line('ok', f'LaTeX typesets a formula (x_t at 7 pt: {r["w"]:.2f} x {r["h"] + r["d"]:.2f} pt)')
    except Exception as e:
        line('MISS', f'LaTeX could not typeset a formula: {str(e).strip()[-300:]}   [latex_math: needs latex, dvisvgm, amsmath, mathtools, preview, fix-cm]')
        bad += 1


def chromium():
    """Launch headless Chromium once, the way figgenie does (executable_path is not reliable: newer playwright uses its own
    headless shell). Returns a description or None."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            ver = b.version
            b.close()
        return f'launches (Chromium {ver})'
    except Exception:
        return None


def arial():
    roots = [os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Fonts'), '/usr/share/fonts', '/usr/local/share/fonts',
             os.path.expanduser('~/.fonts'), os.path.expanduser('~/.local/share/fonts'), '/Library/Fonts',
             '/System/Library/Fonts/Supplemental']
    for r in roots:
        for pat in ('arial.ttf', 'Arial.ttf', '**/arial.ttf', '**/Arial.ttf'):
            hit = glob.glob(os.path.join(r, pat), recursive=True)
            if hit:
                return hit[0]


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--role', choices=['patch', 'sys', 'programs', 'all'], default='all')
role = ap.parse_args().role
print(f'python: {sys.executable} {sys.version.split()[0]}   role: {role}')
if role in ('patch', 'all'):
    module('pptx', 'python-pptx', 'patch scripts, pptx_kit, pptx_inspect')
    module('lxml', 'lxml', 'patch scripts, pptx_strip_style')
    module('PIL', 'Pillow', 'add_picture checks the ppi')
    fg = _paths.figgenie_scripts()
    program('figgenie scripts', fg, 'install figgenie-paper-diagram under ~/.codex, ~/.claude or ~/.agents skills, or set FIGGENIE_SCRIPTS=<its scripts folder>',
            'K.formula, pptx_kit.tw() and the from-scratch route need it; editing an existing deck, rendering and the audit do not', required=False)
    if fg:
        sys.path.insert(0, fg)
        try:
            importlib.import_module('measure_text')
            line('ok', 'figgenie measure_text imports (fonttools present)')
        except Exception as e:
            line('MISS', f'figgenie measure_text does not import: {type(e).__name__}: {e}  -> use the Python of figgenie\'s own venv as PY_PATCH')
            bad += 1
    module('playwright', 'playwright', 'only the from-scratch route (figgenie renders SVG with Chromium)', required=False)
    if role == 'patch':
        exe = chromium()
        program('Chromium (playwright)', exe, 'python -m playwright install chromium', 'only the from-scratch route', required=False)
if role in ('sys', 'all'):
    module('fitz', 'PyMuPDF', 'render_pptx, audit_outputs, extract_assets, pdf_text_width_check, pdf_clean')
    module('PIL', 'Pillow', 'render_pptx, qa_sheets, extract_assets')
    module('numpy', 'numpy', 'qa_sheets, extract_assets')
if role in ('programs', 'all'):
    print('programs:')
    program('LibreOffice', _paths.soffice(), 'install LibreOffice, or set SOFFICE=<path to soffice>', 'render_pptx (pptx to PDF)')
    program('latex', _paths.tex_exe('latex'), 'install TeX Live and put its bin folder on PATH, or set TEXLIVE_BIN=<that folder>', 'latex_math (formulas)')
    program('dvisvgm', _paths.tex_exe('dvisvgm'), 'comes with TeX Live; same fix as latex', 'latex_math (formulas)')
    if _paths.tex_exe('latex') and _paths.tex_exe('dvisvgm'):
        latex_works()
    program('inkscape', shutil.which('inkscape') or next(iter(glob.glob(os.path.join(os.environ.get('LOCALAPPDATA', '-'), 'Programs', 'Inkscape', 'bin', 'inkscape.exe'))), None),
            'optional', 'checking SVG path extents', required=False)
    a = arial()
    line('ok' if a else 'note', f'Arial: {a}' if a else 'Arial not found: LibreOffice substitutes a metric-compatible font (Liberation Sans) when it is installed; check the render, and the PDF font names')
print('READY' if not bad else f'{bad} required item(s) missing')
sys.exit(1 if bad else 0)
