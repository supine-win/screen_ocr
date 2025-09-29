#!/usr/bin/env python3
"""
真实场景测试 - 模拟用户遇到的实际问题
"""

from ocr_processor import OCRProcessor

def test_real_problem():
    """测试用户描述的真实问题场景"""
    print("=" * 60)
    print("测试真实问题场景")
    print("=" * 60)
    
    # 使用真实的配置
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
    
    # 模拟用户描述的场景：识别如： 位置波动（max）：123，位置波动（mix）： 321
    # 注意这里故意用了mix而不是min，这可能是OCR识别错误
    print("\n场景1：用户描述的原始问题")
    print("-" * 40)
    
    # OCR可能识别出的文本（可能有识别错误）
    real_ocr_texts = [
        "位置波动（max）：123",
        "位置波动（mix）：321",  # OCR可能把min识别为mix
    ]
    
    print(f"OCR识别结果: {real_ocr_texts}")
    
    # 测试当前逻辑
    result_max = processor._extract_field_value(real_ocr_texts, "位置波动 (max)")
    result_min = processor._extract_field_value(real_ocr_texts, "位置波动 (min)")
    
    print(f"位置波动 (max) 结果: {result_max}")
    print(f"位置波动 (min) 结果: {result_min}")
    
    if result_max == "123" and result_min == "321":
        print("❌ 问题依然存在：两个都是123")
    elif result_max == "123" and result_min == "321":
        print("✅ 问题已解决：正确区分")
    else:
        print(f"⚠️  意外结果：max={result_max}, min={result_min}")
    
    # 场景2：更复杂的混合文本
    print("\n场景2：复杂混合OCR文本")
    print("-" * 40)
    
    complex_texts = [
        "系统监控数据报告",
        "时间：2025-09-29 13:43",
        "位置波动（max）：123", 
        "位置波动（min）：321",
        "平均速度(rpm)：606.537",
        "最高速度(rpm)：652.313",
        "温度：25.5°C",
        "状态：正常"
    ]
    
    print(f"复杂OCR文本: {complex_texts}")
    
    # 测试所有字段
    results = {}
    for field_name in config['field_mappings'].keys():
        result = processor._extract_field_value(complex_texts, field_name)
        results[field_name] = result
        print(f"{field_name}: {result}")
    
    # 验证结果
    print("\n" + "=" * 60)
    print("问题分析")
    print("=" * 60)
    
    if results["位置波动 (max)"] == "123" and results["位置波动 (min)"] == "321":
        print("✅ max/min正确区分")
    elif results["位置波动 (max)"] == results["位置波动 (min)"]:
        print("❌ max/min识别为相同值，问题依然存在")
        print("可能的原因：")
        print("1. 正则模式太宽泛")
        print("2. 文本匹配顺序问题") 
        print("3. OCR识别错误导致字段名不匹配")
    else:
        print("⚠️  其他情况")
    
    return results

if __name__ == "__main__":
    test_real_problem()
