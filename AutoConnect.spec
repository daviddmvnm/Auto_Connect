# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules

project_root = os.path.abspath(".")
venv_site_packages = os.path.join(project_root, ".venv", "lib", "python3.10", "site-packages")

# Gender Guesser data file (if still used)
gender_data_file = os.path.join(venv_site_packages, "gender_guesser", "data", "nam_dict.txt")

# Data files to include (preserves structure)
datas = [
    ('manual.txt', '.'),
    ('config.json', '.'),
    ('images/iconb.png', 'images'),
    ('images/iconb1.png', 'images'),
    ('images/iconb1.ico', 'images'),
    ('models', 'models'),
]

# Optional: Include gender guesser data if used
if os.path.exists(gender_data_file):
    datas.append((gender_data_file, 'gender_guesser/data'))

# Hidden imports (PIL + your Pipeline package)
hiddenimports = [
    "PIL._tkinter_finder"
] + collect_submodules("Pipeline")

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutoConnect',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # no terminal window
    disable_windowed_traceback=False,
    icon='images/iconb1.png'  # use ICO for Windows, PNG for Linux
)
