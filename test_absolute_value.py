#!/usr/bin/env python3
"""
测试绝对值配置功能
"""

from ocr_processor import OCRProcessor

def test_absolute_value_config():
    """测试绝对值配置功能"""
    print("=" * 60)
    print("测试绝对值配置功能")
    print("=" * 60)
    
    # 测试数据包含正负数
    test_texts = [
        '位置波动',
        '(max): 152',
        '位置波动', 
        '(min): -178'
    ]
    
    print(f"测试数据: {test_texts}")
    
    # 测试1：启用绝对值（默认）
    print("\n测试1：启用绝对值 (use_absolute_value: true)")
    print("-" * 40)
    
    config_abs = {
        'field_mappings': {
            '位置波动 (max)': 'position_deviation_max',
            '位置波动 (min)': 'position_deviation_min'
        },
        'use_absolute_value': True
    }
    
    processor_abs = OCRProcessor(config_abs)
    
    result_max_abs = processor_abs._extract_field_value(test_texts, '位置波动 (max)')
    result_min_abs = processor_abs._extract_field_value(test_texts, '位置波动 (min)')
    
    print(f"max结果: {result_max_abs} (原始: 152)")
    print(f"min结果: {result_min_abs} (原始: -178)")
    
    # 测试2：禁用绝对值
    print("\n测试2：禁用绝对值 (use_absolute_value: false)")
    print("-" * 40)
    
    config_raw = {
        'field_mappings': {
            '位置波动 (max)': 'position_deviation_max',
            '位置波动 (min)': 'position_deviation_min'
        },
        'use_absolute_value': False
    }
    
    processor_raw = OCRProcessor(config_raw)
    
    result_max_raw = processor_raw._extract_field_value(test_texts, '位置波动 (max)')
    result_min_raw = processor_raw._extract_field_value(test_texts, '位置波动 (min)')
    
    print(f"max结果: {result_max_raw} (原始: 152)")
    print(f"min结果: {result_min_raw} (原始: -178)")
    
    # 验证结果
    print("\n" + "=" * 60)
    print("结果验证")
    print("=" * 60)
    
    print(f"启用绝对值:")
    print(f"  max: {result_max_abs} {'✅' if result_max_abs == '152' else '❌'}")
    print(f"  min: {result_min_abs} {'✅' if result_min_abs == '178' else '❌'} (期望: 178, 即|-178|)")
    
    print(f"\n禁用绝对值:")
    print(f"  max: {result_max_raw} {'✅' if result_max_raw == '152' else '❌'}")
    print(f"  min: {result_min_raw} {'✅' if result_min_raw == '-178' else '❌'} (期望: -178, 保留负号)")
    
    # 整体验证
    success_abs = (result_max_abs == '152' and result_min_abs == '178')
    success_raw = (result_max_raw == '152' and result_min_raw == '-178')
    
    if success_abs and success_raw:
        print("\n🎉 绝对值配置功能测试通过！")
        print("✅ 启用绝对值时正确取绝对值")
        print("✅ 禁用绝对值时保留原始数值（包括负号）")
        return True
    else:
        print("\n⚠️  绝对值配置功能测试失败")
        return False

if __name__ == "__main__":
    test_absolute_value_config()
