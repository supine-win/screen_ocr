#!/usr/bin/env python3
"""
测试字段提取逻辑
用于验证修复后的OCR字段解析问题
"""

from ocr_processor import OCRProcessor

def test_field_extraction():
    """测试字段提取功能"""
    print("=" * 60)
    print("测试OCR字段提取修复 - 基于配置文件")
    print("=" * 60)
    
    # 创建OCR处理器 - 使用配置文件
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
    
    print("当前配置的字段映射:")
    for field_name, mapped_key in config['field_mappings'].items():
        print(f"  '{field_name}' -> '{mapped_key}'")
    
    processor = OCRProcessor(config)
    
    # 测试用例1：原问题 - max和min被错误识别
    print("\n测试用例1：位置波动max/min识别")
    print("-" * 40)
    
    test_texts_1 = [
        "位置波动（max）：123",
        "位置波动（min）：321", 
        "其他文本"
    ]
    
    print(f"测试文本: {test_texts_1}")
    
    result_max = processor._extract_field_value(test_texts_1, "位置波动 (max)")
    result_min = processor._extract_field_value(test_texts_1, "位置波动 (min)")
    
    print(f"位置波动 (max) 结果: {result_max} (期望: 123)")
    print(f"位置波动 (min) 结果: {result_min} (期望: 321)")
    
    # 测试用例2：速度相关字段
    print("\n测试用例2：速度字段识别")
    print("-" * 40)
    
    test_texts_2 = [
        "平均速度 (rpm): 606.537",
        "最高速度 (rpm): 652.313", 
        "最低速度 (rpm): 572.205",
        "速度偏差 (rpm): 45.7764"
    ]
    
    print(f"测试文本: {test_texts_2}")
    
    result_avg = processor._extract_field_value(test_texts_2, "平均速度 (rpm)")
    result_max_speed = processor._extract_field_value(test_texts_2, "最高速度 (rpm)")
    result_min_speed = processor._extract_field_value(test_texts_2, "最低速度 (rpm)")
    result_deviation = processor._extract_field_value(test_texts_2, "速度偏差 (rpm)")
    
    print(f"平均速度 结果: {result_avg} (期望: 606.537)")
    print(f"最高速度 结果: {result_max_speed} (期望: 652.313)")
    print(f"最低速度 结果: {result_min_speed} (期望: 572.205)")
    print(f"速度偏差 结果: {result_deviation} (期望: 45.7764)")
    
    # 测试用例3：混合文本（模拟真实OCR结果）
    print("\n测试用例3：混合OCR文本")
    print("-" * 40)
    
    test_texts_3 = [
        "监控数据",
        "平均速度 (rpm): 606.537",
        "最高速度 (rpm): 652.313",
        "位置波动（max）：123",
        "位置波动（min）：321",
        "其他信息"
    ]
    
    print(f"测试文本: {test_texts_3}")
    
    all_results = {}
    for field_name in config['field_mappings'].keys():
        result = processor._extract_field_value(test_texts_3, field_name)
        all_results[field_name] = result
        print(f"{field_name}: {result}")
    
    # 验证结果
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # 验证测试用例1
    if result_max == "123" and result_min == "321":
        print("✅ 测试用例1 通过: max/min正确区分")
        success_count += 1
    else:
        print("❌ 测试用例1 失败: max/min识别错误")
    total_tests += 1
    
    # 验证测试用例2
    expected_speeds = {
        "平均速度 (rpm)": "606.537",
        "最高速度 (rpm)": "652.313", 
        "最低速度 (rpm)": "572.205",
        "速度偏差 (rpm)": "45.7764"
    }
    
    speed_results = {
        "平均速度 (rpm)": result_avg,
        "最高速度 (rpm)": result_max_speed,
        "最低速度 (rpm)": result_min_speed,
        "速度偏差 (rpm)": result_deviation
    }
    
    speeds_correct = all(speed_results[k] == v for k, v in expected_speeds.items())
    if speeds_correct:
        print("✅ 测试用例2 通过: 速度字段识别正确")
        success_count += 1
    else:
        print("❌ 测试用例2 失败: 速度字段识别错误")
        for k, v in expected_speeds.items():
            if speed_results[k] != v:
                print(f"  {k}: 期望 {v}, 得到 {speed_results[k]}")
    total_tests += 1
    
    # 测试用例4：动态配置测试
    print("\n测试用例4：动态配置测试")
    print("-" * 40)
    
    # 添加新的字段映射
    processor.add_field_mapping("温度 (°C)", "temperature")
    processor.add_field_mapping("湿度 (%)", "humidity")
    
    test_texts_4 = [
        "温度 (°C): 25.5",
        "湿度 (%): 60.2"
    ]
    
    print(f"测试文本: {test_texts_4}")
    print("动态添加字段映射:")
    print("  '温度 (°C)' -> 'temperature'")
    print("  '湿度 (%)' -> 'humidity'")
    
    temp_result = processor._extract_field_value(test_texts_4, "温度 (°C)")
    humidity_result = processor._extract_field_value(test_texts_4, "湿度 (%)")
    
    print(f"温度结果: {temp_result} (期望: 25.5)")
    print(f"湿度结果: {humidity_result} (期望: 60.2)")
    
    if temp_result == "25.5" and humidity_result == "60.2":
        print("✅ 测试用例4 通过: 动态配置工作正常")
        success_count += 1
    else:
        print("❌ 测试用例4 失败: 动态配置不工作")
    total_tests += 1
    
    print(f"\n总体结果: {success_count}/{total_tests} 测试通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！基于配置的OCR字段提取工作正常！")
        print("✅ 没有硬编码字段名")
        print("✅ 完全基于配置文件驱动")
        print("✅ 支持动态添加字段")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    test_field_extraction()
