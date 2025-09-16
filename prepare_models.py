#!/usr/bin/env python3
"""
预下载PaddleOCR模型脚本
确保模型文件在打包前已下载完成
"""

import os
import sys
from paddleocr import PaddleOCR

def download_models():
    """下载所需的PaddleOCR模型"""
    print("开始下载PaddleOCR模型...")
    
    try:
        # 初始化PaddleOCR，这会自动下载所需模型
        ocr = PaddleOCR(
            use_textline_orientation=True,
            lang='ch'
        )
        print("✅ 中文OCR模型下载完成")
        
        # 检查模型文件是否存在
        paddlex_home = os.path.expanduser("~/.paddlex")
        if os.path.exists(paddlex_home):
            model_count = 0
            for root, dirs, files in os.walk(paddlex_home):
                for file in files:
                    if file.endswith(('.pdiparams', '.pdmodel')):
                        model_count += 1
            print(f"✅ 找到 {model_count} 个模型文件")
            print(f"模型存储路径: {paddlex_home}")
        else:
            print("❌ 未找到模型文件目录")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模型下载失败: {e}")
        return False

def list_model_files():
    """列出所有模型文件"""
    paddlex_home = os.path.expanduser("~/.paddlex")
    if not os.path.exists(paddlex_home):
        print("模型目录不存在")
        return
    
    print("\n模型文件列表:")
    print("=" * 50)
    
    total_size = 0
    for root, dirs, files in os.walk(paddlex_home):
        for file in files:
            filepath = os.path.join(root, file)
            size = os.path.getsize(filepath)
            total_size += size
            rel_path = os.path.relpath(filepath, paddlex_home)
            print(f"{rel_path} ({size / 1024 / 1024:.1f} MB)")
    
    print("=" * 50)
    print(f"总大小: {total_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    if download_models():
        list_model_files()
        print("\n✅ 模型准备完成，可以进行打包")
    else:
        print("\n❌ 模型准备失败")
        sys.exit(1)
