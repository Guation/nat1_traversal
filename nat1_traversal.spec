# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['nat1_traversal\\nat1_traversal.py'],
    pathex=[],
    binaries=[],
    datas=[('nat1_traversal', 'nat1_traversal')],
    hiddenimports=['requests', 'dnspython', 'tencentcloud-sdk-python-dnspod'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='nat1_traversal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
