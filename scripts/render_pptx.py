#!/usr/bin/env python3
"""PDF and PNG of a pptx: LibreOffice -> PDF (lossless, no downsampling, metadata cleared) -> PNG (300 dpi).

The pptx is only copied, never opened in place (the user may have it open in an editor). LibreOffice stands in for the user's
editor (WPS, PowerPoint, ...): it reads the deck with an independent implementation, so a defect it shows is real; the
editor may still differ by a hair.
  --before <pptx>  also render an older deck and write <stem>_vs_before.png (top = before, bottom = this one)
  --thumbnail      replace the stale thumbnail inside <pptx> by the new render (only on a file this pipeline wrote)
  --dpi N          PNG resolution (default 300)
LibreOffice: $SOFFICE, else the per-user or system-wide Windows install, macOS, or soffice / libreoffice on PATH.
A machine where LibreOffice only runs inside Docker cannot use this script as it is: see references/toolchain.md.

Run (system Python with PyMuPDF + Pillow):  python render_pptx.py <pptx> <out_stem> [--before <older pptx>] [--thumbnail]
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

import fitz
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _paths  # noqa: E402

LOSSLESS = 'pdf:impress_pdf_Export:{"ReduceImageResolution":{"type":"boolean","value":"false"},"UseLosslessCompression":{"type":"boolean","value":"true"}}'


def soffice():
    p = _paths.soffice()
    if not p:
        raise SystemExit('LibreOffice not found: set SOFFICE=<path to soffice>')
    return p


def to_pdf(pptx, pdf_out):
    tmp = tempfile.mkdtemp(prefix='lo_')
    try:
        src = os.path.join(tmp, 'in.pptx')
        shutil.copyfile(pptx, src)
        subprocess.run([soffice(), '-env:UserInstallation=file:///' + tmp.replace('\\', '/').lstrip('/') + '/profile', '--headless',
                        '--convert-to', LOSSLESS, '--outdir', tmp, src], capture_output=True, text=True, timeout=300, check=True)
        doc = fitz.open(os.path.join(tmp, 'in.pdf'))
        doc.set_metadata({})                     # no producer / creator strings in the delivered PDF
        doc.del_xml_metadata()
        doc.save(pdf_out, garbage=3, deflate=True)
        doc.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def to_png(pdf, png_out, dpi=300):
    doc = fitz.open(pdf)
    doc[0].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False).save(png_out)
    doc.close()


def set_thumbnail(pptx, png):
    """Replace docProps/thumbnail.jpeg (the stale screenshot the editor stored) by the new render."""
    if 'docProps/thumbnail.jpeg' not in zipfile.ZipFile(pptx).namelist():
        return False
    im = Image.open(png).convert('RGB')
    im = im.resize((480, round(480 * im.height / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=88)
    tmp = pptx + '.tmp'
    with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, buf.getvalue() if item.filename == 'docProps/thumbnail.jpeg' else zin.read(item.filename))
    os.replace(tmp, pptx)
    return True


def main(pptx, stem, before=None, thumbnail=False, dpi=300):
    to_pdf(pptx, stem + '.pdf')
    to_png(stem + '.pdf', stem + '.png', dpi)
    print('wrote', stem + '.pdf', stem + '.png')
    if thumbnail and set_thumbnail(pptx, stem + '.png'):
        print('thumbnail of', pptx, 'replaced by the new render')
    if before:
        tmp_pdf, tmp_png = stem + '_before.tmp.pdf', stem + '_before.tmp.png'
        to_pdf(before, tmp_pdf)
        to_png(tmp_pdf, tmp_png, dpi)
        a, b = Image.open(tmp_png).convert('RGB'), Image.open(stem + '.png').convert('RGB')
        gap = 14
        sheet = Image.new('RGB', (max(a.width, b.width), a.height + b.height + gap), 'white')
        sheet.paste(a, (0, 0))
        sheet.paste(b, (0, a.height + gap))
        ImageDraw.Draw(sheet).text((6, a.height + 1), 'top: before   bottom: after', fill=(90, 90, 90))
        sheet.save(stem + '_vs_before.png')
        os.remove(tmp_pdf)
        os.remove(tmp_png)
        print('wrote', stem + '_vs_before.png')


if __name__ == '__main__':
    args = sys.argv[1:]
    opts = {'before': None, 'thumbnail': False, 'dpi': 300}
    if '--thumbnail' in args:
        args.remove('--thumbnail')
        opts['thumbnail'] = True
    for flag, conv in (('--before', str), ('--dpi', int)):
        if flag in args:
            i = args.index(flag)
            opts[flag[2:]] = conv(args[i + 1])
            del args[i:i + 2]
    if len(args) != 2:
        raise SystemExit(__doc__)
    main(args[0], args[1], **opts)
