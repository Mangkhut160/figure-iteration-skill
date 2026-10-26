#!/usr/bin/env python3
"""Skeleton of the from-scratch route: writes fig.svg and spec.json for one figure (run it through scripts/make_draft.sh).

Copy this file to <figure folder>/tools/build_<name>.py and replace the CONTENT block. Everything is in pt (1 SVG unit = 1 pt).
Page size, text sizes, ink and font come from figure.env through the environment (FIG_PAGE, FIG_SIZES, FIG_INK, FIG_FONT), so
they live in one place. What the skeleton gives you: tex() - a formula typeset by LaTeX and drawn as paths, with its measured
box; tw() - the width of a text in the figure's font; node(), edge() and legend() - the groups figgenie's checks expect
(ids n:<id>, e:<id>, a:<id>, legend). The example content is three boxes, an arrow chain, a dashed return line with a formula
label, and a legend: keep what you need, delete the rest, and keep every spec entry in step with the SVG group it describes.
Not covered here: bitmaps (an <image> in its node group, path relative to the figure folder; embed_fonts.py inlines it) and
containers, lanes and step badges (figgenie: references/spec-guide.md section 4).
"""
import json
import os
import sys

FIG = os.environ.get('FIG_DIR') or os.getcwd()
for p in (os.environ.get('FIGGENIE_SCRIPTS', ''), os.environ.get('FIGURE_ITERATION_SCRIPTS', '')):
    if p:
        sys.path.insert(0, p)
os.environ.setdefault('LATEX_CACHE', os.path.join(FIG, 'tools', 'latex_cache.json'))      # read by latex_math at import
import latex_math                                                                           # noqa: E402
from measure_text import width_of                                                           # noqa: E402
from place_text import metrics                                                              # noqa: E402

# ---- settings: figure.env and the paper's profile -------------------------------------------------------------------------
W, H = (float(v) for v in os.environ['FIG_PAGE'].lower().split('x'))      # make the width a multiple of 0.75 pt (Chromium rounds the page to CSS pixels)
SIZES = sorted(float(v) for v in os.environ['FIG_SIZES'].split(','))
S_SMALL, S_LABEL = SIZES[0], SIZES[1] if len(SIZES) > 1 else SIZES[0]    # annotations / labels: the only text sizes
FONT = os.environ.get('FIG_FONT', 'arial')                                # figgenie font key
STACK = "Arimo, 'Liberation Sans', Arial, Helvetica, sans-serif"          # the stack of that key (figgenie assets/fonts/fonts.json)
INK = '#' + os.environ.get('FIG_INK', '000000')
MUTED, OUTLINE = '#595959', '#595959'
ROLE_A, ROLE_B, ROLE_C = '#EDEDED', '#CFE2F3', '#D9EAD3'                  # example roles: take the colours and their meaning from the profile
BOX_W, MAIN_W, DASH_W = 0.5, 0.9, 0.5                                     # outline / main path / dashed line widths (profile)
FAMILY, VENUE_STYLE = 'systems', 'acm'                                    # <-- SET FROM THE PROFILE (placeholder values). figgenie spec meta: family systems -> venue_style acm|usenix; family ai -> meta.venue instead
COLUMN = 'single'                                                         # <-- SET FROM THE PROFILE: single | double

esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
tw = lambda s, size: width_of(s, FONT, size, False)[0]
out, nodes, edges, annots = [], [], [], []
add = out.append


def tex(t, size, x, base, anchor='start'):
    """(svg group, (x0, top, x1, bottom)) of a formula; x is its left edge, centre or right edge by `anchor`; base is the baseline."""
    v = latex_math.typeset([(t, size)])[(t, size)]
    x0 = x - v['w'] / 2 if anchor == 'middle' else (x - v['w'] if anchor == 'end' else x)
    g = (f'<g data-symbol="latex" data-tex="{esc(t)}" data-w="{v["w"]:.4f}" data-h="{v["h"]:.4f}" data-d="{v["d"]:.4f}" '
         f'transform="translate({x0:.3f} {base:.3f})" fill="{INK}">{v["body"]}</g>')
    return g, (x0, base - v['h'], x0 + v['w'], base + v['d'])


