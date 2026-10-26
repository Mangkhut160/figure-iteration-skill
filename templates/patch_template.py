#!/usr/bin/env python3
"""vN: <one line: what this version changes>, on a copy of the pptx the user saved last.

Changes (the same list goes into brief.md §6 and the vN section of claims_vs_code.md):
  1. ...

Rules: argv[1] is a copy of the saved deck, argv[2] the new file (Kit.save refuses to overwrite). Find shapes by group
name, text, fill or picture, never by position (a deck without groups: K.slide stands for the group); new text and boxes are
clones of existing ones (same font and size as their neighbours); formulas through K.formula (real LaTeX); stop with a message
when a shape is not found exactly once (the user may have deleted or renamed it); print the numbers you chose, they go into
the brief. A group the user moved keeps its place: positions inside a group are in the group's child space, page_geom(sh)
gives page coordinates.
Run through make_from_saved.sh (it puts the skill's scripts on PYTHONPATH and sets FIG_DIR):
  bash $SK/scripts/make_from_saved.sh <saved pptx> <this script> <output stem> [--archive <figure>/vN]
"""
import os
import sys

from pptx import Presentation

if os.environ.get('FIGURE_ITERATION_SCRIPTS'):           # the skill's pptx_kit, not an older copy next to this script
    sys.path.insert(0, os.environ['FIGURE_ITERATION_SCRIPTS'])
from pptx_kit import Kit, FIG_DIR, geom, page_geom, put, shift, set_text, set_fill, set_line, put_text_in_cell, remove, fill_of, one, tw, pt  # noqa: E402,F401


def main(inp, outp):
    prs = Presentation(inp)
    K = Kit(prs)

    # Examples (delete what you do not need; the working directory is this script's folder, so build paths from FIG_DIR):
    # g = K.group('n:encoder ')                         # '<spec id> ' with the trailing space
    # title = K.text_of(g, 'Encoder')
    # x, y, w, h = geom(title)
    # shift(title, dx=-2.0)
    # tmpl = K.text_of(K.group('a:note '), 'a label')   # an existing label as the template (same font and size)
    # label = K.text_box(g, tmpl, 'new label', x=x, baseline=y + 20)
    # icon = K.add_picture(g, os.path.join(FIG_DIR, 'assets', 'icons', 'lock.png'), x=x + w + 3, y=y, h=10,
    #                      name='n:encoder lock', descr='fixed')
    # glyphs, (fw, fh, fd) = K.formula(g, r'x_t', x=x, baseline=y + 30, size=7)
    # print(f'label at x {x:.2f}, formula box {fw:.2f} x {fh + fd:.2f} pt')

    K.save(outp)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
