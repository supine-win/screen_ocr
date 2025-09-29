#!/usr/bin/env python3
"""
Windows打包脚本 - 包含EasyOCR模型
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil
import datetime

def check_models():
    """检查模型配置（模型不打包，用户手动下载）"""
    print("EasyOCR模型配置检查...")
    print("-" * 40)
    print("✅ 模型策略: 用户手动下载")
    print("   - exe不包含模型（体积更小）")
    print("   - 用户首次使用时下载模型")
    print("   - 模型放入 easyocr_models/ 目录")
    print("-" * 40)
    
    # 仅供参考，显示本地是否有模型
    local_model_dir = Path("easyocr_models")
    if local_model_dir.exists():
        models = list(local_model_dir.glob("*.pth"))
        if models:
            print(f"\n参考：本地有 {len(models)} 个模型文件（不会打包）")
            total_size = sum(m.stat().st_size for m in models) / (1024*1024)
            print(f"总大小: {total_size:.1f} MB")
    
    print("\n✅ 配置检查通过（模型由用户提供）")
    return True

def prepare_build():
    """准备打包环境"""
    print("\n准备打包环境...")
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print(f"✅ PyInstaller已安装: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller未安装")
        print("请运行: pip install pyinstaller")
        return False
    
    # 检查spec文件
    spec_file = Path("MonitorOCR_EasyOCR.spec")
    if not spec_file.exists():
        print(f"❌ 打包配置文件不存在: {spec_file}")
        return False
    
    print(f"✅ 打包配置文件: {spec_file}")
    return True

def build_executable():
    """构建可执行文件"""
    print("\n开始构建Windows可执行文件...")
    
    # 清理之前的构建
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        print("清理build目录...")
        shutil.rmtree(build_dir)
    
    if dist_dir.exists():
        print("清理dist目录...")
        shutil.rmtree(dist_dir)
    
    # 运行PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm", 
        "MonitorOCR_EasyOCR.spec"
    ]
    
    print(f"运行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 构建成功!")
            
            # 检查输出文件
            exe_path = dist_dir / "MonitorOCR_EasyOCR.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✅ 可执行文件: {exe_path}")
                print(f"   文件大小: {size_mb:.1f} MB")
                return True
            else:
                print("❌ 可执行文件未生成")
                return False
        else:
            print("❌ 构建失败!")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False

def verify_build():
    """验证构建结果"""
    print("\n验证构建结果...")
    
    exe_path = Path("dist/MonitorOCR_EasyOCR.exe")
    if not exe_path.exists():
        print("❌ 可执行文件不存在")
        return False
    
    print(f"✅ 可执行文件: {exe_path}")
    
    # 检查是否包含模型文件（通过检查文件大小）
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"   文件大小: {size_mb:.1f} MB")
    
    # 如果文件大小太小，可能没有包含模型
    if size_mb < 100:  # 预期包含模型的exe应该超过100MB
        print("⚠️  文件大小较小，可能未包含模型文件")
        return False
    
    print("✅ 文件大小正常，应该包含了模型文件")
    
    # 为GitHub Actions准备release目录
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    # 复制exe文件到release目录
    release_exe = release_dir / "MonitorOCR_EasyOCR.exe"
    try:
        shutil.copy2(exe_path, release_exe)
        print(f"✅ 文件已复制到: {release_exe}")
        
        # 复制配置文件
        config_file = Path("config.json")
        if config_file.exists():
            shutil.copy2(config_file, release_dir / "config.json")
            print("✅ 配置文件已复制")
        
        # 创建README
        readme_content = f"""# MonitorOCR Windows 版本

## 文件信息
- 可执行文件: MonitorOCR_EasyOCR.exe
- 文件大小: {size_mb:.1f} MB
- 模型策略: 用户手动下载（体积更小）

## 首次使用 - 下载模型
将以下模型文件下载到 `easyocr_models/` 目录：

**必需模型：**
- craft_mlt_25k.pth (检测模型, ~79MB)
- zh_sim_g2.pth (中文识别, ~21MB)

**下载方式：**
1. 自动下载：运行 `python prepare_models_easyocr.py`
2. 手动下载：从 https://github.com/JaidedAI/EasyOCR/releases

## 运行说明
1. 创建 `easyocr_models` 文件夹
2. 下载模型文件到该文件夹
3. 双击运行 MonitorOCR_EasyOCR.exe
4. 配置文件: config.json

## 特性
- ✅ 无需Python环境
- ✅ 下载模型后完全离线运行
- ✅ 支持中英文识别
- ✅ GPU可选配置
- ✅ 体积小巧（不含模型）

## 配置
编辑 config.json 文件:
```json
{{
  "ocr": {{
    "easyocr": {{
      "use_gpu": false,
      "model_storage_directory": "./easyocr_models"
    }}
  }}
}}
```

## 目录结构
```
MonitorOCR/
├── MonitorOCR_EasyOCR.exe
├── config.json
└── easyocr_models/          # 手动创建并放入模型
    ├── craft_mlt_25k.pth
    └── zh_sim_g2.pth
```

构建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        (release_dir / "README.md").write_text(readme_content, encoding='utf-8')
        print("✅ README文档已创建")
        
    except Exception as e:
        print(f"⚠️  复制到release目录失败: {e}")
        return False
    
    print("\n测试建议:")
    print("1. 在无Python环境的Windows机器上测试")
    print("2. 断开网络连接测试离线运行")
    print("3. 检查日志确认使用本地模型")
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("Windows EasyOCR 打包工具")
    print("=" * 60)
    
    # 检查模型
    if not check_models():
        return False
    
    # 准备构建环境
    if not prepare_build():
        return False
    
    # 构建可执行文件
    if not build_executable():
        return False
    
    # 验证构建结果
    if not verify_build():
        return False
    
    print("\n" + "=" * 60)
    print("🎉 打包成功!")
    print("=" * 60)
    print("输出文件: dist/MonitorOCR_EasyOCR.exe")
    print("注意: 请在Windows环境中测试离线运行")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
