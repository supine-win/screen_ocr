#!/usr/bin/env python3
"""
测试OCR字段提取功能
"""

import requests
import json

def test_screenshot_ocr():
    """测试屏幕截图OCR"""
    print("=== 测试屏幕截图OCR ===")
    
    try:
        # 发送屏幕截图OCR请求
        response = requests.post(
            'http://localhost:8080/screenshot/ocr',
            headers={'Content-Type': 'application/json'},
            json={}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功")
            print(f"截图路径: {result.get('screenshot_path')}")
            print(f"截图尺寸: {result.get('screenshot_size')}")
            print(f"识别结果: {result.get('results')}")
            
            if result.get('results'):
                print("\n🎯 成功提取到字段:")
                for key, value in result['results'].items():
                    print(f"  {key}: {value}")
            else:
                print("\n⚠️  未提取到任何字段值")
                print("请检查:")
                print("1. 屏幕上是否有配置的字段名称")
                print("2. 字段名称是否与config.json中的配置匹配")
                print("3. 字段值是否为数字格式")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保HTTP服务已启动")
        print("启动命令: python main.py --no-gui")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_config_mappings():
    """测试获取当前配置"""
    print("\n=== 当前字段映射配置 ===")
    
    try:
        response = requests.get('http://localhost:8080/config/mappings')
        if response.status_code == 200:
            mappings = response.json().get('mappings', {})
            print("当前配置的字段映射:")
            for field_name, mapped_key in mappings.items():
                print(f"  '{field_name}' -> '{mapped_key}'")
        else:
            print(f"获取配置失败: {response.status_code}")
    except Exception as e:
        print(f"获取配置失败: {e}")

if __name__ == "__main__":
    test_config_mappings()
    test_screenshot_ocr()
