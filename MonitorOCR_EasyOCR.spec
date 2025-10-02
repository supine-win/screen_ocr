# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules
import sys
import os

# 收集EasyOCR和相关依赖
datas = [
    ('config.json', '.'),
    ('easyocr_offline_patch.py', '.'),  # 包含离线补丁
    ('exe_optimization.py', '.'),       # 包含exe优化模块
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
    'torchvision',
    'torchvision.transforms',
    'torch.nn',
    'torch.nn.functional',
    
    # CV和图像处理
    'cv2',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'numpy',
    'skimage',
    'skimage.measure',
    'scipy',
    'scipy.spatial',
    'scipy.spatial.distance',
    
    # 文本处理
    'arabic_reshaper',
    'bidi',
    
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

# 不再打包EasyOCR模型文件，让用户手动下载
# 创建空的模型目录结构
def create_model_directory_structure():
    """创建模型目录结构但不包含模型文件"""
    print("Creating EasyOCR model directory structure...")
    
    # 创建README文件说明如何下载模型
    readme_content = """# EasyOCR模型文件说明

请将以下模型文件放入此目录：

必需模型：
- craft_mlt_25k.pth (检测模型, 约79MB)
- zh_sim_g2.pth (中文识别模型, 约21MB)

可选模型：
- english_g2.pth (英文识别模型, 约14MB)

下载方式：
1. 运行 python prepare_models_easyocr.py
2. 从 ~/.EasyOCR/model/ 复制到此目录
3. 或从 https://github.com/JaidedAI/EasyOCR/releases 下载

注意：模型文件必须放在与exe同目录的 easyocr_models 文件夹中
"""
    
    # 创建临时README文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(readme_content)
        readme_path = f.name
    
    # 添加README到打包
    datas.append((readme_path, 'easyocr_models'))
    print("Added README.md for model directory")
    
    return True

# 创建模型目录结构（不包含实际模型）
create_model_directory_structure()

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

# onedir模式：创建目录而不是单文件
exe = EXE(
    pyz,
    a.scripts,
    [],  # 不包含 a.binaries 和 a.datas
    exclude_binaries=True,  # 关键：排除二进制文件，使用onedir模式
    name='MonitorOCR_EasyOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 创建COLLECT对象用于onedir分发
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MonitorOCR_EasyOCR'
)
