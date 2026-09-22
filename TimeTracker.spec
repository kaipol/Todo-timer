# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 应用代码从不 import numpy，它是被依赖扫描连带进来的
        'numpy',
        # 只用 Widgets/Core/Gui/Network，这些 Qt 模块没有引用
        'PyQt6.QtPdf',
        'PyQt6.QtPdfWidgets',
        'PyQt6.QtOpenGL',
        'PyQt6.QtOpenGLWidgets',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtBluetooth',
        'PyQt6.QtNfc',
        'PyQt6.QtPositioning',
        'PyQt6.QtSensors',
        'PyQt6.QtSerialPort',
        'PyQt6.QtWebChannel',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtXml',
        'PyQt6.QtDBus',
        'PyQt6.QtDesigner',
        'PyQt6.QtHelp',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        # PIL 只做内存位图转换，格式解码由 Qt 完成，编解码扩展不需要
        'PIL._avif',
        'PIL._webp',
        'PIL._imagingcms',
        'PIL._imagingtk',
        'PIL._imagingmath',
        'PIL._imagingft',
        # 测试与交互环境，运行时用不到
        'unittest',
        'pydoc',
        'pydoc_data',
        'doctest',
        'pdb',
        'tkinter',
    ],
    noarchive=False,
    optimize=0,
)

# 软件 OpenGL 渲染库只在没有显卡驱动时才用，Qt 会在缺失时回退到系统 opengl32.dll。
# 图片解码走 Qt 自带的 PNG/ICO/BMP，JPEG/WebP/TIFF 插件应用用不到。
_drop = ('opengl32sw.dll', 'qjpeg.dll', 'qwebp.dll', 'qtiff.dll',
         'qpdf.dll', 'qt6pdf.dll')
a.binaries = [b for b in a.binaries if not b[0].lower().endswith(_drop)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TimeTracker',
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
)
