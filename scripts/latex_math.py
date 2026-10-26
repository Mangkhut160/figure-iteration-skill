#!/usr/bin/env python3
"""TeX math typeset by the local LaTeX (latex + dvisvgm from TeX Live) as vector paths, for figure SVGs and pptx patches.

Each formula is set in its own preview box at the requested size with amsmath, amssymb, mathtools and fix-cm (so any size is
allowed), in the math font of the default preamble: Computer Modern. The glyphs are LaTeX's own at the optical size it picks
for that size (at 7 pt: cmmi7 with cmmi5 scripts), not a 10 pt design scaled down. dvisvgm writes the box with its baseline at
y = 0 and its left edge at x = 0, in bp (= the figure's pt).
Environment: TEXLIVE_BIN (folder with latex and dvisvgm; else PATH; else the usual TeX Live install folders); LATEX_CACHE
(a json file that keeps results between runs, e.g. <figure>/tools/latex_cache.json; unset = no cache); LATEX_PREAMBLE (extra
preamble text for a paper whose math font is not Computer Modern, e.g. \\usepackage{newtxmath}; part of the cache key).
CLI:  python latex_math.py 7 'x_t' '\\hat{y}'      prints width, height and depth of each box in pt
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

PREAMBLE = (r'\documentclass{article}\usepackage{amsmath,amssymb,mathtools,fix-cm}'
            r'\usepackage[active,tightpage]{preview}\setlength\PreviewBorder{0pt}' + os.environ.get('LATEX_PREAMBLE', ''))
CACHE = os.environ.get('LATEX_CACHE') or None


def _exe(name):
    p = _paths.tex_exe(name)
    if not p:
        raise RuntimeError(f'{name} not found: put the TeX Live bin folder on PATH or set TEXLIVE_BIN=<folder holding latex and dvisvgm>')
    return p


def _key(tex, size):
    return hashlib.sha1(f'{PREAMBLE}|{size:g}|{tex}'.encode('utf-8')).hexdigest()


def typeset(items):
    """items: (tex, size_pt) pairs -> {(tex, size): {w, h, d, body}}: box width, height above and depth below the baseline
    in pt, and the glyph paths (no fill set) with the baseline at y = 0 and the box's left edge at x = 0."""
    items = list(dict.fromkeys(items))
    cache = {}
    if CACHE and os.path.exists(CACHE):
        with open(CACHE, encoding='utf-8') as fh:
            cache = json.load(fh)
    todo = [(t, s) for t, s in items if _key(t, s) not in cache]
    if todo:
        with tempfile.TemporaryDirectory() as td:
            pages = ''.join(r'\begin{preview}\fontsize{%g}{%g}\selectfont $%s$\end{preview}' % (s, 1.2 * s, t) + '\n' for t, s in todo)
            with open(os.path.join(td, 'f.tex'), 'w', encoding='utf-8') as fh:
                fh.write(PREAMBLE + '\n\\begin{document}\n' + pages + '\\end{document}\n')
            r = subprocess.run([_exe('latex'), '-interaction=nonstopmode', '-halt-on-error', 'f.tex'], cwd=td, capture_output=True, text=True)
            if r.returncode:
                log = open(os.path.join(td, 'f.log'), encoding='utf-8', errors='replace').read()
                raise RuntimeError('latex failed:\n' + '\n'.join(l for l in log.splitlines() if l.startswith('!') or 'l.' in l[:4])[-1500:])
            r = subprocess.run([_exe('dvisvgm'), '--no-fonts=1', '--bbox=preview', '--page=1-', '--output=f-%p.svg', 'f.dvi'],
                               cwd=td, capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError('dvisvgm failed:\n' + r.stderr[-1500:])
            out = sorted((int(re.search(r'(\d+)\.svg$', n).group(1)), n) for n in os.listdir(td) if re.fullmatch(r'f-\d+\.svg', n))
            if len(out) != len(todo):
                raise RuntimeError(f'dvisvgm wrote {len(out)} pages for {len(todo)} formulas')
            for (t, s), (_, name) in zip(todo, out):
                with open(os.path.join(td, name), encoding='utf-8') as fh:
                    svg = fh.read()
                x0, y0, w, h = map(float, re.search(r"viewBox='([^']+)'", svg).group(1).split())
                inner = re.search(r"<g id='page\d+'>(.*)</g>\s*</svg>", svg, re.S).group(1)
                if '<use' in inner or '<text' in inner:
                    raise RuntimeError(f'unexpected dvisvgm markup for {t!r}')
                cache[_key(t, s)] = dict(tex=t, size=s, w=round(w, 4), h=round(-y0, 4), d=round(h + y0, 4),
                                         body=re.sub(r'\s+', ' ', inner.strip()).replace("'", '"'))
        if CACHE:
            with open(CACHE, 'w', encoding='utf-8') as fh:
                json.dump(cache, fh, indent=0)
    return {(t, s): cache[_key(t, s)] for t, s in items}


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    size = float(sys.argv[1])
    for (t, s), r in typeset([(t, size) for t in sys.argv[2:]]).items():
        print(f'{r["w"]:7.2f} w {r["h"]:5.2f} h {r["d"]:5.2f} d  {t!r} @{s:g}pt')
