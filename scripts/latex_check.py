#!/usr/bin/env python3
"""Placement check for the LaTeX formulas of a figure SVG (<g data-symbol="latex" data-w data-h data-d transform="translate(x y)">).

figgenie's lint does not measure formulas as text and its tex_fill.py --check only knows MathJax placeholders, so this does
the same three checks for LaTeX-typeset formulas: a formula inside a node stays 1 pt inside the node's box (the largest
<rect> of the group), keeps 0.5 pt from every <text> (figgenie's font metrics; rotated text skipped), every <image> and every
other formula. Exit status 1 when anything fails.
Run (figgenie venv):  python latex_check.py fig.svg
"""
import os
import re
import sys

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

FG = _paths.figgenie_scripts()
if not FG:
    raise SystemExit('figgenie-paper-diagram/scripts not found: set FIGGENIE_SCRIPTS')
sys.path.insert(0, FG)
from measure_text import width_of  # noqa: E402
import _svgkit as K  # noqa: E402

NS = '{http://www.w3.org/2000/svg}'
FONT, PAD_BOX, GAP_TEXT, GAP_IMG = os.environ.get('FIG_FONT', 'arial'), 1.0, 0.5, 0.3


def top_group(el):
    while el.getparent() is not None and el.getparent().tag != NS + 'svg':
        el = el.getparent()
    return el


def inherited(el, attr, default=None):
    while el is not None:
        if el.get(attr) not in (None, ''):
            return el.get(attr)
        el = el.getparent()
    return default


def text_box(t):
    s = ''.join(t.itertext())
    size = inherited(t, 'font-size')
    if size is None:
        raise SystemExit(f'text {s!r} has no font-size: set it on the root <svg> or on the text')
    size = float(size)
    bold = inherited(t, 'font-weight', 'normal') == 'bold'
    w = width_of(s, FONT, size, bold)[0]
    up, down = K.ink_band(s, size, FONT, bold)
    x, y = float(t.get('x')), float(t.get('y'))
    anchor = t.get('text-anchor', 'start')
    x0 = x - w / 2 if anchor == 'middle' else (x - w if anchor == 'end' else x)
    return (x0, y - up, x0 + w, y + down), s


def overlap(a, b, gap):
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def main(path):
    root = etree.parse(path).getroot()
    forms, texts, imgs = [], [], []
    for g in root.iter(NS + 'g'):
        if g.get('data-symbol') == 'latex':
            tx, ty = map(float, re.search(r'translate\(([-\d.]+)[ ,]+([-\d.]+)\)', g.get('transform')).groups())
            w, h, d = (float(g.get(k)) for k in ('data-w', 'data-h', 'data-d'))
            forms.append(((tx, ty - h, tx + w, ty + d), g.get('data-tex'), top_group(g)))
    for t in root.iter(NS + 'text'):
        if t.get('transform') or any(a.get('data-symbol') == 'latex' for a in t.iterancestors()):
            continue
        texts.append(text_box(t))
    for im in root.iter(NS + 'image'):
        x, y, w, h = (float(im.get(k)) for k in ('x', 'y', 'width', 'height'))
        imgs.append(((x, y, x + w, y + h), im.get('href', '')[-28:]))
    bad = 0
    for i, (fb, tex, grp) in enumerate(forms):
        gid = grp.get('id', '')
        msgs = []
        if gid.startswith('n:'):
            rects = [r for r in grp.iter(NS + 'rect') if r.get('width') and r.get('height')]
            if rects:                                   # a node that is only a formula (a label) has no box to stay inside
                r = max(rects, key=lambda r: float(r.get('width')) * float(r.get('height')))
                bx = (float(r.get('x')), float(r.get('y')), float(r.get('x')) + float(r.get('width')), float(r.get('y')) + float(r.get('height')))
                if not (fb[0] >= bx[0] + PAD_BOX and fb[1] >= bx[1] + PAD_BOX and fb[2] <= bx[2] - PAD_BOX and fb[3] <= bx[3] - PAD_BOX):
                    msgs.append(f'leaves the box of {gid} {tuple(round(v, 1) for v in bx)}')
        msgs += [f'within {GAP_TEXT} pt of text {s!r}' for tb, s in texts if overlap(fb, tb, GAP_TEXT)]
        msgs += [f'touches image ...{h}' for ib, h in imgs if overlap(fb, ib, GAP_IMG)]
        msgs += [f'overlaps formula {o[1]!r}' for j, o in enumerate(forms) if j != i and overlap(fb, o[0], GAP_TEXT)]
        box = '(' + ', '.join(f'{v:.1f}' for v in fb) + ')'
        print(f'  {"FAIL" if msgs else "ok  "}  {gid:<18} {tex!r:<34} {box}' + ''.join('\n        - ' + m for m in msgs))
        bad += bool(msgs)
    print(f'{len(forms)} formula(s), {bad} with problems')
    return 1 if bad else 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    sys.exit(main(sys.argv[1]))
