# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules


block_cipher = None

repo_root = Path(__file__).resolve().parent.parent
entry = repo_root / "scripts" / "rural_mapper_launcher.py"

# Bundle important non-code assets
_datas = []
_datas += collect_data_files("streamlit")

# Keep relative layout so Flask finds templates/ and config_utils finds config/countries.json
_datas.append((str(repo_root / "templates"), "templates"))
_datas.append((str(repo_root / "config"), "config"))

# Streamlit + heavy deps often use dynamic imports
_hiddenimports = []
_hiddenimports += collect_submodules("streamlit")
_hiddenimports += collect_submodules("sklearn")
_hiddenimports += collect_submodules("pyarrow")
_hiddenimports += collect_submodules("geopandas")

# Pull in package data/binaries where needed
for pkg in ["streamlit", "pyarrow", "sklearn", "geopandas"]:
    try:
        bundle = collect_all(pkg)
        _datas += bundle.datas
        _hiddenimports += bundle.hiddenimports
    except Exception:
        pass

# Deduplicate
_hiddenimports = sorted(set(_hiddenimports))


a = Analysis(
    [str(entry)],
    pathex=[str(repo_root)],
    binaries=[],
    datas=_datas,
    hiddenimports=_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="rural-mapper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
