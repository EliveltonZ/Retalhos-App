# -*- mode: python ; coding: utf-8 -*-
# Gera dist\Update.exe (arquivo único, para poder substituir os arquivos do Retalhos enquanto roda).
# Uso: pyinstaller --noconfirm Update.spec

a = Analysis(
    ['updater.py'],
    pathex=[],
    binaries=[],
    datas=[('retalhos/resources', 'retalhos/resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pyodbc'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Update',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['retalhos\\resources\\icon_retalho.ico'],
)
