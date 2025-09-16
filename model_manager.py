#!/usr/bin/env python3
"""
模型管理器
处理PaddleOCR模型的加载和路径管理
"""

import os
import sys
import shutil
from pathlib import Path

class ModelManager:
    def __init__(self):
        self.paddlex_home = None
        self.setup_model_paths()
    
    def setup_model_paths(self):
        """设置模型路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件环境
            base_path = sys._MEIPASS
            bundled_models = os.path.join(base_path, 'paddlex_models')
            
            if os.path.exists(bundled_models):
                # 使用打包的模型文件
                self.paddlex_home = bundled_models
                os.environ['PADDLEX_HOME'] = bundled_models
                print(f"使用打包的模型文件: {bundled_models}")
            else:
                # 回退到默认路径
                self.paddlex_home = os.path.expanduser("~/.paddlex")
                print("未找到打包的模型文件，使用默认路径")
        else:
            # 开发环境
            self.paddlex_home = os.path.expanduser("~/.paddlex")
    
    def ensure_models_exist(self):
        """确保模型文件存在"""
        if not os.path.exists(self.paddlex_home):
            print("模型文件不存在，需要下载...")
            return False
        
        # 检查关键模型文件
        required_models = [
            "official_models/PP-OCRv5_server_det",
            "official_models/PP-OCRv5_server_rec"
        ]
        
        for model_path in required_models:
            full_path = os.path.join(self.paddlex_home, model_path)
            if not os.path.exists(full_path):
                print(f"缺少模型文件: {model_path}")
                return False
        
        return True
    
    def copy_models_for_packaging(self, target_dir="paddlex_models"):
        """为打包复制模型文件"""
        source_dir = os.path.expanduser("~/.paddlex")
        
        if not os.path.exists(source_dir):
            print("源模型目录不存在，请先运行 prepare_models.py")
            return False
        
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        print(f"复制模型文件从 {source_dir} 到 {target_dir}")
        shutil.copytree(source_dir, target_dir)
        
        # 计算总大小
        total_size = 0
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                total_size += os.path.getsize(os.path.join(root, file))
        
        print(f"模型文件复制完成，总大小: {total_size / 1024 / 1024:.1f} MB")
        return True
    
    def get_model_info(self):
        """获取模型信息"""
        if not os.path.exists(self.paddlex_home):
            return {"status": "not_found", "path": self.paddlex_home}
        
        model_count = 0
        total_size = 0
        
        for root, dirs, files in os.walk(self.paddlex_home):
            for file in files:
                if file.endswith(('.pdiparams', '.pdmodel', '.yml', '.json')):
                    model_count += 1
                    total_size += os.path.getsize(os.path.join(root, file))
        
        return {
            "status": "found",
            "path": self.paddlex_home,
            "model_count": model_count,
            "total_size_mb": round(total_size / 1024 / 1024, 1)
        }
