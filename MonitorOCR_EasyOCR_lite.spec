# -*- mode: python ; coding: utf-8 -*-
# 轻量级打包配置，减少不必要的依赖

from PyInstaller.utils.hooks import collect_all, collect_data_files
import sys
import os

# 基础数据文件
datas = [
    ('config.json', '.'),
]

binaries = []
hiddenimports = [
    # EasyOCR核心
    'easyocr',
    'easyocr.reader',
    
    # 基础依赖
    'cv2',
    'PIL',
    'numpy',
    'flask',
    'flask_cors',
    'tkinter',
]

# 收集EasyOCR最小依赖
tmp_ret = collect_data_files('easyocr')
datas += tmp_ret

# 添加EasyOCR模型
home_dir = os.path.expanduser("~")
easyocr_model_dir = os.path.join(home_dir, ".EasyOCR", "model")
if os.path.exists(easyocr_model_dir):
    # 只包含必要的模型文件
    models = ['craft_mlt_25k.pth', 'zh_sim_g2.pth']
    for model in models:
        model_path = os.path.join(easyocr_model_dir, model)
        if os.path.exists(model_path):
            datas.append((model_path, '.EasyOCR/model'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tensorboard',
        'notebook',
        'scipy.spatial.transform._rotation_groups',
        'IPython',
        'jupyter',
        'pytest',
    ],
    noarchive=False,
    optimize=2,  # 优化级别
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MonitorOCR_EasyOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 移除符号
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name='MonitorOCR_EasyOCR'
)

app = BUNDLE(
    coll,
    name='MonitorOCR_EasyOCR.app',
    icon=None,
    bundle_identifier='com.windsurf.monitorocr',
)
