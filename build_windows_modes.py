"""
Windows打包工具 - 支持onefile和onedir两种模式
onefile: 单文件exe，每次启动解压（体积小，启动慢）
onedir: 目录模式，一次解压永久使用（体积大，启动快）
"""

import os
import sys
import subprocess
import argparse
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
        print("❌ PyInstaller未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ PyInstaller安装完成")
    
    return True

def build_executable(mode="onefile"):
    """构建可执行文件
    
    Args:
        mode: "onefile" 或 "onedir"
    """
    print(f"\n开始构建{mode}模式...")
    
    if mode == "onefile":
        spec_file = "MonitorOCR_EasyOCR.spec"
        print("📦 使用onefile模式（单文件exe，每次启动解压）")
    else:
        spec_file = "MonitorOCR_EasyOCR_onedir.spec"  
        print("📂 使用onedir模式（目录分发，一次解压永久使用）")
    
    if not Path(spec_file).exists():
        print(f"❌ spec文件不存在: {spec_file}")
        return False
    
    # 清理之前的构建
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("🧹 清理build目录")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("🧹 清理dist目录")
    
    try:
        # 执行打包
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 构建成功!")
            return verify_build(mode)
        else:
            print("❌ 构建失败!")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False

def verify_build(mode):
    """验证构建结果"""
    print(f"\n验证{mode}模式构建结果...")
    
    if mode == "onefile":
        exe_path = Path("dist/MonitorOCR_EasyOCR.exe")
        if not exe_path.exists():
            print("❌ onefile可执行文件不存在")
            return False
        
        print(f"✅ onefile可执行文件: {exe_path}")
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"   文件大小: {size_mb:.1f} MB")
        
        if size_mb < 30:
            print("⚠️  文件大小过小，可能缺少必要组件")
            return False
        elif size_mb > 200:
            print("⚠️  文件大小较大，可能意外包含了模型文件")
        else:
            print("✅ 文件大小合理（不包含模型）")
            
    else:  # onedir
        exe_path = Path("dist/MonitorOCR_EasyOCR/MonitorOCR_EasyOCR.exe")
        dist_dir = Path("dist/MonitorOCR_EasyOCR")
        
        if not exe_path.exists():
            print("❌ onedir可执行文件不存在")
            return False
            
        if not dist_dir.exists():
            print("❌ onedir分发目录不存在")
            return False
        
        print(f"✅ onedir可执行文件: {exe_path}")
        
        # 统计目录大小
        total_size = 0
        file_count = 0
        for file_path in dist_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1
        
        size_mb = total_size / (1024 * 1024)
        print(f"   目录总大小: {size_mb:.1f} MB")
        print(f"   文件数量: {file_count}")
        print("✅ onedir模式构建完成")
    
    return create_release_package(mode, exe_path, size_mb)

def create_release_package(mode, exe_path, size_mb):
    """创建发布包"""
    print("\n创建发布包...")
    
    # 为GitHub Actions准备release目录
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    try:
        if mode == "onefile":
            # 复制单个exe文件
            release_exe = release_dir / "MonitorOCR_EasyOCR.exe"
            shutil.copy2(exe_path, release_exe)
            print(f"✅ 文件已复制到: {release_exe}")
            
        else:  # onedir
            # 复制整个目录
            dist_dir = exe_path.parent
            release_app_dir = release_dir / "MonitorOCR_EasyOCR"
            if release_app_dir.exists():
                shutil.rmtree(release_app_dir)
            shutil.copytree(dist_dir, release_app_dir)
            print(f"✅ 目录已复制到: {release_app_dir}")
        
        # 复制配置文件
        config_file = Path("config.json")
        if config_file.exists():
            shutil.copy2(config_file, release_dir / "config.json")
            print("✅ 配置文件已复制")
        
        # 创建README
        readme_content = create_readme_content(mode, size_mb)
        (release_dir / "README.md").write_text(readme_content, encoding='utf-8')
        print("✅ README文档已创建")
        
    except Exception as e:
        print(f"⚠️  复制到release目录失败: {e}")
        return False
    
    print(f"\n✅ {mode}模式构建完成!")
    print(f"📦 发布包位置: {release_dir.absolute()}")
    
    return True

def create_readme_content(mode, size_mb):
    """创建README内容"""
    mode_desc = {
        "onefile": {
            "title": "单文件版本",
            "desc": "所有依赖打包在一个exe中",
            "pros": "✅ 文件单一，便于分发",
            "cons": "⚠️  每次启动需要解压（首次启动较慢）",
            "startup": "首次启动: 15-30秒，后续启动: 5-10秒"
        },
        "onedir": {
            "title": "目录版本", 
            "desc": "exe文件和依赖文件分开存放",
            "pros": "✅ 启动快速（无需解压）",
            "cons": "⚠️  文件较多，需要保持目录结构完整",
            "startup": "启动时间: 2-5秒"
        }
    }
    
    info = mode_desc[mode]
    
    return f"""# MonitorOCR Windows版本 - {info['title']}

## 版本信息
- 打包模式: {mode}
- 文件大小: {size_mb:.1f} MB
- 模型策略: 用户手动下载（体积更小）
- {info['desc']}

## 特性对比
- {info['pros']}
- {info['cons']}
- 启动性能: {info['startup']}

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
3. {"双击运行 MonitorOCR_EasyOCR.exe" if mode == "onefile" else "运行 MonitorOCR_EasyOCR/MonitorOCR_EasyOCR.exe"}
4. 配置文件: config.json

## 目录结构
```
MonitorOCR/
├── {"MonitorOCR_EasyOCR.exe" if mode == "onefile" else "MonitorOCR_EasyOCR/"}
{"" if mode == "onefile" else "│   ├── MonitorOCR_EasyOCR.exe"}
{"" if mode == "onefile" else "│   └── (其他依赖文件)"}
├── config.json
└── easyocr_models/          # 手动创建并放入模型
    ├── craft_mlt_25k.pth
    └── zh_sim_g2.pth
```

## 性能建议
- 将程序放在SSD上可提高启动速度
- 添加杀毒软件白名单避免误报
- {"第一次启动较慢属正常现象" if mode == "onefile" else "启动速度显著优于onefile版本"}

构建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
构建模式: {mode}
"""

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Windows打包工具 - 支持onefile和onedir模式')
    parser.add_argument('--mode', choices=['onefile', 'onedir', 'both'], 
                       default='both', help='打包模式选择')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Windows EasyOCR 多模式打包工具")
    print("=" * 60)
    print(f"构建模式: {args.mode}")
    print()
    
    # 检查模型
    if not check_models():
        return False
    
    # 准备构建环境
    if not prepare_build():
        return False
    
    success = True
    
    if args.mode == 'onefile':
        success = build_executable('onefile')
    elif args.mode == 'onedir':
        success = build_executable('onedir')
    else:  # both
        print("\n🚀 构建两种模式...")
        success1 = build_executable('onefile')
        success2 = build_executable('onedir') 
        success = success1 and success2
        
        if success:
            print(f"\n🎉 两种模式都构建成功！")
            print("📦 onefile版本: 单文件，启动较慢但便于分发")
            print("📂 onedir版本: 目录分发，启动快速但文件较多")
    
    if success:
        print(f"\n🎯 构建完成! 查看 release/ 目录")
        print("\n💡 选择建议:")
        print("   - 网络分发 → 选择 onefile 版本")  
        print("   - 本地使用 → 选择 onedir 版本")
    else:
        print(f"\n❌ 构建失败，请检查错误信息")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
