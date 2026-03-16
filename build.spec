# -*- mode: python ; coding: utf-8 -*-
import sys

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

a = Analysis(
    ["src/main.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PyQt5_sip",
        "tensorflow",
        "tensorflow_cpu",
        "tensorflow_intel",
        "keras",
        "torch",
        "torchvision",
        "torchaudio",
        "pandas",
        "pyarrow",
        "matplotlib",
        "scipy",
        "sklearn",
        "numba",
        "openpyxl",
        "sqlalchemy",
        "IPython",
        "jupyter",
        "h5py",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WindowsPDFTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WindowsPDFTool",
)
