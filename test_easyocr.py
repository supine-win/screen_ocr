#!/usr/bin/env python3
"""
测试EasyOCR作为替代方案
"""

import cv2
import numpy as np

def test_easyocr():
    """测试EasyOCR识别中文"""
    try:
        import easyocr
        print("初始化EasyOCR...")
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        
        # 读取最新的截图
        import os
        screenshots_dir = "./screenshots/2025/09/24/"
        if os.path.exists(screenshots_dir):
            files = [f for f in os.listdir(screenshots_dir) if f.endswith('.jpg')]
            if files:
                latest_file = sorted(files)[-1]
                file_path = os.path.join(screenshots_dir, latest_file)
                print(f"读取图像: {file_path}")
                
                image = cv2.imread(file_path)
                print(f"图像尺寸: {image.shape}")
                
                # EasyOCR识别
                print("开始EasyOCR识别...")
                results = reader.readtext(image, detail=1)
                
                print(f"识别到 {len(results)} 个文本区域:")
                for idx, (bbox, text, prob) in enumerate(results):
                    print(f"  {idx+1}. '{text}' (置信度: {prob:.2f})")
                
                # 提取字段
                extracted_data = {}
                for bbox, text, prob in results:
                    if "平均速度" in text:
                        # 查找下一个数字
                        for _, val_text, _ in results:
                            if any(c.isdigit() for c in val_text):
                                extracted_data['avg_speed'] = val_text
                                break
                                
                print(f"\n提取的数据: {extracted_data}")
                
    except ImportError:
        print("EasyOCR未安装，正在安装...")
        import subprocess
        subprocess.run(["pip", "install", "easyocr"], check=True)
        print("请重新运行脚本")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_easyocr()
