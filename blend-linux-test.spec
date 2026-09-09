# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_blend.py'],
    pathex=[],
    binaries=[],
    datas=[('src/blend/templates', 'blend/templates'), ('src/blend/static', 'blend/static'), ('src/blend/blend_core/data/*.json', 'blend/blend_core/data'), ('src/blend/blend_core/data/*.txt', 'blend/blend_core/data'), ('src/blend/blend_core/blend_config.yml', 'blend/blend_core')],
    hiddenimports=['flask', 'gunicorn.glogging', 'gunicorn.workers.sync', 'lxml.etree', 'lxml._elementpath', 'lxml.html'],
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
    name='blend-linux-test',
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
