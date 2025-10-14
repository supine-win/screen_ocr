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

# 导入强制单一路径管理器
try:
    from force_single_model_path import ForceSingleModelPath
    _FORCE_AVAILABLE = True
except ImportError:
    _FORCE_AVAILABLE = False

class ModelPathManager:
    """模型路径管理器 - 极简版本"""
    
    @staticmethod 
    def get_easyocr_model_path(config=None):
        """获取EasyOCR模型路径 - 强制单一路径版本"""
        # 优先使用强制单一路径管理器
        if _FORCE_AVAILABLE and getattr(sys, 'frozen', False):
            # 打包环境：使用强制单一路径
            model_dir = ForceSingleModelPath.get_single_model_path()
        else:
            # 开发环境或无强制管理器：使用标准逻辑
            model_dir_name = 'easyocr_models'
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path.cwd()
            model_dir = str(base_dir / model_dir_name)
        
        # 极简日志：只输出一次关键信息
        if not hasattr(ModelPathManager, '_path_logged'):
            logger.info(f"EasyOCR模型目录: {model_dir}")
            if Path(model_dir).exists():
                models = list(Path(model_dir).glob("*.pth"))
                if models:
                    logger.info(f"找到 {len(models)} 个模型文件")
                else:
                    logger.warning("模型目录为空，请添加必要的.pth文件")
            else:
                logger.warning(f"模型目录不存在，请创建: {model_dir}")
            ModelPathManager._path_logged = True
        
        return model_dir
    
    @staticmethod
    def setup_easyocr_environment(config=None):
        """设置EasyOCR环境变量 - 强制单一路径版本"""
        # 在打包环境中使用强制单一路径管理器
        if _FORCE_AVAILABLE and getattr(sys, 'frozen', False):
            # 使用强制单一路径的完整设置
            model_path = ForceSingleModelPath.setup_complete_force()
            # 额外的补丁：尝试重定向EasyOCR内部路径
            ForceSingleModelPath.patch_easyocr_paths()
        else:
            # 开发环境或标准设置
            model_path = ModelPathManager.get_easyocr_model_path(config)
            os.environ['EASYOCR_MODEL_PATH'] = model_path
            os.environ['TORCH_HOME'] = model_path
        
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
    def get_easyocr_reader_params(config=None):
        """获取EasyOCR Reader初始化参数 - 极简版本"""
        model_path = ModelPathManager.get_easyocr_model_path(config)
        
        # 极简参数：只指定必要的路径和禁用下载
        return {
            'model_storage_directory': model_path,
            'download_enabled': False,  # 禁用下载，强制使用本地模型
            'verbose': False
        }
    
