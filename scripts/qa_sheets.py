#!/usr/bin/env python3
"""Colour-blindness and grayscale check sheet: top = grayscale, bottom = deuteranopia (Machado et al. 2009, severity 1.0).

Run:  python qa_sheets.py <figure.png> <sheet.png>
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

M = np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]])


def to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def main(src, dst):
    im = Image.open(src).convert('RGB')
    a = np.asarray(im, dtype=float) / 255.0
    deut = Image.fromarray(np.round(np.clip(to_srgb(np.clip(to_linear(a) @ M.T, 0, 1)), 0, 1) * 255).astype(np.uint8), 'RGB')
    gray = im.convert('L').convert('RGB')
    gap = 14
    sheet = Image.new('RGB', (im.width, im.height * 2 + gap), 'white')
    sheet.paste(gray, (0, 0))
    sheet.paste(deut, (0, im.height + gap))
    ImageDraw.Draw(sheet).text((6, im.height + 1), 'top: grayscale  bottom: deuteranopia (Machado 2009)', fill=(90, 90, 90))
    sheet.save(dst)
    print('wrote', dst)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
