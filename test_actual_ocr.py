#!/usr/bin/env python3
"""
测试实际OCR处理 - 找出位置波动min字段丢失的真正原因
"""

import cv2
import numpy as np
from ocr_processor import OCRProcessor

def test_actual_ocr():
    """测试实际OCR处理流程"""
    print("=" * 60)
    print("测试实际OCR处理 - 诊断min字段丢失")
    print("=" * 60)
    
    # 使用实际配置
    config = {
        'field_mappings': {
            '平均速度 (rpm)': 'avg_speed',
            '最高速度 (rpm)': 'max_speed', 
            '最低速度 (rpm)': 'min_speed',
            '速度偏差 (rpm)': 'speed_deviation',
            '位置波动 (max)': 'position_deviation_max',
            '位置波动 (min)': 'position_deviation_min'
        }
    }
    
    processor = OCRProcessor(config)
    
    # 模拟真实场景：创建一个测试图像
    print("创建测试图像...")
    
    # 创建一个白色背景的测试图像
    height, width = 600, 800
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # 使用OpenCV添加文本 (模拟监控界面显示的数据)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    color = (0, 0, 0)  # 黑色
    thickness = 2
    
    # 添加各种数据文本
    texts = [
        ("平均速度 (rpm): 527.322", (50, 100)),
        ("最高速度 (rpm): 562.191", (50, 150)),
        ("最低速度 (rpm): 484.407", (50, 200)),
        ("速度偏差 (rpm): 38.9814", (50, 250)),
        ("位置波动（max）：152", (50, 300)),
        ("位置波动（min）：89", (50, 350)),
    ]
    
    for text, pos in texts:
        cv2.putText(img, text, pos, font, font_scale, color, thickness)
    
    # 保存测试图像
    cv2.imwrite("test_ocr_image.jpg", img)
    print("✅ 测试图像已保存为 test_ocr_image.jpg")
    
    # 使用OCR处理器处理图像
    print("\n开始OCR处理...")
    print("-" * 40)
    
    results = processor.process_image(img)
    
    print("\n" + "=" * 60)
    print("OCR处理结果分析")
    print("=" * 60)
    
    print(f"返回的结果: {results}")
    print(f"结果类型: {type(results)}")
    print(f"结果包含的键: {list(results.keys()) if isinstance(results, dict) else '不是字典'}")
    
    # 检查每个期望的字段
    expected_fields = [
        ('avg_speed', '平均速度 (rpm)', '527.322'),
        ('max_speed', '最高速度 (rpm)', '562.191'),
        ('min_speed', '最低速度 (rpm)', '484.407'),
        ('speed_deviation', '速度偏差 (rpm)', '38.9814'),
        ('position_deviation_max', '位置波动 (max)', '152'),
        ('position_deviation_min', '位置波动 (min)', '89'),
    ]
    
    print(f"\n字段检查:")
    for mapped_key, field_name, expected_value in expected_fields:
        if mapped_key in results:
            actual_value = results[mapped_key]
            status = "✅" if actual_value == expected_value else "⚠️"
            print(f"  {status} {field_name}: {actual_value} (期望: {expected_value})")
        else:
            print(f"  ❌ {field_name}: 字段缺失")
    
    # 特别关注位置波动字段
    print(f"\n🔍 位置波动字段详细检查:")
    max_val = results.get('position_deviation_max')
    min_val = results.get('position_deviation_min')
    
    print(f"  position_deviation_max: {max_val}")
    print(f"  position_deviation_min: {min_val}")
    
    if max_val is None and min_val is None:
        print("  ❌ 两个字段都丢失了")
    elif max_val is not None and min_val is None:
        print("  ❌ 只有max存在，min丢失了 (这是用户遇到的问题)")
    elif max_val is None and min_val is not None:
        print("  ❌ 只有min存在，max丢失了")
    else:
        print("  ✅ 两个字段都存在")
    
    return results

if __name__ == "__main__":
    test_actual_ocr()
