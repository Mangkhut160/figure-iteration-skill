"""Where the optional programs and sibling skills live on this machine. Only the standard library, so every script can import it."""
import glob
import os
import shutil


def figgenie_scripts():
    """figgenie-paper-diagram's scripts folder: $FIGGENIE_SCRIPTS, else ~/.codex, ~/.claude, ~/.agents under skills/."""
    for p in (os.environ.get('FIGGENIE_SCRIPTS', ''),
              *(os.path.expanduser(f'~/{d}/skills/figgenie-paper-diagram/scripts') for d in ('.codex', '.claude', '.agents'))):
        if p and os.path.isfile(os.path.join(p, 'measure_text.py')):
            return p
    return None


def soffice():
    """LibreOffice's soffice: $SOFFICE, the per-user and system-wide Windows installs, macOS, then PATH."""
    cands = [os.environ.get('SOFFICE', '')]
    for var, rest in (('LOCALAPPDATA', ('Programs', 'LibreOffice', 'program', 'soffice.exe')),
                      ('ProgramFiles', ('LibreOffice', 'program', 'soffice.exe')),
                      ('ProgramFiles(x86)', ('LibreOffice', 'program', 'soffice.exe'))):
        if os.environ.get(var):
            cands.append(os.path.join(os.environ[var], *rest))
    cands += ['/Applications/LibreOffice.app/Contents/MacOS/soffice', shutil.which('soffice') or '', shutil.which('libreoffice') or '']
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


TL_GLOBS = (os.path.join(os.path.expanduser('~'), 'texlive', '*', 'bin', '*'), '/usr/local/texlive/*/bin/*',
            'C:/texlive/*/bin/*', '/Library/TeX/texbin')


def tex_exe(name):
    """latex / dvisvgm: $TEXLIVE_BIN, then PATH, then the usual TeX Live install folders; None when not found."""
    exe = name + ('.exe' if os.name == 'nt' else '')
    tl = os.environ.get('TEXLIVE_BIN', '')
    if tl and os.path.isfile(os.path.join(tl, exe)):
        return os.path.join(tl, exe)
    found = shutil.which(name)
    if found:
        return found
    for pat in TL_GLOBS:
        for folder in sorted(glob.glob(pat), reverse=True):
            if os.path.isfile(os.path.join(folder, exe)):
                return os.path.join(folder, exe)
    return None
