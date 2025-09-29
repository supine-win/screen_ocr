# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules
import sys
import os

# 收集EasyOCR和相关依赖
datas = [
    ('config.json', '.'),
    ('easyocr_offline_patch.py', '.'),  # 包含离线补丁
]

binaries = []
hiddenimports = [
    # EasyOCR相关
    'easyocr',
    'easyocr.detection',
    'easyocr.recognition', 
    'easyocr.utils',
    'easyocr.config',
    
    # PyTorch相关
    'torch',
    'torch._C',
    'torch._ops',
    'torchvision',
    'torchvision.ops',
    'torchvision.transforms',
    
    # 图像处理
    'cv2',
    'PIL',
    'PIL.Image',
    'numpy',
    'scipy',
    'scipy.ndimage',
    'scikit-image',
    'skimage',
    
    # Web服务
    'flask',
    'flask_cors',
    
    # GUI
    'tkinter',
    
    # 其他依赖
    'python_bidi',
    'shapely',
    'pyclipper',
    'ninja',
    
    # PaddleOCR作为备选
    'paddleocr',
    'paddle',
    'paddlex',
]

# 收集EasyOCR数据和模型
tmp_ret = collect_all('easyocr')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 收集PyTorch
tmp_ret = collect_all('torch')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 收集torchvision
tmp_ret = collect_all('torchvision')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 收集scipy
tmp_ret = collect_all('scipy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 收集scikit-image
tmp_ret = collect_all('skimage')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 收集PaddleOCR作为备选
tmp_ret = collect_all('paddleocr')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paddle')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('paddlex')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 添加EasyOCR模型文件（确保打包到正确位置）
home_dir = os.path.expanduser("~")
easyocr_model_dir = os.path.join(home_dir, ".EasyOCR", "model")
if os.path.exists(easyocr_model_dir):
    print(f"Found EasyOCR models in: {easyocr_model_dir}")
    # 将模型文件打包到 easyocr_models 目录（与代码中的路径一致）
    craft_model = os.path.join(easyocr_model_dir, 'craft_mlt_25k.pth')
    zh_model = os.path.join(easyocr_model_dir, 'zh_sim_g2.pth')
    
    if os.path.exists(craft_model):
        datas.append((craft_model, 'easyocr_models'))
        print(f"Added craft model: {craft_model}")
    
    if os.path.exists(zh_model):
        datas.append((zh_model, 'easyocr_models'))
        print(f"Added zh model: {zh_model}")
    
    # 如果有英文模型也包含
    en_model = os.path.join(easyocr_model_dir, 'english_g2.pth')
    if os.path.exists(en_model):
        datas.append((en_model, 'easyocr_models'))
        print(f"Added english model: {en_model}")
else:
    print(f"Warning: EasyOCR model directory not found at {easyocr_model_dir}")
    print("Please run prepare_models_easyocr.py to download models first")

a = Analysis(
    ['main.py'],
    pathex=[],
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
    name='MonitorOCR_EasyOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用UPX，避免压缩导致的问题
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 开启控制台以便查看调试信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS App Bundle
app = BUNDLE(
    exe,
    name='MonitorOCR_EasyOCR.app',
    icon=None,
    bundle_identifier='com.windsurf.monitorocr',
    info_plist={
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    }
)
