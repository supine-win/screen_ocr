#!/usr/bin/env python3
"""
模型路径管理器
处理打包环境和开发环境中的模型路径问题
"""

import os
import sys
from pathlib import Path
from logger_config import get_logger

logger = get_logger(__name__)

class ModelPathManager:
    """模型路径管理器"""
    
    @staticmethod 
    def get_easyocr_model_path(config=None):
        """获取EasyOCR模型路径 - 统一简化版本"""
        # 统一使用 easyocr_models 目录名
        model_dir_name = 'easyocr_models'
        
        # 确定基础目录
        if getattr(sys, 'frozen', False):
            # 打包环境：使用exe同目录
            base_dir = Path(sys.executable).parent
        else:
            # 开发环境：使用当前工作目录
            base_dir = Path.cwd()
        
        model_dir = base_dir / model_dir_name
        
        # 只在第一次检查时输出详细信息
        if not hasattr(ModelPathManager, '_path_checked'):
            logger.info(f"Model directory: {model_dir}")
            
            if model_dir.exists():
                models = list(model_dir.glob("*.pth"))
                if models:
                    logger.info(f"Found {len(models)} model files")
                    for model in models:
                        logger.info(f"  - {model.name}: {model.stat().st_size / (1024*1024):.1f} MB")
                else:
                    logger.warning(f"Model directory exists but no .pth files found")
            else:
                logger.warning(f"Model directory not found: {model_dir}")
                logger.info("Create directory and download models:")
                logger.info(f"  mkdir {model_dir}")
                logger.info("  # Download required .pth files")
            
            ModelPathManager._path_checked = True
        
        return str(model_dir)
    
    @staticmethod
    def setup_easyocr_environment(config=None):
        """设置EasyOCR环境变量 - 简化版本"""
        model_path = ModelPathManager.get_easyocr_model_path(config)
        
        # 设置EasyOCR模型路径环境变量
        os.environ['EASYOCR_MODEL_PATH'] = model_path
        
        # 只在第一次设置时输出日志
        if not hasattr(ModelPathManager, '_env_set'):
            logger.info(f"EasyOCR model path: {model_path}")
            ModelPathManager._env_set = True
        
        return True
    
    @staticmethod
    def get_config_path():
        """获取配置文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包环境
            base_path = Path(sys._MEIPASS)
            config_path = base_path / "config.json"
            
            if config_path.exists():
                return str(config_path)
            
            # 备选：exe同目录
            exe_dir = Path(sys.executable).parent
            alt_config = exe_dir / "config.json"
            if alt_config.exists():
                return str(alt_config)
        
        # 开发环境
        return "config.json"
    
    @staticmethod
    def setup_easyocr_model_structure():
        """为EasyOCR创建正确的模型目录结构"""
        model_path = ModelPathManager.get_easyocr_model_path()
        
        if not model_path or not getattr(sys, 'frozen', False):
            return False
        
        try:
            model_dir = Path(model_path)
            parent_dir = model_dir.parent
            
            # 创建EasyOCR期望的目录结构
            easyocr_home = parent_dir / ".EasyOCR"
            easyocr_model_dir = easyocr_home / "model"
            
            # 确保目录存在
            easyocr_model_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制或链接模型文件到EasyOCR期望的位置
            for model_file in model_dir.glob("*.pth"):
                target_file = easyocr_model_dir / model_file.name
                if not target_file.exists():
                    try:
                        # 尝试创建硬链接（更快）
                        target_file.hardlink_to(model_file)
                        logger.info(f"创建硬链接: {model_file.name}")
                    except:
                        # 回退到复制
                        import shutil
                        shutil.copy2(model_file, target_file)
                        logger.info(f"复制模型文件: {model_file.name}")
            
            # 设置HOME环境变量指向我们的目录
            if os.name == 'nt':
                os.environ['USERPROFILE'] = str(parent_dir)
            else:
                os.environ['HOME'] = str(parent_dir)
            
            logger.info(f"EasyOCR模型结构设置完成: {easyocr_home}")
            return True
            
        except Exception as e:
            logger.error(f"设置EasyOCR模型结构失败: {e}")
            return False
    
    @staticmethod
    def get_easyocr_reader_params(config=None):
        """获取EasyOCR Reader初始化参数 - 简化版本"""
        model_path = ModelPathManager.get_easyocr_model_path(config)
        
        # 统一的参数配置
        params = {
            'model_storage_directory': model_path,
            'download_enabled': True,
            'verbose': False
        }
        
        # 只在第一次调用时输出参数日志
        if not hasattr(ModelPathManager, '_params_logged'):
            logger.info(f"EasyOCR parameters: {params}")
            ModelPathManager._params_logged = True
        
        return params
    
    @staticmethod
    def create_debug_info():
        """创建调试信息文件 - 简化版本"""
        # 只在开发环境或首次运行时创建调试信息
        if not getattr(sys, 'frozen', False) or not hasattr(ModelPathManager, '_debug_created'):
            debug_info = {
                "environment": "packaged" if getattr(sys, 'frozen', False) else "development",
                "model_path": ModelPathManager.get_easyocr_model_path(),
                "config_path": ModelPathManager.get_config_path(),
            }
            
            # 保存调试信息
            try:
                import json
                debug_file = Path("debug_info.json")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    json.dump(debug_info, f, indent=2, ensure_ascii=False)
                
                # 只在首次创建时输出日志
                if not hasattr(ModelPathManager, '_debug_created'):
                    logger.info(f"Debug info saved to: {debug_file}")
                    ModelPathManager._debug_created = True
                    
            except Exception as e:
                logger.error(f"Failed to save debug info: {e}")
            
            return debug_info
        
        return {}
