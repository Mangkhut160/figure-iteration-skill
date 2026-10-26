#!/usr/bin/env python3
"""Compare the width of every text span in a PDF with the width the font itself gives (figgenie metrics, unhinted).

A large gap means the exporter laid the text out with rounded (hinted) advances, so letters look uneven when the PDF is
zoomed (Chromium does this unless the SVG root has text-rendering="geometricPrecision"). Rotated text shows up as a large
gap too: it compares horizontal boxes, so that one is a false alarm.
usage (system Python with PyMuPDF):  python pdf_text_width_check.py fig.final.pdf
"""
import os
import sys

import fitz

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

FG = _paths.figgenie_scripts()
if not FG:
    raise SystemExit('figgenie-paper-diagram/scripts not found: set FIGGENIE_SCRIPTS')
sys.path.insert(0, FG)
from measure_text import width_of  # noqa: E402

if len(sys.argv) != 2:
    raise SystemExit(__doc__)
pg = fitz.open(sys.argv[1])[0]
rows = []
for b in pg.get_text('dict')['blocks']:
    for line in b.get('lines', []):
        for s in line['spans']:
            t = s['text']
            if len(t.strip()) < 4:
                continue
            ref = width_of(t, os.environ.get('FIG_FONT', 'arial'), s['size'], 'Bold' in s['font'])[0]
            got = s['bbox'][2] - s['bbox'][0]
            rows.append((got - ref, got, ref, t))
if not rows:
    raise SystemExit('no text spans of 4 or more characters')
rows.sort()
print('spans', len(rows), '| width minus font width, pt: min %.2f  median %.2f  max %.2f' % (rows[0][0], rows[len(rows) // 2][0], rows[-1][0]))
for d, got, ref, t in rows[:3] + rows[-3:]:
    print('  %+.2f  pdf %.1f  font %.1f  %r' % (d, got, ref, t[:30]))
