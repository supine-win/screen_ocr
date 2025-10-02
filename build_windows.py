"""
Windows打包工具 - onedir目录模式
专用于构建目录分发模式的可执行程序
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

def build_executable():
    """构建onedir模式可执行文件"""
    print("\n开始构建onedir模式...")
    
    spec_file = "MonitorOCR_EasyOCR.spec"
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
            return verify_build()
        else:
            print("❌ 构建失败!")
            print("错误输出:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 构建过程出错: {e}")
        return False

def verify_build():
    """验证onedir构建结果"""
    print("\n验证onedir模式构建结果...")
    
    # onedir模式验证
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
    
    return create_release_package(exe_path, size_mb)

def create_release_package(exe_path, size_mb):
    """创建onedir发布包"""
    print("\n创建发布包...")
    
    # 为GitHub Actions准备release目录
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)
    
    try:
        # 复制整个onedir目录
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
        readme_content = create_readme_content(size_mb)
        (release_dir / "README.md").write_text(readme_content, encoding='utf-8')
        print("✅ README文档已创建")
        
    except Exception as e:
        print(f"⚠️  复制到release目录失败: {e}")
        return False
    
    print(f"\n✅ onedir模式构建完成!")
    print(f"📦 发布包位置: {release_dir.absolute()}")
    
    return True

def create_readme_content(size_mb):
    """创建README内容"""
    return f"""# MonitorOCR Windows版本 - 目录版本

## 版本信息
- 打包模式: onedir
- 文件大小: {size_mb:.1f} MB  
- OCR引擎: EasyOCR (纯净版本，已移除PaddleOCR)
- 模型策略: 用户手动下载（体积更小）
- exe文件和依赖文件分开存放

## 特性
- ✅ 启动快速（无需解压）
- ✅ 基于EasyOCR的高精度中英文识别
- ✅ 支持配置文件自定义设置
- ⚠️  文件较多，需要保持目录结构完整
- 启动时间: 2-5秒

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
3. 运行 MonitorOCR_EasyOCR/MonitorOCR_EasyOCR.exe
4. 配置文件: config.json

## 目录结构
```
MonitorOCR/
├── MonitorOCR_EasyOCR/
│   ├── MonitorOCR_EasyOCR.exe
│   └── (其他依赖文件)
├── config.json
└── easyocr_models/          # 手动创建并放入模型
    ├── craft_mlt_25k.pth
    └── zh_sim_g2.pth
```

## 性能建议
- 将程序放在SSD上可提高启动速度
- 添加杀毒软件白名单避免误报
- 启动速度快，无需解压

构建时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
构建模式: onedir
"""

def main():
    """主函数"""
    print("=" * 60)
    print("Windows EasyOCR onedir 打包工具")
    print("=" * 60)
    print("构建模式: onedir (目录分发模式)")
    print()
    
    # 检查模型
    if not check_models():
        return False
    
    # 准备构建环境
    if not prepare_build():
        return False
    
    # 构建onedir模式
    success = build_executable()
    
    if success:
        print(f"\n🎯 构建完成! 查看 release/ 目录")
        print("\n💡 onedir版本特点:")
        print("   - 启动快速，无需解压")
        print("   - 文件较多，需保持目录结构完整")
        print("   - 适合本地部署和快速启动")
    else:
        print(f"\n❌ 构建失败，请检查错误信息")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
