#!/usr/bin/env python3
"""Remove the theme style references (<p:style>) that python-pptx puts on every autoshape and connector svg2pptx writes.

svg2pptx.py writes explicit fill, outline and `<a:effectLst/>` on each shape but leaves `<p:style>` in place, whose
effectRef idx=2 points at the theme's outer shadow. PowerPoint lets the empty effectLst win; LibreOffice does not
and draws a soft shadow under every shape. Fill, outline and effect are all explicit, so dropping the reference changes
nothing the figure needs and makes every reader draw the same thing. It also clears the python-pptx template's document
properties (a 2013 date, the library author as last modifier, "generated using python-pptx").

usage: pptx_strip_style.py deck.pptx [deck.pptx ...]      (rewritten in place: run it only on decks a script just wrote)
"""
import datetime
import os
import re
import shutil
import sys
import zipfile

from lxml import etree
from pptx import Presentation

NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'


def strip(path):
    tmp = path + '.tmp'
    removed = 0
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.fullmatch(r'ppt/slides/slide\d+\.xml', item.filename):
                root = etree.fromstring(data)
                for parent in root.iter('{%s}sp' % NS_P, '{%s}cxnSp' % NS_P):
                    for st in parent.findall('{%s}style' % NS_P):
                        parent.remove(st)
                        removed += 1
                data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
            zout.writestr(item, data)
    shutil.move(tmp, path)
    prs = Presentation(path)
    cp = prs.core_properties
    cp.author, cp.last_modified_by, cp.comments, cp.title = '', '', '', ''
    cp.created = cp.modified = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None, microsecond=0)
    prs.save(path)
    return removed


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for path in sys.argv[1:]:
        print(f'{os.path.basename(path)}: removed {strip(path)} style references')


if __name__ == '__main__':
    main()
