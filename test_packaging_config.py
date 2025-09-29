#!/usr/bin/env python3
"""
测试打包配置
验证模型文件和配置是否正确
"""

import os
import sys
from pathlib import Path

def test_packaged_environment():
    """模拟测试打包环境"""
    print("=" * 60)
    print("测试打包环境配置")
    print("=" * 60)
    
    # 模拟打包环境
    original_frozen = getattr(sys, 'frozen', False)
    original_meipass = getattr(sys, '_MEIPASS', None)
    
    # 创建测试目录结构
    test_meipass = Path("test_package_env")
    test_meipass.mkdir(exist_ok=True)
    
    # 创建模型目录
    models_dir = test_meipass / "easyocr_models"
    models_dir.mkdir(exist_ok=True)
    
    try:
        # 模拟设置
        sys.frozen = True
        sys._MEIPASS = str(test_meipass)
        
        # 复制现有模型（如果存在）
        home_models = Path.home() / ".EasyOCR" / "model"
        if home_models.exists():
            import shutil
            for model_file in home_models.glob("*.pth"):
                if "craft" in model_file.name or "sim" in model_file.name:
                    shutil.copy2(model_file, models_dir / model_file.name)
                    print(f"复制模型: {model_file.name}")
        else:
            # 创建假模型文件
            (models_dir / "craft_mlt_25k.pth").write_bytes(b"fake_detection_model")
            (models_dir / "zh_sim_g2.pth").write_bytes(b"fake_recognition_model")
            print("创建了测试模型文件")
        
        # 测试离线补丁
        print("\n测试离线补丁...")
        try:
            # 导入并测试离线补丁
            from easyocr_offline_patch import patch_easyocr_for_offline
            
            result = patch_easyocr_for_offline()
            print(f"离线补丁应用: {'✅' if result else '❌'}")
            
            # 检查环境变量
            print(f"EASYOCR_MODULE_PATH: {os.environ.get('EASYOCR_MODULE_PATH', 'Not set')}")
            print(f"EASYOCR_MODEL_PATH: {os.environ.get('EASYOCR_MODEL_PATH', 'Not set')}")
            
            return result
            
        except Exception as e:
            print(f"❌ 离线补丁测试失败: {e}")
            return False
    
    finally:
        # 恢复原始设置
        sys.frozen = original_frozen
        if original_meipass:
            sys._MEIPASS = original_meipass
        elif hasattr(sys, '_MEIPASS'):
            delattr(sys, '_MEIPASS')
        
        # 清理测试目录
        try:
            import shutil
            shutil.rmtree(test_meipass)
        except:
            pass

def test_model_files():
    """测试模型文件是否存在"""
    print("\n" + "=" * 40)
    print("检查EasyOCR模型文件")
    print("=" * 40)
    
    home_dir = Path.home()
    model_dir = home_dir / ".EasyOCR" / "model"
    
    required_models = [
        "craft_mlt_25k.pth",
        "zh_sim_g2.pth"
    ]
    
    if not model_dir.exists():
        print("❌ EasyOCR模型目录不存在")
        print(f"   期望路径: {model_dir}")
        print("   请运行: python prepare_models_easyocr.py")
        return False
    
    all_found = True
    for model in required_models:
        model_path = model_dir / model
        if model_path.exists():
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"✅ {model}: {size_mb:.1f} MB")
        else:
            print(f"❌ {model}: 缺失")
            all_found = False
    
    return all_found

def test_spec_file():
    """测试spec文件配置"""
    print("\n" + "=" * 40)
    print("检查PyInstaller配置")
    print("=" * 40)
    
    spec_file = Path("MonitorOCR_EasyOCR.spec")
    if not spec_file.exists():
        print("❌ spec文件不存在")
        return False
    
    # 检查spec文件内容
    spec_content = spec_file.read_text(encoding='utf-8')
    
    checks = [
        ("easyocr_offline_patch.py", "离线补丁包含"),
        ("easyocr_models", "模型目录配置"),
        ("craft_mlt_25k.pth", "检测模型配置"),
        ("zh_sim_g2.pth", "识别模型配置"),
    ]
    
    all_good = True
    for check, desc in checks:
        if check in spec_content:
            print(f"✅ {desc}")
        else:
            print(f"❌ {desc} - 未找到: {check}")
            all_good = False
    
    return all_good

def main():
    """主测试函数"""
    print("打包配置测试工具")
    print("=" * 60)
    
    # 检查是否在GitHub Actions环境中
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
    if is_github_actions:
        print("🔧 GitHub Actions环境检测到")
        print(f"   Runner OS: {os.environ.get('RUNNER_OS', 'Unknown')}")
        print(f"   Workflow: {os.environ.get('GITHUB_WORKFLOW', 'Unknown')}")
    
    # 测试模型文件
    models_ok = test_model_files()
    
    # 测试spec配置  
    spec_ok = test_spec_file()
    
    # 测试打包环境
    package_ok = test_packaged_environment()
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print("=" * 60)
    print(f"模型文件检查: {'✅' if models_ok else '❌'}")
    print(f"配置文件检查: {'✅' if spec_ok else '❌'}")
    print(f"打包环境测试: {'✅' if package_ok else '❌'}")
    
    if all([models_ok, spec_ok, package_ok]):
        print("\n🎉 所有测试通过！可以进行打包")
        if is_github_actions:
            print("\n✅ GitHub Actions环境就绪")
        else:
            print("\n下一步:")
            print("1. 运行: python build_windows_with_models.py")
    else:
        print("\n⚠️  存在问题，请先解决后再打包")
        
        if not models_ok:
            print("- 运行: python prepare_models_easyocr.py")
        if not spec_ok:
            print("- 检查MonitorOCR_EasyOCR.spec文件")
        if not package_ok:
            print("- 检查easyocr_offline_patch.py文件")
        
        # 在GitHub Actions中，测试失败应该退出
        if is_github_actions:
            sys.exit(1)
    
    return all([models_ok, spec_ok, package_ok])

if __name__ == "__main__":
    main()
