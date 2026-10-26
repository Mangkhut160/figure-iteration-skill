#!/usr/bin/env python3
"""Which pptx did the user save last, and is it open? (read-only)

usage: python latest_saved.py <folder> [--glob 'fig.v*.pptx']
Each figure has its own prefix in the delivery folder (e.g. fig.vN.pptx, fig2.vN.pptx, ...): pass that
figure's glob, otherwise another figure's newest deck is picked.
For every matching pptx, newest first: modification time; the Application string stored in docProps/app.xml (WPS
Presentation, Microsoft Office PowerPoint, ...; my own outputs carry python-pptx's template name 'Microsoft Macintosh
PowerPoint', so this column does not say who saved it: read the next two); whether core.xml carries an
author name (my outputs leave it empty, an editor writes the account name on every save); whether a lock file sits next to it
(~$<name> from WPS / Office, which drops up to two leading characters of a long name; .~lock.<name># from LibreOffice: the
deck is open in an editor, never write to it, never convert it in place); whether it was saved after the PDF of the same
name was rendered (= the user edited a version I delivered). Ends with the deck to patch and the next free version number.
"""
import glob
import os
import re
import sys
import time
import zipfile


def locked(path):
    folder, name = os.path.split(path)
    folder = folder or '.'
    if os.path.exists(os.path.join(folder, f'.~lock.{name}#')):
        return True
    return any(f.startswith('~$') and name.endswith(f[2:]) and len(name) - len(f[2:]) <= 2 for f in os.listdir(folder))


def info(path):
    z = zipfile.ZipFile(path)
    app = re.findall(r'<Application>([^<]*)</Application>', z.read('docProps/app.xml').decode('utf-8', 'ignore')) \
        if 'docProps/app.xml' in z.namelist() else []
    core = z.read('docProps/core.xml').decode('utf-8', 'ignore') if 'docProps/core.xml' in z.namelist() else ''
    named = any(re.search(rf'<{t}>[^<]+</{t}>', core) for t in ('dc:creator', 'cp:lastModifiedBy'))
    return (app[0] if app else '?'), named


def main(folder, pattern):
    files = [p for p in glob.glob(os.path.join(folder, pattern)) if not os.path.basename(p).startswith('~$')]
    if not files:
        raise SystemExit(f'no {pattern} in {folder}')
    files.sort(key=os.path.getmtime, reverse=True)
    print(f'{"file":<28} {"saved":<17} {"by":<22} {"author":<7} {"open":<5} after my render')
    for p in files:
        name = os.path.basename(p)
        app, named = info(p)
        lock = locked(p)
        pdf = os.path.splitext(p)[0] + '.pdf'
        after = '-' if not os.path.exists(pdf) else ('yes' if os.path.getmtime(p) > os.path.getmtime(pdf) + 5 else 'no')
        stamp = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(p)))
        print(f'{name:<28} {stamp:<17} {app[:22]:<22} {"set" if named else "empty":<7} {"YES" if lock else "no":<5} {after}')
    newest = files[0]
    nums = [int(m.group(1)) for m in (re.search(r'v(\d+)', os.path.basename(p)) for p in files) if m]
    print(f'\npatch a copy of: {os.path.normpath(newest)}')
    if locked(newest):
        print('  it is open in an editor (lock file): read it, never write to it or convert it in place')
    if nums:
        print(f'next version: v{max(nums) + 1}')


if __name__ == '__main__':
    args = sys.argv[1:]
    pat = 'fig.v*.pptx'
    if '--glob' in args:
        i = args.index('--glob')
        pat = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1:
        raise SystemExit(__doc__)
    main(args[0], pat)
