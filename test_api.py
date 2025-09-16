#!/usr/bin/env python3
"""
API测试脚本
用于测试HTTP服务的各个接口
"""

import requests
import json
import time

def test_api(base_url="http://localhost:8080"):
    """测试API接口"""
    
    print(f"测试API服务: {base_url}")
    print("=" * 50)
    
    # 1. 健康检查
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ 健康检查: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    
    print("\n" + "-" * 30 + "\n")
    
    # 2. 摄像头状态
    try:
        response = requests.get(f"{base_url}/camera/status")
        print(f"✅ 摄像头状态: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 摄像头状态查询失败: {e}")
    
    print("\n" + "-" * 30 + "\n")
    
    # 3. 存储统计
    try:
        response = requests.get(f"{base_url}/storage/stats")
        print(f"✅ 存储统计: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 存储统计查询失败: {e}")
    
    print("\n" + "-" * 30 + "\n")
    
    # 4. 获取字段映射
    try:
        response = requests.get(f"{base_url}/config/mappings")
        print(f"✅ 字段映射: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 字段映射查询失败: {e}")
    
    print("\n" + "-" * 30 + "\n")
    
    # 5. OCR识别（需要摄像头运行）
    try:
        response = requests.post(f"{base_url}/ocr")
        print(f"✅ OCR识别: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ OCR识别失败: {e}")

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    test_api(base_url)
