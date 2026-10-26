"""Read-only helpers shared by pptx_inspect, pptx_user_edits and pptx_kit (python-pptx only).

Geometry: python-pptx gives a shape's x / y / w / h in the coordinate space of its parent. Inside a group that is the group's
child space; a group the user moved keeps its child space and only changes its own offset, so child coordinates stop being
page coordinates. page_geom() applies the enclosing groups' transforms (scale and shift; rotation and flips are ignored).
"""
import hashlib
import os

E = 12700
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'


def known_assets(assets):
    out = {}
    if assets and os.path.isdir(assets):
        for root, _, files in os.walk(assets):
            for fn in files:
                if fn.lower().endswith(('.png', '.jpg', '.jpeg')):
                    p = os.path.join(root, fn)
                    with open(p, 'rb') as fh:
                        out[hashlib.sha1(fh.read()).hexdigest()] = os.path.relpath(p, assets).replace(os.sep, '/')
    return out


def kind(sh):
    return str(sh.shape_type).split('.')[-1].split(' ')[0]


def fill_hex(sh):
    """Explicit RGB fill as upper-case hex, or None (no fill, theme colour, or painted by the theme style)."""
    v = sh._element.xpath('./p:spPr/a:solidFill/a:srgbClr/@val')
    return v[0].upper() if v else None


def fill_desc(sh):
    """Hex = explicit RGB; theme:<name> = palette colour set on the shape; style:<name> = painted by the theme style; none."""
    el = sh._element
    h = fill_hex(sh)
    if h:
        return h
    v = el.xpath('./p:spPr/a:solidFill/a:schemeClr/@val')
    if v:
        return 'theme:' + v[0]
    if el.xpath('./p:spPr/a:noFill'):
        return 'none'
    v = el.xpath('./p:style/a:fillRef/a:schemeClr/@val')
    if v and not el.xpath('./p:spPr/a:gradFill|./p:spPr/a:blipFill|./p:spPr/a:pattFill'):
        return 'style:' + v[0]
    return ''


def line_desc(sh):
    """'<colour>/<width pt>' of the shape's own outline ('' when it has none of its own)."""
    ln = sh._element.xpath('./p:spPr/a:ln')
    if not ln:
        return ''
    ln = ln[0]
    c = ln.xpath('./a:solidFill/a:srgbClr/@val')
    if c:
        col = c[0].upper()
    elif ln.xpath('./a:solidFill/a:schemeClr/@val'):
        col = 'theme:' + ln.xpath('./a:solidFill/a:schemeClr/@val')[0]
    elif ln.xpath('./a:noFill'):
        col = 'none'
    else:
        col = '?'
    w = ln.get('w')
    return f'{col}/{int(w) / E:.2f}' if w else col


def font_desc(sh):
    """First run's '<size>pt <font> <colour> [bold]' ('' when the shape has no text)."""
    r = sh._element.xpath('.//a:r/a:rPr')
    if not r:
        return ''
    r = r[0]
    parts = []
    if r.get('sz'):
        parts.append(f'{int(r.get("sz")) / 100:g}pt')
    lat = r.xpath('./a:latin/@typeface')
    if lat:
        parts.append(lat[0])
    col = r.xpath('./a:solidFill/a:srgbClr/@val')
    if col:
        parts.append(col[0].upper())
    if r.get('b') == '1':
        parts.append('bold')
    return ' '.join(parts)


def _xfrm(grp_el):
    x = grp_el.xpath('./p:grpSpPr/a:xfrm')
    if not x:
        return None
    x = x[0]
    g = lambda tag, a, b: (int(x.find(A + tag).get(a)), int(x.find(A + tag).get(b))) if x.find(A + tag) is not None else None
    return dict(off=g('off', 'x', 'y'), ext=g('ext', 'cx', 'cy'), choff=g('chOff', 'x', 'y'), chext=g('chExt', 'cx', 'cy'))


def group_xform(group_shape):
    """The group's transform as {'off','ext','choff','chext'} in EMU, or None."""
    return _xfrm(group_shape._element)


def group_shift(group_shape):
    """(dx, dy, sx, sy): the page position of a child-space point (x, y) is (x*sx + dx, y*sy + dy), in EMU for dx, dy."""
    t = _xfrm(group_shape._element)
    if not t or not all(t.values()):
        return 0, 0, 1.0, 1.0
    sx = t['ext'][0] / t['chext'][0] if t['chext'][0] else 1.0
    sy = t['ext'][1] / t['chext'][1] if t['chext'][1] else 1.0
    return t['off'][0] - t['choff'][0] * sx, t['off'][1] - t['choff'][1] * sy, sx, sy


def is_identity(group_shape):
    t = _xfrm(group_shape._element)
    return bool(t and t['off'] == t['choff'] and t['ext'] == t['chext'])


def page_geom(sh):
    """(x, y, w, h) in pt on the page, after the transforms of every enclosing group."""
    x, y, w, h = (v / E for v in (sh.left, sh.top, sh.width, sh.height))
    el = sh._element.getparent()
    while el is not None and el.tag == P + 'grpSp':
        t = _xfrm(el)
        if t and all(t.values()):
            sx = t['ext'][0] / t['chext'][0] if t['chext'][0] else 1.0
            sy = t['ext'][1] / t['chext'][1] if t['chext'][1] else 1.0
            x = t['off'][0] / E + (x - t['choff'][0] / E) * sx
            y = t['off'][1] / E + (y - t['choff'][1] / E) * sy
            w, h = w * sx, h * sy
        el = el.getparent()
    return x, y, w, h
