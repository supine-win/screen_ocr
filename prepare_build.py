#!/usr/bin/env python3
"""
打包前准备脚本 - 检查并下载所需的OCR模型
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_easyocr_models():
    """检查并下载EasyOCR模型"""
    print("=" * 60)
    print("检查EasyOCR模型...")
    
    # EasyOCR模型目录
    home_dir = Path.home()
    easyocr_dir = home_dir / ".EasyOCR"
    model_dir = easyocr_dir / "model"
    
    # 需要的模型文件
    required_models = [
        "craft_mlt_25k.pth",  # 文本检测模型
        "zh_sim_g2.pth",      # 中文识别模型 (注意：文件名是zh_sim不是chinese_sim)
        # "english_g2.pth",   # 英文识别模型 (可选)
    ]
    
    # 检查模型是否存在
    missing_models = []
    existing_models = []
    
    for model in required_models:
        model_path = model_dir / model
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            existing_models.append(f"  ✓ {model} ({size_mb:.1f} MB)")
        else:
            missing_models.append(model)
    
    if existing_models:
        print("已存在的模型:")
        for model in existing_models:
            print(model)
    
    if missing_models:
        print(f"\n缺少 {len(missing_models)} 个模型文件:")
        for model in missing_models:
            print(f"  ✗ {model}")
        
        print("\n正在下载缺失的模型...")
        try:
            # 通过导入easyocr触发模型下载
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, download_enabled=True)
            print("✅ 模型下载完成！")
        except Exception as e:
            print(f"❌ 模型下载失败: {e}")
            return False
    else:
        print("\n✅ 所有EasyOCR模型都已准备就绪！")
    
    # 显示模型目录大小
    if model_dir.exists():
        total_size = sum(f.stat().st_size for f in model_dir.glob('**/*') if f.is_file())
        print(f"\nEasyOCR模型总大小: {total_size / (1024*1024):.1f} MB")
        print(f"模型位置: {model_dir}")
    
    return True

def check_paddle_models():
    """检查PaddleOCR模型（作为备选）"""
    print("\n" + "=" * 60)
    print("检查PaddleOCR模型（备选）...")
    
    home_dir = Path.home()
    paddlex_dir = home_dir / ".paddlex" / "official_models"
    
    paddle_models = [
        "PP-OCRv5_server_det",
        "PP-OCRv5_server_rec",
        "PP-LCNet_x1_0_doc_ori",
        "UVDoc",
    ]
    
    existing = []
    for model in paddle_models:
        model_path = paddlex_dir / model
        if model_path.exists():
            existing.append(f"  ✓ {model}")
    
    if existing:
        print("已存在的PaddleOCR模型:")
        for model in existing:
            print(model)
    else:
        print("  ⚠️  没有PaddleOCR模型（不影响使用，EasyOCR为主）")
    
    return True

def create_build_script():
    """创建打包脚本"""
    print("\n" + "=" * 60)
    print("创建打包脚本...")
    
    build_script = """#!/bin/bash
# MonitorOCR打包脚本

echo "开始打包MonitorOCR (with EasyOCR)..."

# 清理旧的打包文件
rm -rf build dist *.app

# 使用PyInstaller打包
pyinstaller MonitorOCR_EasyOCR.spec --clean

# 检查打包结果
if [ -d "dist/MonitorOCR_EasyOCR.app" ]; then
    echo "✅ 打包成功！"
    echo "应用位置: dist/MonitorOCR_EasyOCR.app"
    
    # 显示包大小
    du -sh dist/MonitorOCR_EasyOCR.app
    
    # 创建DMG（可选）
    # hdiutil create -volname "MonitorOCR" -srcfolder dist/MonitorOCR_EasyOCR.app -ov -format UDZO MonitorOCR.dmg
else
    echo "❌ 打包失败！"
    exit 1
fi
"""
    
    script_path = Path("build_app.sh")
    script_path.write_text(build_script)
    script_path.chmod(0o755)
    print(f"✅ 已创建打包脚本: {script_path}")
    
    return True

def check_dependencies():
    """检查Python依赖"""
    print("\n" + "=" * 60)
    print("检查Python依赖...")
    
    required_packages = {
        "easyocr": "easyocr",
        "torch": "torch",
        "torchvision": "torchvision",
        "opencv-python": "cv2",
        "flask": "flask",
        "PyInstaller": "PyInstaller",
    }
    
    missing = []
    for display_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  ✓ {display_name}")
        except ImportError:
            missing.append(display_name)
            print(f"  ✗ {display_name}")
    
    if missing:
        print(f"\n缺少 {len(missing)} 个依赖包:")
        print(f"请运行: pip install {' '.join(missing)}")
        return False
    
    print("\n✅ 所有依赖都已安装！")
    return True

def estimate_package_size():
    """估算打包后的大小"""
    print("\n" + "=" * 60)
    print("估算打包大小...")
    
    estimates = {
        "EasyOCR模型": 200,  # MB
        "PyTorch库": 150,
        "OpenCV": 50,
        "应用代码": 10,
        "其他依赖": 40,
    }
    
    total = sum(estimates.values())
    
    print("预计打包大小:")
    for component, size in estimates.items():
        print(f"  - {component}: ~{size} MB")
    print(f"\n总计: ~{total} MB")
    
    print("\n注意: 实际大小可能有所不同")
    print("提示: 可以使用UPX压缩减小体积，但可能影响启动速度")
    
    return True

def main():
    """主函数"""
    print("MonitorOCR 打包准备工具")
    print("=" * 60)
    
    # 检查各项
    checks = [
        ("检查Python依赖", check_dependencies),
        ("检查EasyOCR模型", check_easyocr_models),
        ("检查PaddleOCR模型", check_paddle_models),
        ("创建打包脚本", create_build_script),
        ("估算打包大小", estimate_package_size),
    ]
    
    all_passed = True
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {name}失败: {e}")
            all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有检查通过！可以开始打包了。")
        print("\n运行以下命令开始打包:")
        print("  ./build_app.sh")
        print("\n或者直接运行:")
        print("  pyinstaller MonitorOCR_EasyOCR.spec --clean")
    else:
        print("⚠️  有些检查未通过，请解决问题后重试。")
        sys.exit(1)

if __name__ == "__main__":
    main()
