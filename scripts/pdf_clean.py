#!/usr/bin/env python3
"""Blank the Info dictionary and the XMP metadata of PDFs this pipeline wrote, in place (system Python with PyMuPDF).

  python pdf_clean.py <pdf> [<pdf> ...]
Chromium's export (figgenie's export_pdf.py) leaves Creator "Chromium" and Producer "Skia/PDF"; a PDF made from a Word or
WPS export may carry an author name. render_pptx.py already blanks the PDFs it renders. Never run this on a file someone
else delivered: it rewrites the file (fonts, text and graphics are untouched).
"""
import os
import sys

import fitz

if len(sys.argv) < 2:
    raise SystemExit(__doc__)
for path in sys.argv[1:]:
    doc = fitz.open(path)
    before = {k: v for k, v in doc.metadata.items() if v and k not in ('format', 'encryption', 'trapped')}
    doc.set_metadata({})
    doc.del_xml_metadata()
    tmp = path + '.tmp'
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    os.replace(tmp, path)
    print(f'{path}: metadata blanked (was {before})')
