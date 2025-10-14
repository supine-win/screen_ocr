#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强制单一模型路径管理器
彻底阻止EasyOCR使用多个路径
"""

import os
import sys
from pathlib import Path

class ForceSingleModelPath:
    """强制EasyOCR只使用一个模型路径"""
    
    @staticmethod
    def get_single_model_path():
        """获取唯一的模型路径"""
        if getattr(sys, 'frozen', False):
            # 打包环境：exe同目录的easyocr_models
            return str(Path(sys.executable).parent / "easyocr_models")
        else:
            # 开发环境：当前目录的easyocr_models
            return str(Path.cwd() / "easyocr_models")
    
    @staticmethod
    def force_single_path():
        """强制设置单一路径，阻止EasyOCR使用其他路径"""
        single_path = ForceSingleModelPath.get_single_model_path()
        
        # 1. 设置所有可能的环境变量到同一路径
        env_vars = [
            'EASYOCR_MODEL_PATH',
            'TORCH_HOME',
            'TORCH_MODEL_ZOO',
            'XDG_CACHE_HOME',
        ]
        
        for var in env_vars:
            os.environ[var] = single_path
        
        # 2. 强制设置用户目录环境变量
        if getattr(sys, 'frozen', False):
            base_dir = str(Path(single_path).parent)
            if os.name == 'nt':
                # Windows
                os.environ['USERPROFILE'] = base_dir
                os.environ['APPDATA'] = base_dir
                os.environ['LOCALAPPDATA'] = base_dir
            else:
                # Unix-like
                os.environ['HOME'] = base_dir
                os.environ['XDG_CONFIG_HOME'] = base_dir
        
        # 3. 创建模型目录（如果不存在）
        Path(single_path).mkdir(parents=True, exist_ok=True)
        
        return single_path
    
    @staticmethod
    def patch_easyocr_paths():
        """打补丁：替换EasyOCR内部的路径获取函数"""
        try:
            import easyocr.utils as easyocr_utils
            
            # 获取单一路径
            single_path = ForceSingleModelPath.get_single_model_path()
            
            # 定义强制返回单一路径的函数
            def force_model_dir():
                return single_path
            
            def force_download_path(*args, **kwargs):
                return single_path
            
            # 替换EasyOCR内部的路径函数
            if hasattr(easyocr_utils, 'get_model_path'):
                easyocr_utils.get_model_path = force_model_dir
            
            if hasattr(easyocr_utils, 'download_model'):
                original_download = easyocr_utils.download_model
                def patched_download(*args, **kwargs):
                    # 强制下载到我们的路径
                    kwargs['dst'] = single_path
                    return original_download(*args, **kwargs)
                easyocr_utils.download_model = patched_download
            
            print(f"✅ EasyOCR路径函数已被强制重定向到: {single_path}")
            return True
            
        except Exception as e:
            print(f"⚠️ EasyOCR路径补丁失败: {e}")
            return False
    
    @staticmethod
    def setup_complete_force():
        """完整的强制单一路径设置"""
        print("🔧 开始强制单一模型路径设置...")
        
        # 1. 强制环境变量
        single_path = ForceSingleModelPath.force_single_path()
        print(f"📁 强制模型路径: {single_path}")
        
        # 2. 检查模型文件
        model_dir = Path(single_path)
        if model_dir.exists():
            models = list(model_dir.glob("*.pth"))
            print(f"📦 找到模型文件: {len(models)} 个")
            
            # 检查关键模型
            required = ['craft_mlt_25k.pth', 'zh_sim_g2.pth']
            missing = []
            for req in required:
                if not any(m.name == req for m in models):
                    missing.append(req)
            
            if missing:
                print(f"⚠️ 缺少关键模型: {missing}")
                print(f"请将这些文件复制到: {single_path}")
            else:
                print("✅ 所有关键模型文件都存在")
        else:
            print(f"⚠️ 模型目录不存在: {model_dir}")
            print("请创建目录并添加必要的.pth文件")
        
        # 3. 尝试补丁EasyOCR
        ForceSingleModelPath.patch_easyocr_paths()
        
        # 4. 验证环境变量
        print("\n📋 环境变量验证:")
        for var in ['EASYOCR_MODEL_PATH', 'TORCH_HOME', 'USERPROFILE', 'HOME']:
            value = os.environ.get(var)
            if value:
                print(f"   {var}: {value}")
        
        print(f"\n✅ 强制单一路径设置完成")
        print(f"🎯 所有模型请求都将重定向到: {single_path}")
        
        return single_path

if __name__ == "__main__":
    # 测试强制单一路径
    ForceSingleModelPath.setup_complete_force()
