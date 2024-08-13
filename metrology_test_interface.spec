# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 12:36:26 2024

@author: tbates
"""

# metrology_test_interface.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['MetrologyTestInterface.py'],
    pathex=['.'],
    binaries=[('Automation1C.dll', '.'), ('Automation1C64.dll', '.'), ('Automation1Compiler.dll', '.'), ('Automation1Compiler64.dll', '.')],
    datas=[
        ('AerotechDataCal.py', '.'), 
        ('AerotechFormat.py', '.'), 
        ('AerotechPDF.py', '.'), 
        ('AngularTest.py', '.'), 
        ('Logger.py', '.'), 
        ('RS232.py', '.'), 
        ('RotaryCalTest.py', '.')
    ],
    hiddenimports=['matplotlib.backends.backend-pdf'],
    hookspath=[],
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
    [],
    exclude_binaries=True,
    name='MetrologyTestInterface',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MetrologyTestInterface',
)
