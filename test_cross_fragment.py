#!/usr/bin/env python3
"""
测试跨片段匹配功能 - 解决OCR拆分字段的问题
"""

from ocr_processor import OCRProcessor

def test_cross_fragment_matching():
    """测试跨片段匹配功能"""
    print("=" * 60)
    print("测试跨片段匹配 - 解决OCR拆分字段问题")
    print("=" * 60)
    
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
    
    # 测试场景1：从日志看到的实际OCR片段分布
    print("\n场景1：根据日志的实际OCR片段分布")
    print("-" * 40)
    
    # 模拟日志中看到的OCR结果
    fragmented_texts = [
        '数据分析:',
        '平均速度',
        '(rpm):',
        '527.322',
        '最高速度',
        '(rpm):',
        '562.191',
        '最低速度',
        '(rpm):',
        '484.407',
        '速度偏差 (trpm):',
        '38.9814',
        '位置波动',
        '(max):',
        '152',
        '位置波动',  # 假设还有min的片段
        '(min):',
        '89'
    ]
    
    print("OCR片段:")
    for i, text in enumerate(fragmented_texts):
        print(f"  {i+1:2d}. '{text}'")
    
    print("\n测试各字段提取:")
    
    # 测试所有字段
    test_fields = [
        '平均速度 (rpm)',
        '最高速度 (rpm)', 
        '最低速度 (rpm)',
        '速度偏差 (rpm)',
        '位置波动 (max)',
        '位置波动 (min)'
    ]
    
    results = {}
    for field in test_fields:
        result = processor._extract_field_value(fragmented_texts, field)
        results[field] = result
        print(f"  {field}: {result}")
    
    # 验证结果
    print("\n" + "=" * 60)
    print("结果验证")
    print("=" * 60)
    
    expected = {
        '平均速度 (rpm)': '527.322',
        '最高速度 (rpm)': '562.191',
        '最低速度 (rpm)': '484.407',
        '速度偏差 (rpm)': '38.9814',
        '位置波动 (max)': '152',
        '位置波动 (min)': '89'
    }
    
    success_count = 0
    for field, expected_value in expected.items():
        actual_value = results.get(field)
        if actual_value == expected_value:
            print(f"✅ {field}: {actual_value}")
            success_count += 1
        elif actual_value is None:
            print(f"❌ {field}: 未找到 (期望: {expected_value})")
        else:
            print(f"⚠️  {field}: {actual_value} (期望: {expected_value})")
    
    print(f"\n总体结果: {success_count}/{len(expected)} 测试通过")
    
    if success_count == len(expected):
        print("🎉 跨片段匹配成功！所有字段都正确识别！")
    else:
        print("⚠️  部分字段仍有问题，需要进一步优化")
    
    return success_count == len(expected)

if __name__ == "__main__":
    test_cross_fragment_matching()
