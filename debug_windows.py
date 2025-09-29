#!/usr/bin/env python3
"""
Windows打包调试脚本
用于诊断Windows exe中的模型和日志问题
"""

import os
import sys
import json
from pathlib import Path

def check_environment():
    """检查运行环境"""
    print("=" * 60)
    print("环境检查")
    print("=" * 60)
    
    print(f"Python版本: {sys.version}")
    print(f"可执行文件路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"是否打包环境: {getattr(sys, 'frozen', False)}")
    
    if getattr(sys, 'frozen', False):
        print(f"MEIPASS路径: {getattr(sys, '_MEIPASS', 'Not available')}")

def check_modules():
    """检查模块导入"""
    print("\n" + "=" * 60)
    print("模块导入检查")
    print("=" * 60)
    
    modules = [
        'easyocr',
        'torch',
        'torchvision', 
        'cv2',
        'numpy',
        'PIL',
        'logger_config',
        'model_path_manager'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}: 可用")
        except ImportError as e:
            print(f"❌ {module}: 导入失败 - {e}")
        except Exception as e:
            print(f"⚠️  {module}: 其他错误 - {e}")

def check_files():
    """检查文件结构"""
    print("\n" + "=" * 60)
    print("文件结构检查")
    print("=" * 60)
    
    # 检查当前目录
    print(f"\n当前目录内容 ({os.getcwd()}):")
    try:
        for item in os.listdir("."):
            path = Path(item)
            if path.is_file():
                size = path.stat().st_size / (1024*1024)
                print(f"  📄 {item}: {size:.1f} MB")
            else:
                print(f"  📁 {item}/")
    except Exception as e:
        print(f"无法读取目录: {e}")
    
    # 检查MEIPASS目录（打包环境）
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', '')
        print(f"\nMEIPASS目录内容 ({meipass}):")
        if meipass and Path(meipass).exists():
            try:
                # 查找关键文件
                key_patterns = ['*.pth', '*.json', 'easyocr*', 'config*']
                for pattern in key_patterns:
                    matches = list(Path(meipass).rglob(pattern))
                    if matches:
                        print(f"  模式 '{pattern}':")
                        for match in matches[:10]:  # 限制显示数量
                            rel_path = match.relative_to(Path(meipass))
                            if match.is_file():
                                size = match.stat().st_size / (1024*1024)
                                print(f"    📄 {rel_path}: {size:.1f} MB")
                            else:
                                print(f"    📁 {rel_path}/")
            except Exception as e:
                print(f"无法读取MEIPASS目录: {e}")

def test_logging():
    """测试日志系统"""
    print("\n" + "=" * 60)
    print("日志系统测试")  
    print("=" * 60)
    
    try:
        from logger_config import get_logger
        logger = get_logger(__name__)
        logger.info("日志系统测试消息")
        print("✅ 日志系统初始化成功")
        
        # 检查日志文件
        if getattr(sys, 'frozen', False):
            log_dir = Path(sys.executable).parent / "logs"
        else:
            log_dir = Path("logs")
        
        print(f"日志目录: {log_dir}")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            print(f"找到 {len(log_files)} 个日志文件:")
            for log_file in log_files:
                size = log_file.stat().st_size / 1024
                print(f"  📄 {log_file.name}: {size:.1f} KB")
        else:
            print("❌ 日志目录不存在")
            
    except Exception as e:
        print(f"❌ 日志系统错误: {e}")

def test_model_path():
    """测试模型路径"""
    print("\n" + "=" * 60)
    print("模型路径测试")
    print("=" * 60)
    
    try:
        from model_path_manager import ModelPathManager
        
        # 创建调试信息
        debug_info = ModelPathManager.create_debug_info()
        print("✅ 调试信息创建成功")
        
        # 获取模型路径
        model_path = ModelPathManager.get_easyocr_model_path()
        print(f"EasyOCR模型路径: {model_path}")
        
        if model_path and Path(model_path).exists():
            models = list(Path(model_path).glob("*.pth"))
            print(f"找到 {len(models)} 个模型文件:")
            for model in models:
                size = model.stat().st_size / (1024*1024)
                print(f"  🧠 {model.name}: {size:.1f} MB")
        else:
            print("❌ 模型路径不存在或为空")
            
    except Exception as e:
        print(f"❌ 模型路径测试错误: {e}")

def test_easyocr():
    """测试EasyOCR初始化"""
    print("\n" + "=" * 60)
    print("EasyOCR初始化测试")
    print("=" * 60)
    
    try:
        import easyocr
        print("✅ EasyOCR模块导入成功")
        
        # 尝试初始化
        print("正在初始化EasyOCR Reader...")
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=True)
        print("✅ EasyOCR Reader初始化成功")
        
        # 简单测试
        import numpy as np
        test_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        results = reader.readtext(test_image)
        print(f"✅ EasyOCR测试完成，识别结果: {len(results)} 个区域")
        
    except Exception as e:
        print(f"❌ EasyOCR测试失败: {e}")
        print(f"错误类型: {type(e).__name__}")

def main():
    """主函数"""
    print("Windows打包调试工具")
    print("诊断模型路径和日志问题")
    
    # 执行所有检查
    check_environment()
    check_modules()
    check_files()
    test_logging()
    test_model_path()
    test_easyocr()
    
    # 保存详细信息到文件
    try:
        debug_file = "debug_output.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("Windows打包调试输出\n")
            f.write("=" * 60 + "\n")
            f.write(f"Python版本: {sys.version}\n")
            f.write(f"可执行文件: {sys.executable}\n")
            f.write(f"工作目录: {os.getcwd()}\n")
            f.write(f"打包环境: {getattr(sys, 'frozen', False)}\n")
            
            if getattr(sys, 'frozen', False):
                f.write(f"MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}\n")
        
        print(f"\n✅ 调试信息已保存到: {debug_file}")
    except Exception as e:
        print(f"\n❌ 无法保存调试信息: {e}")
    
    print("\n" + "=" * 60)
    print("调试完成！")
    print("=" * 60)
    
    input("按回车键退出...")

if __name__ == "__main__":
    main()
