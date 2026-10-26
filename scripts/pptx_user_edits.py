#!/usr/bin/env python3
"""What did the user change by hand? Compares two decks shape by shape (read-only).

Per shape: kind, text (a picture: the asset whose bytes it matches), position and size to 0.1 pt, fill, outline and the first
run's font. Groups are compared by name: a group the user moved or resized is reported as one line with its offset and size
change, and the shapes inside are compared in the group's own child space, so a moved group does not list all its members.
Shapes that differ are paired by (kind, text), then by (kind, position), and printed as "changed" with what differs; what is
left over is printed as "only in the first deck" / "only in the second deck". A recolour, a moved group, a retyped label, a
resized icon all show up. Also prints which application saved each deck (the Application string the editor stored).

Run (python with python-pptx):  python pptx_user_edits.py <deck I delivered> <deck the user saved> [--assets DIR]
"""
import hashlib
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pptx import Presentation  # noqa: E402

from _deck import E, fill_desc, font_desc, group_xform, kind as _kind, known_assets, line_desc  # noqa: E402


def inventory(path, known):
    """(list of shape keys, {key: group path}, {group path: transform})."""
    keys, where, groups = [], {}, {}

    def walk(shapes, trail):
        for sh in shapes:
            if sh.shape_type == 6:
                groups[trail + '/' + sh.name] = group_xform(sh)
                walk(sh.shapes, trail + '/' + sh.name)
                continue
            txt = sh.text_frame.text.strip() if sh.has_text_frame else ''
            if sh.shape_type == 13:
                txt = known.get(hashlib.sha1(sh.image.blob).hexdigest(), 'picture (not in assets/)')
            geom = tuple(round(v / E, 1) for v in (sh.left, sh.top, sh.width, sh.height))
            key = (_kind(sh), txt, geom, fill_desc(sh), line_desc(sh), font_desc(sh))
            keys.append(key)
            where.setdefault(key, trail or '(top level)')

    walk(Presentation(path).slides[0].shapes, '')
    return keys, where, groups


def pair_up(a_left, b_left, fn):
    da, db = defaultdict(list), defaultdict(list)
    for k in a_left:
        if fn(k) is not None:
            da[fn(k)].append(k)
    for k in b_left:
        if fn(k) is not None:
            db[fn(k)].append(k)
    pairs = []
    for f in da:
        if len(da[f]) == 1 and len(db.get(f, [])) == 1:
            pairs.append((da[f][0], db[f][0]))
    for ka, kb in pairs:
        a_left.remove(ka)
        b_left.remove(kb)
    return pairs


def describe(ka, kb):
    parts = []
    if ka[1] != kb[1]:
        parts.append(f'text {ka[1][:30]!r} -> {kb[1][:30]!r}')
    ga, gb = ka[2], kb[2]
    if ga[:2] != gb[:2]:
        parts.append(f'moved ({ga[0]}, {ga[1]}) -> ({gb[0]}, {gb[1]}) [dx {gb[0] - ga[0]:+.1f}, dy {gb[1] - ga[1]:+.1f}]')
    if ga[2:] != gb[2:]:
        parts.append(f'size {ga[2]} x {ga[3]} -> {gb[2]} x {gb[3]}')
    for name, i in (('fill', 3), ('outline', 4), ('font', 5)):
        if ka[i] != kb[i]:
            parts.append(f'{name} {ka[i] or "-"} -> {kb[i] or "-"}')
    return '; '.join(parts)


def group_changes(ga, gb):
    out = []
    for name in sorted(set(ga) & set(gb)):
        ta, tb = ga[name], gb[name]
        if ta == tb:
            continue
        d = []
        for field, label in (('off', 'offset'), ('ext', 'size'), ('choff', 'child offset'), ('chext', 'child size')):
            if ta and tb and ta.get(field) != tb.get(field) and ta.get(field) and tb.get(field):
                a, b = ta[field], tb[field]
                d.append(f'{label} {(b[0] - a[0]) / E:+.1f}, {(b[1] - a[1]) / E:+.1f} pt')
        out.append(f'  group {name.split("/")[-1][:40]!r}: ' + ('; '.join(d) or 'transform changed') +
                   ('   (only the offset changed: the whole group was moved)' if d and all(x.startswith('offset') for x in d) else ''))
    return out


def main(a, b, assets):
    known = known_assets(assets)
    for p in (a, b):
        app = re.findall(r'<Application>([^<]*)</Application>', zipfile.ZipFile(p).read('docProps/app.xml').decode('utf-8', 'ignore'))
        print(f'{p}: saved by {app[0] if app else "?"}')
    ka, wa, ga = inventory(a, known)
    kb, wb, gb = inventory(b, known)
    only_a, only_b = Counter(ka) - Counter(kb), Counter(kb) - Counter(ka)
    a_left, b_left = list(only_a.elements()), list(only_b.elements())
    pairs = pair_up(a_left, b_left, lambda k: (k[0], k[1]) if k[1] else None)
    pairs += pair_up(a_left, b_left, lambda k: (k[0], k[2]))
    gchg = group_changes(ga, gb)
    gone, new = sorted(set(ga) - set(gb)), sorted(set(gb) - set(ga))
    n = len(pairs) + len(a_left) + len(b_left) + len(gchg) + len(gone) + len(new)
    if not n:
        print('  identical to 0.1 pt: nothing was changed by hand')
        return
    print(f'{len(pairs)} shape(s) changed, {len(a_left)} only in the first deck, {len(b_left)} only in the second deck, {len(gchg)} group(s) moved or resized')
    for line in gchg:
        print(line)
    for name in gone:
        print(f'  group only in the first deck: {name.split("/")[-1][:50]!r}')
    for name in new:
        print(f'  group only in the second deck: {name.split("/")[-1][:50]!r}')
    for x, y in sorted(pairs, key=lambda p: (p[0][2][1], p[0][2][0])):
        print(f'  changed      {x[0]:<10} {(x[1] or "")[:34]!r:<38} in {wa.get(x, "")[:28].split("/")[-1]!r}: {describe(x, y)}')
    for label, left, where in (('first only ', a_left, wa), ('second only', b_left, wb)):
        for k in sorted(left, key=lambda k: (k[2][1], k[2][0])):
            print(f'  {label}  {k[0]:<10} {k[1][:34]!r:<38} x,y,w,h = {k[2]}  fill {k[3] or "-"}  outline {k[4] or "-"}  font {k[5] or "-"}')


if __name__ == '__main__':
    args = sys.argv[1:]
    assets = os.path.join(os.environ['FIG_DIR'], 'assets') if os.environ.get('FIG_DIR') else None
    if '--assets' in args:
        i = args.index('--assets')
        assets = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        raise SystemExit(__doc__)
    main(args[0], args[1], assets)
