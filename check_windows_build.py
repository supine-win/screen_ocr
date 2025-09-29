#!/usr/bin/env python3
"""
Windows打包检查脚本
验证EasyOCR模型是否正确包含在Windows打包中
"""

import os
import sys
from pathlib import Path

def check_easyocr_models_status():
    """检查EasyOCR模型状态"""
    print("=" * 60)
    print("EasyOCR模型检查")
    print("=" * 60)
    
    # 1. 检查用户目录的模型
    home_dir = Path.home()
    user_model_dir = home_dir / ".EasyOCR" / "model"
    
    print(f"\n1. 用户目录模型 ({user_model_dir}):")
    if user_model_dir.exists():
        models = list(user_model_dir.glob("*.pth"))
        if models:
            print(f"   ✅ 找到 {len(models)} 个模型文件:")
            for model in models:
                size_mb = model.stat().st_size / (1024 * 1024)
                print(f"      - {model.name}: {size_mb:.1f} MB")
        else:
            print("   ❌ 目录存在但没有模型文件")
    else:
        print("   ❌ 目录不存在")
    
    # 2. 检查本地复制的模型（用于打包）
    local_model_dir = Path("easyocr_models")
    
    print(f"\n2. 本地打包目录 ({local_model_dir}):")
    if local_model_dir.exists():
        models = list(local_model_dir.glob("*.pth"))
        if models:
            print(f"   ✅ 找到 {len(models)} 个模型文件:")
            for model in models:
                size_mb = model.stat().st_size / (1024 * 1024)
                print(f"      - {model.name}: {size_mb:.1f} MB")
        else:
            print("   ❌ 目录存在但没有模型文件")
    else:
        print("   ❌ 目录不存在")
    
    # 3. 检查打包后的可执行文件
    dist_paths = [
        Path("dist/MonitorOCR_EasyOCR.exe"),
        Path("release/MonitorOCR_EasyOCR.exe"),
    ]
    
    print(f"\n3. 打包后的可执行文件:")
    exe_found = False
    for exe_path in dist_paths:
        if exe_path.exists():
            exe_found = True
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ {exe_path}: {size_mb:.1f} MB")
            
            # 检查大小是否合理（包含模型应该>200MB）
            if size_mb > 200:
                print(f"      ✅ 大小合理，可能包含了模型")
            else:
                print(f"      ⚠️  文件较小，可能没有包含模型")
    
    if not exe_found:
        print("   ❌ 未找到打包的可执行文件")
    
    return True

def check_build_script():
    """检查构建脚本配置"""
    print("\n" + "=" * 60)
    print("构建脚本检查")
    print("=" * 60)
    
    # 检查build_windows_easyocr.py
    build_script = Path("build_windows_easyocr.py")
    if build_script.exists():
        content = build_script.read_text(encoding='utf-8')
        
        print(f"\n✅ 找到构建脚本: {build_script}")
        
        # 检查关键配置
        checks = {
            "复制EasyOCR模型": "easyocr_model_dir",
            "添加模型到打包": "--add-data=easyocr_models",
            "包含EasyOCR依赖": "easyocr",
            "包含torch依赖": "torch",
        }
        
        for check_name, keyword in checks.items():
            if keyword in content:
                print(f"   ✅ {check_name}: 已配置")
            else:
                print(f"   ❌ {check_name}: 未找到配置")
    else:
        print(f"❌ 构建脚本不存在: {build_script}")
    
    return True

def check_github_workflow():
    """检查GitHub Actions工作流"""
    print("\n" + "=" * 60)
    print("GitHub Actions工作流检查")
    print("=" * 60)
    
    workflow_file = Path(".github/workflows/build-windows.yml")
    if workflow_file.exists():
        content = workflow_file.read_text(encoding='utf-8')
        
        print(f"\n✅ 找到工作流文件: {workflow_file}")
        
        # 检查关键步骤
        checks = {
            "缓存EasyOCR模型": "Cache EasyOCR models",
            "准备模型": "prepare_models_easyocr.py",
            "构建脚本": "build_windows_easyocr.py",
            "上传产物": "MonitorOCR-Windows-EasyOCR",
        }
        
        for check_name, keyword in checks.items():
            if keyword in content:
                print(f"   ✅ {check_name}: 已配置")
            else:
                print(f"   ❌ {check_name}: 未找到配置")
    else:
        print(f"❌ 工作流文件不存在: {workflow_file}")
    
    return True

def generate_recommendations():
    """生成优化建议"""
    print("\n" + "=" * 60)
    print("📋 Windows打包建议")
    print("=" * 60)
    
    recommendations = [
        "1. 确保在打包前运行: python prepare_models_easyocr.py",
        "2. 验证easyocr_models目录包含必要的模型文件",
        "3. 使用--add-data参数确保模型被包含在exe中",
        "4. 考虑使用UPX压缩减小文件大小",
        "5. 在Windows环境测试打包后的exe是否能正确加载模型",
    ]
    
    for rec in recommendations:
        print(f"\n{rec}")
    
    print("\n" + "=" * 60)
    print("📝 模型文件清单")
    print("=" * 60)
    
    print("\n必需的EasyOCR模型文件:")
    print("  - craft_mlt_25k.pth (~79MB) - 文本检测")
    print("  - zh_sim_g2.pth (~21MB) - 中文识别")
    print("  - english_g2.pth (可选) - 英文识别")
    
    print("\n打包后预期大小:")
    print("  - 包含EasyOCR: ~400-500MB")
    print("  - 不含模型: ~150-200MB")

def main():
    """主函数"""
    print("Windows EasyOCR打包检查工具")
    print("=" * 60)
    
    # 执行检查
    check_easyocr_models_status()
    check_build_script()
    check_github_workflow()
    generate_recommendations()
    
    print("\n" + "=" * 60)
    print("✅ 检查完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
