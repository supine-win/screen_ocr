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
        """获取EasyOCR模型路径 - 统一使用easyocr_models目录"""
        # 从配置读取模型目录，默认为 easyocr_models
        if config and 'easyocr' in config and 'model_storage_directory' in config['easyocr']:
            model_dir_name = config['easyocr']['model_storage_directory']
        else:
            model_dir_name = 'easyocr_models'
        
        # 优先级顺序：
        # 1. exe同目录/当前目录下的配置目录
        # 2. 配置目录的绝对路径（如果是绝对路径）
        
        if Path(model_dir_name).is_absolute():
            # 绝对路径
            model_dir = Path(model_dir_name)
        else:
            # 相对路径，相对于exe目录或当前目录
            if getattr(sys, 'frozen', False):
                # 打包环境：相对于exe目录
                exe_dir = Path(sys.executable).parent
                model_dir = exe_dir / model_dir_name
            else:
                # 开发环境：相对于当前目录
                model_dir = Path.cwd() / model_dir_name
        
        logger.info(f"Using unified model directory: {model_dir}")
        
        if model_dir.exists():
            models = list(model_dir.glob("*.pth"))
            logger.info(f"Found {len(models)} model files")
            for model in models:
                logger.info(f"  - {model.name}: {model.stat().st_size / (1024*1024):.1f} MB")
            
            if models:
                return str(model_dir)
            else:
                logger.warning(f"Model directory exists but no .pth files found: {model_dir}")
        else:
            logger.warning(f"Model directory not found: {model_dir}")
            logger.info("Please create the directory and download model files:")
            logger.info(f"  mkdir {model_dir}")
            logger.info("  # Download craft_mlt_25k.pth and zh_sim_g2.pth to this directory")
        
        return str(model_dir)  # 即使不存在也返回路径，让EasyOCR自己处理
    
    @staticmethod
    def setup_easyocr_environment(config=None):
        """设置EasyOCR环境变量"""
        model_path = ModelPathManager.get_easyocr_model_path(config)
        
        if model_path:
            # 设置EasyOCR模型路径
            os.environ['EASYOCR_MODEL_PATH'] = model_path
            
            logger.info(f"Set EASYOCR_MODEL_PATH to: {model_path}")
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
        """获取EasyOCR Reader初始化参数"""
        model_path = ModelPathManager.get_easyocr_model_path(config)
        
        # 统一的参数配置
        params = {
            'model_storage_directory': model_path,
            'download_enabled': True,  # 允许下载缺失的模型
            'verbose': False
        }
        
        logger.info(f"EasyOCR parameters: {params}")
        return params
    
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
