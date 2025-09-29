#!/usr/bin/env python3
"""
测试完整的process_image流程，验证绝对值配置
"""

import cv2
import numpy as np
from ocr_processor import OCRProcessor

def test_full_process_with_absolute_value():
    """测试完整流程的绝对值配置"""
    print("=" * 60)
    print("测试完整流程的绝对值配置")
    print("=" * 60)
    
    # 创建测试图像
    img = np.ones((400, 600, 3), dtype=np.uint8) * 255
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # 添加正负数数据
    cv2.putText(img, "Position Deviation", (50, 100), font, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "(max): 152", (50, 150), font, 1.0, (0, 0, 0), 2)
    cv2.putText(img, "(min): -178", (50, 200), font, 1.0, (0, 0, 0), 2)
    
    # 测试1：启用绝对值
    print("\n测试1：启用绝对值")
    print("-" * 30)
    
    config_abs = {
        'field_mappings': {
            '位置波动 (max)': 'position_deviation_max',
            '位置波动 (min)': 'position_deviation_min'
        },
        'use_absolute_value': True
    }
    
    processor_abs = OCRProcessor(config_abs)
    result_abs = processor_abs.process_image(img)
    
    print(f"结果: {result_abs}")
    
    # 测试2：禁用绝对值
    print("\n测试2：禁用绝对值")
    print("-" * 30)
    
    config_raw = {
        'field_mappings': {
            '位置波动 (max)': 'position_deviation_max',
            '位置波动 (min)': 'position_deviation_min'
        },
        'use_absolute_value': False
    }
    
    processor_raw = OCRProcessor(config_raw)
    result_raw = processor_raw.process_image(img)
    
    print(f"结果: {result_raw}")
    
    # 验证
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    max_val_abs = result_abs.get('position_deviation_max')
    min_val_abs = result_abs.get('position_deviation_min') 
    max_val_raw = result_raw.get('position_deviation_max')
    min_val_raw = result_raw.get('position_deviation_min')
    
    print(f"启用绝对值: max={max_val_abs}, min={min_val_abs}")
    print(f"禁用绝对值: max={max_val_raw}, min={min_val_raw}")
    
    # 分析结果
    if min_val_abs and min_val_raw:
        if min_val_abs != min_val_raw:
            print("✅ 绝对值配置正常工作：两种配置产生了不同的结果")
            
            # 进一步检查数值
            try:
                abs_min_num = float(min_val_abs)
                raw_min_num = float(min_val_raw)
                
                if abs_min_num > 0 and raw_min_num < 0:
                    print(f"✅ 绝对值处理正确：{raw_min_num} -> {abs_min_num}")
                else:
                    print(f"⚠️  数值处理可能有问题")
                    
            except ValueError:
                print("⚠️  无法解析数值")
        else:
            print("❌ 绝对值配置没有生效：两种配置产生相同结果")
    else:
        print("❌ 测试失败：某些数值为None")

if __name__ == "__main__":
    test_full_process_with_absolute_value()