# ---- CONTENT: geometry ----------------------------------------------------------------------------------------------------
BY, BH = H * 0.2, H * 0.24                       # box row: top, height
MID = BY + BH / 2
MARGIN, BW = 6.0, W * 0.24
GAPX = (W - 2 * MARGIN - 3 * BW) / 2             # equal gaps between the boxes (the linter checks)
BOXES = [('in', 'Input', MARGIN, BW, ROLE_A, 'existing'), ('mod', 'Module', MARGIN + BW + GAPX, BW, ROLE_C, 'novel'),
         ('out', 'Output', MARGIN + 2 * (BW + GAPX), BW, ROLE_B, 'existing')]
HEAD = 1.0                                       # an arrow tip sits HEAD pt beyond the path end
CAP, _ = metrics(FONT, S_LABEL)                  # cap height of the label face: one baseline for the whole row
LABEL_BASE = MID + CAP / 2

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}" width="{W:g}pt" height="{H:g}pt" font-family="{STACK}" '
    f'font-size="{S_LABEL:g}" text-rendering="geometricPrecision" data-spec="figure" data-spec-version="1">')
add('<defs>'
    f'<marker id="arrow" markerUnits="userSpaceOnUse" markerWidth="5" markerHeight="4.4" refX="4" refY="2.2" orient="auto"><path d="M0 0 L5 2.2 L0 4.4 Z" fill="{INK}"/></marker>'
    f'<marker id="arrow-dash" markerUnits="userSpaceOnUse" markerWidth="4.4" markerHeight="4" refX="3.4" refY="2" orient="auto"><path d="M0 0 L4.4 2 L0 4 Z" fill="{MUTED}"/></marker>'
    '</defs>')

# ---- edges are painted before nodes ----------------------------------------------------------------------------------------
for a, b in (('in', 'mod'), ('mod', 'out')):
    xa = next(x + w for i, _, x, w, _, _ in BOXES if i == a)
    xb = next(x for i, _, x, w, _, _ in BOXES if i == b)
    add(f'<g id="e:e-{a}-{b}" data-kind="edge" data-from="{a}" data-to="{b}" data-edge-kind="data">'
        f'<path d="M{xa:.2f} {MID:.2f} H{xb - HEAD:.2f}" fill="none" stroke="{INK}" stroke-width="{MAIN_W}" marker-end="url(#arrow)"/></g>')
    edges.append({'id': f'e-{a}-{b}', 'from': a, 'to': b, 'kind': 'data', 'weight': 'main', 'from_side': 'right', 'to_side': 'left'})
# a dashed return line from the last box to the middle one, with a text and a formula label under it
LOOP_Y = BY + BH + H * 0.16
xo, xm = BOXES[2][2] + BOXES[2][3] / 2, BOXES[1][2] + BOXES[1][3] / 2
t1 = 'optional path'
_, fb = tex(r'\theta', S_LABEL, 0, LOOP_Y + 10)
lx = (xo + xm) / 2 - (tw(t1, S_SMALL) + 3 + (fb[2] - fb[0])) / 2
note_g, _ = tex(r'\theta', S_LABEL, lx + tw(t1, S_SMALL) + 3, LOOP_Y + 10)
add(f'<g id="e:e-return" data-kind="edge" data-from="out" data-to="mod" data-edge-kind="feedback">'
    f'<path d="M{xo:.2f} {BY + BH:.2f} V{LOOP_Y:.2f} H{xm:.2f} V{BY + BH + 0.8:.2f}" fill="none" stroke="{MUTED}" stroke-width="{DASH_W}" '
    f'stroke-dasharray="3 2" stroke-linejoin="miter" marker-end="url(#arrow-dash)"/>'
    f'<text x="{lx:.2f}" y="{LOOP_Y + 10:.2f}" font-size="{S_SMALL:g}" fill="{INK}">{t1}</text></g>')
edges.append({'id': 'e-return', 'from': 'out', 'to': 'mod', 'kind': 'feedback', 'style': 'dashed', 'weight': 'thin', 'label': t1,
              'from_side': 'bottom', 'to_side': 'bottom', 'route_hint': 'under the boxes; dashed = optional path'})
