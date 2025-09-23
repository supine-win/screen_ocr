#!/usr/bin/env python3
"""
创建测试图像来验证OCR功能
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_test_image():
    """创建包含测试字段的图像"""
    # 创建白色背景
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # 尝试使用系统字体
    try:
        # macOS中文字体
        font = ImageFont.truetype('/System/Library/Fonts/PingFang.ttc', 40)
    except:
        try:
            # 备用字体
            font = ImageFont.truetype('/System/Library/Fonts/Arial.ttf', 40)
        except:
            # 默认字体
            font = ImageFont.load_default()
    
    # 添加测试文本
    test_texts = [
        "平均速度: 85.6 km/h",
        "最高速度: 120.3 km/h", 
        "最低速度: 45.2 km/h",
        "速度偏差: 12.8 km/h",
        "位置波动(max): 2.5 mm",
        "位置波动(min): 0.8 mm"
    ]
    
    y_start = 50
    for i, text in enumerate(test_texts):
        y = y_start + i * 80
        draw.text((50, y), text, fill='black', font=font)
    
    # 保存图像
    img.save('test_data_image.jpg')
    print("✅ 测试图像已创建: test_data_image.jpg")
    
    # 转换为OpenCV格式进行测试
    cv_img = cv2.imread('test_data_image.jpg')
    return cv_img

def test_with_created_image():
    """使用创建的图像测试OCR"""
    from config_manager import ConfigManager
    from ocr_processor import OCRProcessor
    
    print("=== 测试自创建图像的OCR ===")
    
    # 创建测试图像
    test_image = create_test_image()
    
    # 初始化OCR处理器
    config_manager = ConfigManager()
    ocr_processor = OCRProcessor(config_manager.get_ocr_config())
    
    print(f"当前字段映射: {ocr_processor.get_field_mappings()}")
    
    # 进行OCR识别
    print("\n🔍 开始OCR识别...")
    results = ocr_processor.process_image(test_image)
    
    print(f"\n📊 识别结果: {results}")
    
    if results:
        print("🎯 成功提取到字段:")
        for key, value in results.items():
            print(f"  {key}: {value}")
    else:
        print("⚠️  未提取到任何字段值")

if __name__ == "__main__":
    test_with_created_image()
