#!/usr/bin/env python3
"""
测试GPU配置功能
"""

import json
from pathlib import Path
from ocr_processor import OCRProcessor

def test_gpu_config():
    """测试GPU配置读取"""
    print("=" * 60)
    print("测试GPU配置功能")
    print("=" * 60)
    
    # 测试配置1: 禁用GPU
    print("\n1. 测试GPU禁用配置:")
    config_cpu = {
        'language': 'ch',
        'field_mappings': {},
        'use_absolute_value': True,
        'use_gpu': False,  # PaddleOCR的GPU设置
        'easyocr': {
            'use_gpu': False,  # EasyOCR的GPU设置
            'verbose': True
        }
    }
    
    try:
        processor_cpu = OCRProcessor(config_cpu)
        print(f"✅ CPU模式初始化成功")
        print(f"   使用EasyOCR: {processor_cpu.use_easyocr}")
    except Exception as e:
        print(f"❌ CPU模式初始化失败: {e}")
    
    # 测试配置2: 启用GPU（如果有GPU的话）
    print("\n2. 测试GPU启用配置:")
    config_gpu = {
        'language': 'ch',
        'field_mappings': {},
        'use_absolute_value': True,
        'use_gpu': True,   # PaddleOCR的GPU设置
        'easyocr': {
            'use_gpu': True,   # EasyOCR的GPU设置
            'verbose': True
        }
    }
    
    try:
        processor_gpu = OCRProcessor(config_gpu)
        print(f"✅ GPU模式初始化成功")
        print(f"   使用EasyOCR: {processor_gpu.use_easyocr}")
    except Exception as e:
        print(f"⚠️  GPU模式初始化失败: {e}")
        print("   这可能是因为没有GPU或CUDA环境未正确配置")

def test_config_file_loading():
    """测试从配置文件加载GPU设置"""
    print("\n" + "=" * 60)
    print("测试配置文件GPU设置")
    print("=" * 60)
    
    config_file = Path("config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            ocr_config = config.get('ocr', {})
            use_gpu = ocr_config.get('use_gpu', False)
            easyocr_config = ocr_config.get('easyocr', {})
            easyocr_gpu = easyocr_config.get('use_gpu', False)
            
            print(f"配置文件PaddleOCR GPU设置: {use_gpu}")
            print(f"配置文件EasyOCR GPU设置: {easyocr_gpu}")
            
            # 使用配置文件初始化
            processor = OCRProcessor(ocr_config)
            print(f"✅ 使用配置文件初始化成功")
            print(f"   使用EasyOCR: {processor.use_easyocr}")
            
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
    else:
        print("⚠️  配置文件config.json不存在")

def main():
    """主测试函数"""
    print("GPU配置测试")
    print("=" * 60)
    
    # 测试GPU配置
    test_gpu_config()
    
    # 测试配置文件加载
    test_config_file_loading()
    
    print("\n" + "=" * 60)
    print("GPU配置说明:")
    print("- config.json中的'use_gpu': GPU总开关（影响PaddleOCR）")
    print("- config.json中的'easyocr.use_gpu': EasyOCR专用GPU设置")
    print("- 如果没有GPU或CUDA环境，请保持为false")
    print("- GPU模式需要安装对应的CUDA版本的PyTorch和PaddlePaddle")

if __name__ == "__main__":
    main()
