#!/usr/bin/env python3
"""Turn the material the user supplied (arXiv source PDFs, icon PNGs, logos, own SVG artwork) into figure assets.

The user's folders are only read; write the results into <figure>/assets/ and log every file in assets/SOURCES.md.
System Python (PyMuPDF, Pillow, numpy).

  pdf-images <pdf> <out dir> [--min 64]   every embedded raster of a PDF as a PNG (its soft mask as alpha), named
                                          <pdf stem>_p<page>_x<xref>_<w>x<h>.png; look at them, keep the one you need
  cutout <in> <out> [--lo 232 --hi 250] [--max-h N] [--pad 2]
                                          photo or drawing on white: near-white -> transparent (soft edge from lo to hi
                                          of the darkest channel), cropped to the ink, optionally scaled to N px high
  icon <in> <out> [--side 256] [--pad 4]  icon PNG with alpha: crop to the ink, shrink with premultiplied alpha (no dark fringe)
  tint <in> <out> --dark '#4a4a4a' [--light '#ffffff']
                                          recolour by role (e.g. one colour per role): luminance mapped from dark
                                          to light, so the shading stays; alpha unchanged
  glyph <in> <out> [--bg 244]             black pictogram on an off-white ground -> pure black with the darkness as alpha
  svg <in.svg> <out> [--scale 24] [--pad 4]
                                          render an SVG (own artwork, a logo) to a transparent PNG
"""
import argparse
import os

import fitz
import numpy as np
from PIL import Image


def crop_to_alpha(im, pad=2, thr=8):
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > thr)
    if not len(xs):
        raise SystemExit('nothing left after removing the background')
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + 1 + pad, im.width)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + 1 + pad, im.height)
    return im.crop((x0, y0, x1, y1))


def white_to_alpha(im, lo=232, hi=250):
    a = np.asarray(im.convert('RGBA')).copy()
    m = a[..., :3].min(axis=2).astype(float)
    soft = np.clip((hi - m) / (hi - lo), 0, 1) * 255
    a[..., 3] = np.minimum(a[..., 3], soft.astype(np.uint8))
    return Image.fromarray(a, 'RGBA')


def shrink(im, side=256):
    s = side / max(im.size)
    if s >= 1:
        return im
    return im.convert('RGBa').resize((round(im.width * s), round(im.height * s)), Image.LANCZOS).convert('RGBA')


def role_tint(im, dark, light='#ffffff'):
    a = np.asarray(im.convert('RGBA')).astype(float)
    lum = a[..., :3] @ np.array([0.299, 0.587, 0.114])
    lo = np.percentile(lum[a[..., 3] > 128], 1)
    t = np.clip((lum - lo) / max(255 - lo, 1), 0, 1)[..., None]
    c0 = np.array([int(dark[i:i + 2], 16) for i in (1, 3, 5)], float)
    c1 = np.array([int(light[i:i + 2], 16) for i in (1, 3, 5)], float)
    a[..., :3] = c0 * (1 - t) + c1 * t
    return Image.fromarray(np.round(a).astype(np.uint8), 'RGBA')


def glyph(im, bg=244):
    a = np.asarray(im.convert('RGBA')).astype(float)
    lum = a[..., :3].mean(axis=2)
    alpha = np.clip((bg - lum) / (bg - 60), 0, 1) * (a[..., 3] / 255)
    out = np.zeros(a.shape, dtype=np.uint8)
    out[..., 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def save(im, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    im.save(path, optimize=True)
    print('wrote', path, im.size)


def pdf_images(pdf, out, min_side):
    doc = fitz.open(pdf)
    stem = os.path.splitext(os.path.basename(pdf))[0]
    seen = set()
    for pno, page in enumerate(doc, 1):
        for img in page.get_images(full=True):
            xref, smask = img[0], img[1]
            if xref in seen:
                continue
            seen.add(xref)
            pix = fitz.Pixmap(doc, xref)
            if min(pix.width, pix.height) < min_side or pix.colorspace is None:
                continue
            if pix.colorspace.n != 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            im = Image.frombytes('RGBA' if pix.alpha else 'RGB', (pix.width, pix.height), pix.samples)
            if smask and not pix.alpha:
                m = fitz.Pixmap(doc, smask)
                if (m.width, m.height) == im.size:
                    im = im.convert('RGBA')
                    im.putalpha(Image.frombytes('L', (m.width, m.height), m.samples))
            save(im.convert('RGBA'), os.path.join(out, f'{stem}_p{pno}_x{xref}_{pix.width}x{pix.height}.png'))
    if not seen:
        print(f'{pdf}: no embedded rasters (vector only: borrow the drawing idea, or render the page with pdftocairo)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('pdf-images'); p.add_argument('pdf'); p.add_argument('out'); p.add_argument('--min', type=int, default=64)
    p = sub.add_parser('cutout'); p.add_argument('inp'); p.add_argument('out')
    p.add_argument('--lo', type=int, default=232); p.add_argument('--hi', type=int, default=250)
    p.add_argument('--max-h', type=int); p.add_argument('--pad', type=int, default=2)
    p = sub.add_parser('icon'); p.add_argument('inp'); p.add_argument('out')
    p.add_argument('--side', type=int, default=256); p.add_argument('--pad', type=int, default=4)
    p = sub.add_parser('tint'); p.add_argument('inp'); p.add_argument('out')
    p.add_argument('--dark', required=True); p.add_argument('--light', default='#ffffff')
    p = sub.add_parser('glyph'); p.add_argument('inp'); p.add_argument('out'); p.add_argument('--bg', type=int, default=244)
    p = sub.add_parser('svg'); p.add_argument('inp'); p.add_argument('out')
    p.add_argument('--scale', type=float, default=24); p.add_argument('--pad', type=int, default=4)
    a = ap.parse_args()
    if a.cmd == 'pdf-images':
        pdf_images(a.pdf, a.out, a.min)
    elif a.cmd == 'cutout':
        im = crop_to_alpha(white_to_alpha(Image.open(a.inp), a.lo, a.hi), a.pad)
        if a.max_h and im.height > a.max_h:
            im = im.resize((round(im.width * a.max_h / im.height), a.max_h), Image.LANCZOS)
        save(im, a.out)
    elif a.cmd == 'icon':
        save(shrink(crop_to_alpha(Image.open(a.inp).convert('RGBA'), a.pad), a.side), a.out)
    elif a.cmd == 'tint':
        save(role_tint(Image.open(a.inp), a.dark, a.light), a.out)
    elif a.cmd == 'glyph':
        save(crop_to_alpha(glyph(Image.open(a.inp), a.bg), 1), a.out)
    elif a.cmd == 'svg':
        pix = fitz.open(a.inp)[0].get_pixmap(matrix=fitz.Matrix(a.scale, a.scale), alpha=True)
        save(crop_to_alpha(Image.frombytes('RGBA', (pix.width, pix.height), pix.samples), a.pad), a.out)


if __name__ == '__main__':
    main()
