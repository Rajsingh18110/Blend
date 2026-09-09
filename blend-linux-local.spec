# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('src/blend/templates', 'blend/templates'), ('src/blend/static', 'blend/static'), ('src/blend/blend_core/assets', 'blend/blend_core/assets'), ('src/blend/blend_core/views', 'blend/blend_core/views'), ('src/blend/blend_core/translations', 'blend/blend_core/translations'), ('src/blend/blend_core/data', 'blend/blend_core/data'), ('src/blend/blend_core/blend_config.yml', 'blend/blend_core'), ('src/blend/blend_core/limiter.toml', 'blend/blend_core'), ('src/blend/blend_core/sources', 'blend/blend_core/sources')]
binaries = []
hiddenimports = ['lxml.etree', 'lxml._elementpath', 'lxml.html', 'flask', 'gunicorn.glogging', 'gunicorn.workers.sync', 'httpx_socks', 'valkey']
tmp_ret = collect_all('lxml')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
ext_ret = collect_all('blend.blend_core.extensions')
datas += ext_ret[0]; binaries += ext_ret[1]; hiddenimports += ext_ret[2]


a = Analysis(
    ['run_blend.py'],
    pathex=['src'],
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
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='blend-linux-local',
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
