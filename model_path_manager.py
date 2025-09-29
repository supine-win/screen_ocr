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
    def get_easyocr_model_path():
        """获取EasyOCR模型路径"""
        # 检查打包环境
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            base_path = Path(sys._MEIPASS)
            packaged_model_dir = base_path / "easyocr_models"
            
            logger.info(f"Running in packaged environment, checking: {packaged_model_dir}")
            
            if packaged_model_dir.exists():
                models = list(packaged_model_dir.glob("*.pth"))
                logger.info(f"Found {len(models)} model files in packaged directory")
                for model in models:
                    logger.info(f"  - {model.name}: {model.stat().st_size / (1024*1024):.1f} MB")
                return str(packaged_model_dir)
            else:
                logger.error(f"Packaged model directory not found: {packaged_model_dir}")
                # 尝试相对路径
                exe_dir = Path(sys.executable).parent
                alt_model_dir = exe_dir / "easyocr_models"
                if alt_model_dir.exists():
                    logger.info(f"Found models in alternative path: {alt_model_dir}")
                    return str(alt_model_dir)
        
        # 开发环境 - 使用默认EasyOCR路径
        home_dir = Path.home()
        default_model_dir = home_dir / ".EasyOCR" / "model"
        
        logger.info(f"Running in development environment, using: {default_model_dir}")
        
        if default_model_dir.exists():
            models = list(default_model_dir.glob("*.pth"))
            logger.info(f"Found {len(models)} model files in default directory")
            return str(default_model_dir)
        else:
            logger.error(f"Default model directory not found: {default_model_dir}")
            return None
    
    @staticmethod
    def setup_easyocr_environment():
        """设置EasyOCR环境变量"""
        model_path = ModelPathManager.get_easyocr_model_path()
        
        if model_path:
            # 设置EasyOCR相关环境变量
            model_dir = str(Path(model_path))
            parent_dir = str(Path(model_path).parent)
            
            # 多种可能的环境变量
            os.environ['EASYOCR_MODULE_PATH'] = parent_dir
            os.environ['EASYOCR_MODEL_PATH'] = model_dir
            os.environ['TORCH_HOME'] = parent_dir
            
            # 确保EasyOCR能找到模型
            import torch
            torch.hub.set_dir(parent_dir)
            
            logger.info(f"Set EASYOCR_MODULE_PATH to: {parent_dir}")
            logger.info(f"Set EASYOCR_MODEL_PATH to: {model_dir}")
            logger.info(f"Set TORCH_HOME to: {parent_dir}")
            
            return True
        
        logger.error("Failed to setup EasyOCR environment - no model path found")
        return False
    
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
    def create_debug_info():
        """创建调试信息文件"""
        debug_info = {
            "environment": "packaged" if getattr(sys, 'frozen', False) else "development",
            "executable_path": sys.executable,
            "current_directory": os.getcwd(),
            "python_path": sys.path,
        }
        
        if getattr(sys, 'frozen', False):
            debug_info["meipass"] = getattr(sys, '_MEIPASS', 'Not available')
            debug_info["packaged_files"] = []
            
            # 列出打包的文件
            meipass = getattr(sys, '_MEIPASS', '')
            if meipass and Path(meipass).exists():
                try:
                    for item in Path(meipass).rglob("*"):
                        if item.is_file() and any(item.name.endswith(ext) for ext in ['.pth', '.json', '.dll']):
                            debug_info["packaged_files"].append(str(item))
                except Exception as e:
                    debug_info["file_list_error"] = str(e)
        
        # 检查EasyOCR相关
        debug_info["easyocr_model_path"] = ModelPathManager.get_easyocr_model_path()
        debug_info["config_path"] = ModelPathManager.get_config_path()
        
        # 保存调试信息
        try:
            import json
            debug_file = Path("debug_info.json")
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_info, f, indent=2, ensure_ascii=False)
            logger.info(f"Debug info saved to: {debug_file}")
        except Exception as e:
            logger.error(f"Failed to save debug info: {e}")
        
        return debug_info
