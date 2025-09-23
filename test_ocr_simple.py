#!/usr/bin/env python3
"""
简单测试OCR处理器
"""

import cv2
import numpy as np
from config_manager import ConfigManager
from ocr_processor import OCRProcessor
from screenshot_manager import ScreenshotManager

def test_ocr_directly():
    """直接测试OCR处理器"""
    print("=== 直接测试OCR处理器 ===")
    
    try:
        # 初始化组件
        config_manager = ConfigManager()
        ocr_processor = OCRProcessor(config_manager.get_ocr_config())
        screenshot_manager = ScreenshotManager()
        
        print("✅ 组件初始化成功")
        print(f"当前字段映射: {ocr_processor.get_field_mappings()}")
        
        # 截取一个小区域的截图进行测试
        print("\n📸 截取测试区域...")
        screenshot = screenshot_manager.capture_region(100, 100, 800, 600)
        
        if screenshot is None:
            print("❌ 截图失败")
            return
            
        print(f"✅ 截图成功，尺寸: {screenshot.shape}")
        
        # 保存测试截图
        cv2.imwrite("test_screenshot.jpg", screenshot)
        print("✅ 测试截图已保存为 test_screenshot.jpg")
        
        # 进行OCR识别
        print("\n🔍 开始OCR识别...")
        results = ocr_processor.process_image(screenshot)
        
        print(f"\n📊 识别结果: {results}")
        
        if results:
            print("🎯 成功提取到字段:")
            for key, value in results.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️  未提取到任何字段值")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ocr_directly()
