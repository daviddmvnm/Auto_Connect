# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(".")
venv_site_packages = os.path.join(project_root, ".venv", "lib", "python3.10", "site-packages")

# Gender Guesser data file
gender_data_file = os.path.join(venv_site_packages, "gender_guesser", "data", "nam_dict.txt")

# Shared libpython to bundle
libpython_shared = "/usr/lib/x86_64-linux-gnu/libpython3.10.so.1.0"

# Data files to include
datas = [
    ('manual.txt', '.'),
    ('config.json', '.'),
    ('iconb.png', '.'),
    ('iconb1.png', '.'),
    ('iconb1.ico', '.'),
    ('models', 'models'),
    (gender_data_file, 'gender_guesser/data')
]

# Bundle libpython
binaries = [
    (libpython_shared, '.')
]

# Hidden imports
hiddenimports = [
    "PIL._tkinter_finder"
] + collect_submodules("functions")

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutoConnectv1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon='iconb1.png',
)

