# -*- mode: python ; coding: utf-8 -*-
# Gera dist\Retalhos\Retalhos.exe (modo pasta).  Uso: pyinstaller --noconfirm Retalhos.spec

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('retalhos/resources', 'retalhos/resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Retalhos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['retalhos\\resources\\icon_retalho.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Retalhos',
)
