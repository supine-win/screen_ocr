#!/usr/bin/env python3
"""
测试EasyOCR模型修复
"""

import os
import sys
from pathlib import Path
from model_path_manager import ModelPathManager

def test_model_path_setup():
    """测试模型路径设置"""
    print("=" * 50)
    print("测试EasyOCR模型路径设置")
    print("=" * 50)
    
    # 检查是否在打包环境中
    is_packaged = getattr(sys, 'frozen', False)
    print(f"打包环境: {is_packaged}")
    
    if is_packaged:
        print(f"MEIPASS: {getattr(sys, '_MEIPASS', 'Not available')}")
    
    # 测试模型路径获取
    model_path = ModelPathManager.get_easyocr_model_path()
    print(f"EasyOCR模型路径: {model_path}")
    
    if model_path:
        model_dir = Path(model_path)
        if model_dir.exists():
            models = list(model_dir.glob("*.pth"))
            print(f"找到模型文件数量: {len(models)}")
            for model in models:
                size_mb = model.stat().st_size / (1024 * 1024)
                print(f"  - {model.name}: {size_mb:.1f} MB")
        else:
            print("❌ 模型目录不存在")
    
    # 测试环境设置
    print("\n" + "=" * 30)
    print("测试环境变量设置")
    print("=" * 30)
    
    success = ModelPathManager.setup_easyocr_environment()
    print(f"环境设置成功: {success}")
    
    # 显示关键环境变量
    env_vars = ['EASYOCR_MODULE_PATH', 'EASYOCR_MODEL_PATH', 'TORCH_HOME', 'HOME', 'USERPROFILE']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"{var}: {value}")
    
    # 测试模型结构设置
    print("\n" + "=" * 30)
    print("测试模型结构设置")
    print("=" * 30)
    
    structure_success = ModelPathManager.setup_easyocr_model_structure()
    print(f"模型结构设置成功: {structure_success}")
    
    # 测试参数获取
    print("\n" + "=" * 30)
    print("测试初始化参数")
    print("=" * 30)
    
    params = ModelPathManager.get_easyocr_reader_params()
    print(f"EasyOCR初始化参数: {params}")
    
    return model_path is not None

def test_easyocr_init():
    """测试EasyOCR初始化"""
    print("\n" + "=" * 50)
    print("测试EasyOCR初始化")
    print("=" * 50)
    
    try:
        import easyocr
        print("✅ EasyOCR导入成功")
        
        # 设置环境
        ModelPathManager.setup_easyocr_environment()
        ModelPathManager.setup_easyocr_model_structure()
        
        # 获取参数
        reader_params = ModelPathManager.get_easyocr_reader_params()
        
        # 基础参数
        base_params = {
            'lang_list': ['ch_sim', 'en'],
            'gpu': False,
            'verbose': True
        }
        
        # 合并参数
        base_params.update(reader_params)
        
        print(f"尝试使用参数初始化: {base_params}")
        
        # 尝试初始化
        reader = easyocr.Reader(**base_params)
        print("✅ EasyOCR初始化成功！")
        
        return True
        
    except ImportError:
        print("❌ EasyOCR未安装")
        return False
    except Exception as e:
        print(f"❌ EasyOCR初始化失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("EasyOCR模型修复测试")
    print("=" * 60)
    
    # 测试模型路径
    path_ok = test_model_path_setup()
    
    # 测试EasyOCR初始化（仅在模型路径OK时）
    if path_ok:
        init_ok = test_easyocr_init()
    else:
        print("⚠️  跳过EasyOCR初始化测试（模型路径未找到）")
        init_ok = False
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"模型路径设置: {'✅' if path_ok else '❌'}")
    print(f"EasyOCR初始化: {'✅' if init_ok else '❌'}")
    
    if path_ok and init_ok:
        print("🎉 所有测试通过！EasyOCR应该能使用打包的模型文件了。")
    else:
        print("⚠️  测试未完全通过，可能需要进一步调试。")
