# -*- mode: python ; coding: utf-8 -*-
import sys
import os

# Detect the operating system at build time
if sys.platform == 'win32':
    icon_file = 'icons/b3_selic_pre.ico'
elif sys.platform == 'darwin':
    icon_file = 'icons/b3_selic_pre.icns'
else:
    icon_file = None  # Linux / Unix standard paths do not embed icons

# UPX does not support macOS binaries and may cause warnings
upx_enabled = sys.platform != 'darwin'

# Console window: useful for CLI on Linux/Windows, but macOS .app should not
# open a terminal when launched from Finder
console_enabled = sys.platform != 'darwin'

a = Analysis(
    ['b3_selic_pre.py'],
    pathex=[],
    binaries=[],
    datas=[('icons/b3_selic_pre.png', '.')],
    hiddenimports=[
        'tkinter',
        'PIL',
        'PIL._tkinter_finder',
        'matplotlib',
        'matplotlib.figure',
        'matplotlib.backends.backend_tkagg',
        'ctypes',
        'pyxclip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='b3-selic-pre',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=upx_enabled,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console_enabled,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# For macOS bundle packaging (.app container)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='b3-selic-pre.app',
        icon=icon_file,
        bundle_identifier='com.github.amaurycarvalho.b3-selic-pre',
        info_plist={
            'CFBundleShortVersionString': '0.5.1',
            'CFBundleVersion': '0.5.1',
            'NSHighResolutionCapable': True,
        },
    )

