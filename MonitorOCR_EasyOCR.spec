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

# 添加EasyOCR模型文件（支持多种来源）
def add_easyocr_models():
    """添加EasyOCR模型文件到打包"""
    added_models = []
    
    # 方案1: 检查本地easyocr_models目录（用户自定义目录）
    local_model_dir = "easyocr_models"
    if os.path.exists(local_model_dir):
        print(f"Found local EasyOCR models in: {local_model_dir}")
        for model_file in os.listdir(local_model_dir):
            if model_file.endswith('.pth'):
                src_path = os.path.join(local_model_dir, model_file)
                datas.append((src_path, 'easyocr_models'))
                added_models.append(model_file)
                size_mb = os.path.getsize(src_path) / (1024*1024)
                print(f"Added local model: {model_file} ({size_mb:.1f} MB)")
    
    # 方案2: 如果本地目录没有模型，尝试用户的.EasyOCR目录
    if not added_models:
        home_dir = os.path.expanduser("~")
        easyocr_model_dir = os.path.join(home_dir, ".EasyOCR", "model")
        if os.path.exists(easyocr_model_dir):
            print(f"Found EasyOCR models in: {easyocr_model_dir}")
            
            required_models = ['craft_mlt_25k.pth', 'zh_sim_g2.pth', 'english_g2.pth']
            for model_name in required_models:
                model_path = os.path.join(easyocr_model_dir, model_name)
                if os.path.exists(model_path):
                    datas.append((model_path, 'easyocr_models'))
                    added_models.append(model_name)
                    size_mb = os.path.getsize(model_path) / (1024*1024)
                    print(f"Added home model: {model_name} ({size_mb:.1f} MB)")
    
    if not added_models:
        print("Warning: No EasyOCR models found!")
        print("Please ensure models are in:")
        print("  1. ./easyocr_models/ directory, or")
        print("  2. ~/.EasyOCR/model/ directory")
        print("Run 'python prepare_models_easyocr.py' to download models")
    else:
        print(f"Total models added: {len(added_models)}")
    
    return len(added_models) > 0

# 执行模型添加
add_easyocr_models()

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
