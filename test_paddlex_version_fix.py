#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EasyOCR依赖测试
验证EasyOCR及其依赖是否正确安装
"""

import os
import sys
import site
import tempfile
from pathlib import Path

def test_torch_installation():
    """测试PyTorch是否正确安装"""
    print("\n🔍 测试PyTorch安装...")
    
    try:
        import torch
        print(f"✅ 找到PyTorch包: {torch.__version__}")
        
        # 检查CUDA可用性
        if torch.cuda.is_available():
            print(f"✅ CUDA可用: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠️  CUDA不可用，将使用CPU")
        
        return True
    except ImportError as e:
        print(f"❌ 无法导入PyTorch: {e}")
        return False
    except Exception as e:
        print(f"❌ PyTorch测试失败: {e}")
        return False

def test_opencv_installation():
    """测试OpenCV是否正确安装"""
    print("\n🔍 测试OpenCV安装...")
    
    try:
        import cv2
        print(f"✅ 找到OpenCV包: {cv2.__version__}")
        
        # 测试基本功能
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        print("✅ OpenCV基本功能测试成功")
        
        return True
    except ImportError as e:
        print(f"❌ 无法导入OpenCV: {e}")
        return False
    except Exception as e:
        print(f"❌ OpenCV测试失败: {e}")
        return False

def test_pyinstaller_easyocr_collection():
    """测试PyInstaller EasyOCR数据收集"""
    print("\n🔍 测试PyInstaller EasyOCR数据收集...")
    
    try:
        from PyInstaller.utils.hooks import collect_all
        
        # 收集EasyOCR数据
        datas, binaries, hiddenimports = collect_all('easyocr')
        
        print(f"✅ 收集到 {len(datas)} 个EasyOCR数据文件")
        print(f"✅ 收集到 {len(binaries)} 个EasyOCR二进制文件")
        print(f"✅ 收集到 {len(hiddenimports)} 个EasyOCR隐藏导入")
        
        # 收集PyTorch数据
        torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')
        print(f"✅ 收集到 {len(torch_datas)} 个PyTorch数据文件")
        print(f"✅ 收集到 {len(torch_binaries)} 个PyTorch二进制文件")
        
        return True
    except ImportError:
        print("❌ PyInstaller未安装")
        return False
    except Exception as e:
        print(f"❌ 数据收集测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("EasyOCR依赖测试")
    print("=" * 60)
    
    tests = [
        ("PyTorch安装测试", test_torch_installation),
        ("OpenCV安装测试", test_opencv_installation),
        ("PyInstaller EasyOCR数据收集测试", test_pyinstaller_easyocr_collection),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！EasyOCR环境配置正确")
        return True
    else:
        print("⚠️  部分测试失败，需要安装缺失的依赖")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