add(f'<g id="a:note" data-kind="annotation" data-anchor="e-return">{note_g}</g>')
annots.append({'id': 'note', 'text': r'\theta', 'anchor': 'e-return', 'kind': 'label', 'side': 'bottom'})

# ---- nodes -----------------------------------------------------------------------------------------------------------------
for i, (nid, label, x, w, fill, role) in enumerate(BOXES):
    add(f'<g id="n:{nid}" data-kind="node" data-role="{role}">'
        f'<rect x="{x:.2f}" y="{BY:.2f}" width="{w:.2f}" height="{BH:.2f}" rx="2" fill="{fill}" stroke="{OUTLINE}" stroke-width="{BOX_W}"/>'
        f'<text x="{x + w / 2:.2f}" y="{LABEL_BASE:.2f}" font-size="{S_LABEL:g}" text-anchor="middle" fill="{INK}">{label}</text></g>')
    n = {'id': nid, 'label': label, 'kind': 'module', 'role': role, 'order': i}
    if role == 'novel':
        n['emphasis'] = 'accent'
    nodes.append(n)

# ---- legend ----------------------------------------------------------------------------------------------------------------
items = [('a', 'type A', ROLE_A), ('b', 'type B', ROLE_B), ('c', 'type C', ROLE_C)]
SW_W, SW_H, SW_GAP, ITEM_GAP, LEG_BASE = 8.0, 6.0, 3.0, 12.0, H - 8.0
x = (W - sum(SW_W + SW_GAP + tw(lab, S_SMALL) for _, lab, _ in items) - ITEM_GAP * (len(items) - 1)) / 2
add('<g id="legend" data-kind="legend">')
for iid, lab, fill in items:
    add(f'<g id="legend:{iid}" data-kind="legend-item"><rect x="{x:.2f}" y="{LEG_BASE - 5.1:.2f}" width="{SW_W:g}" height="{SW_H:g}" rx="1" '
        f'fill="{fill}" stroke="{OUTLINE}" stroke-width="{BOX_W}"/>'
        f'<text x="{x + SW_W + SW_GAP:.2f}" y="{LEG_BASE:.2f}" font-size="{S_SMALL:g}" fill="{INK}">{lab}</text></g>')
    x += SW_W + SW_GAP + tw(lab, S_SMALL) + ITEM_GAP
add('</g>')
add('</svg>')
with open(os.path.join(FIG, 'fig.svg'), 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(out) + '\n')

# ---- spec: the contract figgenie's linter reads (references/spec-guide.md) -----------------------------------------------
meta = {'id': 'figure', 'title': 'Example figure', 'system': {'name': 'Example', 'one_liner': 'a three-module pipeline'},
        'figure_kind': 'whole-system', 'family': FAMILY, 'column': COLUMN, 'width_pt': W, 'max_height_pt': H,
        'template': 'pipeline', 'direction': 'left-right', 'panels': 1, 'palette': 'custom', 'font': FONT, 'step_markers': 'none',
        'language': 'en', 'version': 1, 'caption_draft': 'Replace with the caption.', 'open_questions': []}
if FAMILY == 'systems':
    meta['venue_style'] = VENUE_STYLE
spec = {'meta': meta, 'nodes': nodes, 'edges': edges, 'annotations': annots,
        'legend': {'mode': 'explicit', 'placement': 'below', 'items': [
            {'id': iid, 'label': lab, 'swatch': {'kind': 'fill', 'role': fill}} for iid, lab, fill in items]},
        'style_overrides': {
            'palette_roles': {'canvas': '#ffffff', 'module': ROLE_B, 'module-alt': [ROLE_A], 'accent': ROLE_C, 'stroke': OUTLINE,
                              'text': INK, 'text-muted': MUTED, 'arrow': INK, 'arrow-accent': INK, 'legend': '#ffffff'},
            'stroke_width_pt': {'container': BOX_W, 'box': BOX_W, 'main': MAIN_W},
            'font_size_pt': {'title': S_LABEL, 'label': S_LABEL, 'small': S_SMALL}, 'corner_radius_pt': 2}}
with open(os.path.join(FIG, 'spec.json'), 'w', encoding='utf-8') as fh:
    json.dump(spec, fh, indent=1, ensure_ascii=False)
print('wrote fig.svg and spec.json in', FIG)
