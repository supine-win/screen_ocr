#!/usr/bin/env python3
"""
macOS系统OCR功能
"""

import subprocess
import tempfile
import os
import cv2
import re
from typing import Dict, List, Optional

class MacOSOCR:
    """使用macOS系统OCR功能"""
    
    def __init__(self):
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查是否可以使用macOS OCR"""
        try:
            # 检查是否是macOS系统
            result = subprocess.run(['uname'], capture_output=True, text=True)
            if result.stdout.strip() != 'Darwin':
                return False
            
            # 检查是否有OCR命令
            result = subprocess.run(['which', 'textutil'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def extract_text_from_image(self, image_path: str) -> List[str]:
        """从图像中提取文本"""
        if not self.available:
            return []
        
        try:
            # 使用macOS的OCR功能
            cmd = [
                'osascript', '-e',
                f'''
                set theImage to POSIX file "{image_path}"
                tell application "System Events"
                    set imageFile to (theImage as alias)
                end tell
                
                tell application "Preview"
                    open imageFile
                    delay 1
                    tell application "System Events"
                        keystroke "a" using command down
                        keystroke "c" using command down
                    end tell
                    close front document
                end tell
                
                return the clipboard as string
                '''
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                text = result.stdout.strip()
                return text.split('\n') if text else []
            else:
                return []
                
        except Exception as e:
            print(f"macOS OCR错误: {e}")
            return []

def test_macos_ocr():
    """测试macOS OCR功能"""
    ocr = MacOSOCR()
    
    if not ocr.available:
        print("macOS OCR不可用")
        return
    
    # 测试处理后的图像
    if os.path.exists("debug_processed.jpg"):
        print("测试处理后的图像...")
        texts = ocr.extract_text_from_image(os.path.abspath("debug_processed.jpg"))
        print(f"识别结果: {texts}")
    
    # 测试原始截图
    screenshots_dir = "./screenshots/2025/09/24/"
    if os.path.exists(screenshots_dir):
        files = [f for f in os.listdir(screenshots_dir) if f.endswith('.jpg')]
        if files:
            latest_file = max(files)
            file_path = os.path.join(screenshots_dir, latest_file)
            print(f"\n测试最新截图: {file_path}")
            texts = ocr.extract_text_from_image(os.path.abspath(file_path))
            print(f"识别结果: {texts}")

if __name__ == "__main__":
    test_macos_ocr()
