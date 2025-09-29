#!/usr/bin/env python3
"""
实时调试用户实际问题
"""

from ocr_processor import OCRProcessor
import json

def debug_actual_issue():
    """调试用户实际遇到的问题"""
    print("=" * 60)
    print("实时调试 - 找出真正的问题")
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
    
    print("请输入你实际遇到的OCR识别结果:")
    print("(可以直接粘贴OCR输出的文本列表，或者逐行输入，输入空行结束)")
    print("例如：['位置波动（max）：123', '位置波动（mix）：321']")
    print()
    
    # 获取用户输入
    user_input = input("OCR文本 (JSON格式或逐行): ").strip()
    
    if user_input.startswith('['):
        # JSON格式输入
        try:
            texts = json.loads(user_input.replace("'", '"'))
        except:
            print("JSON格式错误，改用逐行输入模式")
            texts = get_line_by_line_input()
    else:
        # 逐行输入模式
        texts = [user_input] if user_input else []
        texts.extend(get_line_by_line_input())
    
    if not texts:
        print("❌ 没有输入任何文本")
        return
    
    print(f"\n收到的OCR文本 ({len(texts)} 个片段):")
    for i, text in enumerate(texts):
        print(f"  {i+1:2d}. '{text}'")
    
    print("\n" + "=" * 60)
    print("开始详细分析")
    print("=" * 60)
    
    # 重点测试位置波动字段
    target_fields = ['位置波动 (max)', '位置波动 (min)']
    
    for field_name in target_fields:
        print(f"\n🔍 详细分析字段: {field_name}")
        print("-" * 40)
        
        # 手动跟踪每个步骤
        result = debug_field_extraction(processor, texts, field_name)
        
        if result:
            print(f"✅ 最终结果: {field_name} = {result}")
        else:
            print(f"❌ 最终结果: {field_name} = None (未找到)")
            
            # 提供诊断建议
            print("\n🛠️ 诊断建议:")
            analyze_failure_reasons(texts, field_name)
    
    print("\n" + "=" * 60)
    print("问题诊断完成")
    print("=" * 60)

def get_line_by_line_input():
    """逐行获取输入"""
    texts = []
    print("逐行输入OCR文本 (输入空行结束):")
    while True:
        line = input(f"文本{len(texts)+1}: ").strip()
        if not line:
            break
        texts.append(line)
    return texts

def debug_field_extraction(processor, texts, field_name):
    """调试字段提取过程"""
    print(f"步骤1: 检查单个片段匹配")
    for i, text in enumerate(texts):
        result = processor._extract_value_from_text(text, field_name)
        if result:
            print(f"  ✅ 片段 {i+1} '{text}' -> {result}")
            return result
        else:
            print(f"  ❌ 片段 {i+1} '{text}' -> 无匹配")
    
    print(f"\n步骤2: 检查跨片段匹配")
    result = processor._extract_cross_fragment(texts, field_name)
    if result:
        print(f"  ✅ 跨片段匹配成功 -> {result}")
        return result
    else:
        print(f"  ❌ 跨片段匹配失败")
    
    print(f"\n步骤3: 检查全文模式匹配")
    result = processor._extract_with_patterns(texts, field_name)
    if result:
        print(f"  ✅ 全文模式匹配成功 -> {result}")
        return result
    else:
        print(f"  ❌ 全文模式匹配失败")
    
    print(f"\n步骤4: 检查后备方案")
    result = processor._fallback_extraction(texts, field_name)
    if result:
        print(f"  ✅ 后备方案成功 -> {result}")
        return result
    else:
        print(f"  ❌ 后备方案失败")
    
    return None

def analyze_failure_reasons(texts, field_name):
    """分析失败原因"""
    base_field = "位置波动"
    is_min = "(min)" in field_name
    is_max = "(max)" in field_name
    
    # 检查是否有基础字段
    base_found = any(base_field in text for text in texts)
    print(f"1. 基础字段'{base_field}'存在: {'✅' if base_found else '❌'}")
    
    if is_min:
        # 检查min相关的文本
        min_patterns = ['min', 'mix', 'nin', 'mir']
        min_found = any(any(pattern in text.lower() for pattern in min_patterns) for text in texts)
        print(f"2. min相关文本存在: {'✅' if min_found else '❌'}")
        
        if not min_found:
            print("   💡 建议: OCR可能将min识别为其他文字，检查类似的文本")
            
    elif is_max:
        # 检查max相关的文本
        max_patterns = ['max', 'nax', 'mux', 'mac']
        max_found = any(any(pattern in text.lower() for pattern in max_patterns) for text in texts)
        print(f"2. max相关文本存在: {'✅' if max_found else '❌'}")
    
    # 检查数字
    import re
    numbers = []
    for text in texts:
        nums = re.findall(r'\d+\.?\d*', text)
        numbers.extend(nums)
    
    print(f"3. 找到的数字: {numbers}")
    
    if not numbers:
        print("   💡 建议: OCR可能没有正确识别数字")
    
    # 提供改进建议
    print("\n🔧 可能的解决方案:")
    print("1. 检查OCR识别质量，可能需要调整图像预处理")
    print("2. 在config.json中添加更多字段变体")
    print("3. 使用更宽松的匹配模式")

if __name__ == "__main__":
    debug_actual_issue()
