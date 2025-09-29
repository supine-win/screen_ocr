#!/usr/bin/env python3
"""
测试OCR processor是否能正常初始化
"""

import sys
import tempfile
import shutil
from pathlib import Path
from ocr_processor import OCRProcessor

def test_ocr_processor_init():
    """测试OCR处理器初始化"""
    print("=" * 50)
    print("测试OCR处理器初始化")
    print("=" * 50)
    
    # 基本配置 - 包含GPU设置
    config = {
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
        # 初始化OCR处理器
        print("正在初始化OCR处理器...")
        processor = OCRProcessor(config)
        
        # 检查初始化结果
        if processor.use_easyocr and processor.easyocr_reader:
            print("✅ EasyOCR初始化成功")
            print(f"   使用EasyOCR: {processor.use_easyocr}")
            
            # 尝试简单的OCR测试（如果有测试图片）
            print("\n如果需要测试OCR功能，请提供测试图片路径")
            
        elif processor.ocr:
            print("✅ PaddleOCR初始化成功（EasyOCR未使用）")
            print(f"   使用EasyOCR: {processor.use_easyocr}")
            
        else:
            print("❌ 所有OCR引擎初始化失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ OCR处理器初始化失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

def main():
    """主测试函数"""
    print("OCR处理器测试")
    print("=" * 60)
    
    # 测试OCR处理器
    success = test_ocr_processor_init()
    
    print("\n" + "=" * 60)
    print("测试结果总结:")
    print(f"OCR处理器初始化: {'✅' if success else '❌'}")
    
    if success:
        print("🎉 OCR处理器可以正常工作！")
    else:
        print("⚠️  OCR处理器初始化失败，请检查配置。")

if __name__ == "__main__":
    main()
