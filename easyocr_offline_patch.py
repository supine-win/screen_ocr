#!/usr/bin/env python3
"""
EasyOCR离线补丁
强制EasyOCR使用本地模型，完全禁用网络下载
"""

import os
import sys
from pathlib import Path

def patch_easyocr_for_offline():
    """为EasyOCR应用离线补丁"""
    
    # 如果不是打包环境，不应用补丁
    if not getattr(sys, 'frozen', False):
        return
    
    print("Applying EasyOCR offline patch for packaged environment...")
    
    try:
        # 1. 屏蔽网络下载相关的模块
        import urllib.request
        import urllib.error
        
        # 保存原始函数
        original_urlopen = urllib.request.urlopen
        original_urlretrieve = urllib.request.urlretrieve
        
        def blocked_urlopen(*args, **kwargs):
            raise urllib.error.URLError("Network access blocked in packaged mode")
        
        def blocked_urlretrieve(*args, **kwargs):
            raise urllib.error.URLError("Network download blocked in packaged mode")
        
        # 替换网络函数
        urllib.request.urlopen = blocked_urlopen
        urllib.request.urlretrieve = blocked_urlretrieve
        
        print("✅ Network functions blocked")
        
        # 2. 设置环境变量
        meipass = getattr(sys, '_MEIPASS', '')
        if meipass:
            model_dir = os.path.join(meipass, 'easyocr_models')
            if os.path.exists(model_dir):
                # 设置EasyOCR相关环境变量
                os.environ['EASYOCR_MODULE_PATH'] = meipass
                os.environ['EASYOCR_MODEL_PATH'] = model_dir
                
                # 创建.EasyOCR目录结构
                easyocr_home = os.path.join(meipass, '.EasyOCR')
                easyocr_model_dir = os.path.join(easyocr_home, 'model')
                
                os.makedirs(easyocr_model_dir, exist_ok=True)
                
                # 链接模型文件
                for model_file in os.listdir(model_dir):
                    if model_file.endswith('.pth'):
                        src = os.path.join(model_dir, model_file)
                        dst = os.path.join(easyocr_model_dir, model_file)
                        if not os.path.exists(dst):
                            try:
                                os.link(src, dst)
                            except:
                                import shutil
                                shutil.copy2(src, dst)
                
                # 设置HOME环境变量
                if os.name == 'nt':
                    os.environ['USERPROFILE'] = meipass
                else:
                    os.environ['HOME'] = meipass
                
                print(f"✅ EasyOCR environment set to: {meipass}")
                print(f"✅ Models directory: {model_dir}")
                
                return True
        
        print("⚠️  MEIPASS not found or models directory missing")
        return False
        
    except Exception as e:
        print(f"❌ Failed to apply offline patch: {e}")
        return False

def restore_network_access():
    """恢复网络访问（如果需要）"""
    # 在大多数情况下，打包应用不需要恢复网络访问
    # 但如果有其他组件需要网络，可以在这里恢复
    pass

# 自动应用补丁
if getattr(sys, 'frozen', False):
    patch_easyocr_for_offline()
