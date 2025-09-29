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
            # 打包后的环境 - 多个路径检查
            search_paths = []

            # 1. _internal目录中的模型（PyInstaller打包的资源）
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
                search_paths.append(base_path / "easyocr_models")
                search_paths.append(base_path / "_internal" / "easyocr_models")

            # 2. exe同目录的模型
            exe_dir = Path(sys.executable).parent
            search_paths.append(exe_dir / "easyocr_models")
            search_paths.append(exe_dir / "_internal" / "easyocr_models")

            # 3. 当前工作目录
            current_dir = Path.cwd()
            search_paths.append(current_dir / "easyocr_models")

            for model_dir in search_paths:
                logger.info(f"Running in packaged environment, checking: {model_dir}")

                if model_dir.exists():
                    models = list(model_dir.glob("*.pth"))
                    logger.info(f"Found {len(models)} model files in packaged directory")
                    for model in models:
                        logger.info(f"  - {model.name}: {model.stat().st_size / (1024*1024):.1f} MB")

                    if models:  # 只有在找到模型文件时才返回
                        return str(model_dir)
                    else:
                        logger.warning(f"Directory exists but no .pth files found: {model_dir}")
                else:
                    logger.debug(f"Directory not found: {model_dir}")

            logger.error("No valid model directory found in packaged environment")
            return None
        
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
            
            # 设置关键的EasyOCR环境变量
            os.environ['EASYOCR_MODULE_PATH'] = parent_dir
            os.environ['EASYOCR_MODEL_PATH'] = model_dir
            
            # 仅在打包环境中设置用户目录，避免破坏开发环境
            if getattr(sys, 'frozen', False):
                if os.name == 'nt':
                    os.environ['USERPROFILE'] = parent_dir
                else:
                    os.environ['HOME'] = parent_dir
            
            # 设置torch相关路径
            os.environ['TORCH_HOME'] = parent_dir
            os.environ['XDG_CACHE_HOME'] = parent_dir
            
            # 确保EasyOCR能找到模型
            try:
                import torch
                torch.hub.set_dir(parent_dir)
            except ImportError:
                pass  # 如果torch未安装，忽略
            
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
    def get_easyocr_reader_params():
        """获取EasyOCR Reader的正确初始化参数"""
        model_path = ModelPathManager.get_easyocr_model_path()
        
        if not model_path:
            return {'verbose': False}

        # 对于打包环境，需要特殊处理
        if getattr(sys, 'frozen', False):
            # 打包环境：完全离线模式
            model_dir = Path(model_path)

            # 直接使用模型目录的父目录作为存储目录
            if model_dir.name == "easyocr_models":
                # 如果是标准的easyocr_models目录
                model_storage_dir = str(model_dir.parent)
            else:
                # 否则使用模型目录本身的父目录
                model_storage_dir = str(model_dir.parent)

            # 检查必要的模型文件
            detection_models = list(model_dir.glob("craft_*.pth"))
            recognition_models = (list(model_dir.glob("*_sim_*.pth")) + 
                                list(model_dir.glob("*_g2.pth")) + 
                                list(model_dir.glob("chinese*.pth")))

            logger.info(f"Detection models found: {len(detection_models)}")
            logger.info(f"Recognition models found: {len(recognition_models)}")

            # 设置强制离线环境变量
            os.environ['EASYOCR_DOWNLOAD_ENABLED'] = 'false'
            os.environ['EASYOCR_OFFLINE_MODE'] = 'true'
            os.environ['TORCH_HOME'] = model_storage_dir
            os.environ['CUDA_VISIBLE_DEVICES'] = ''  # 强制CPU模式

            # 返回最小化参数配置
            params = {
                'model_storage_directory': model_storage_dir,
                'verbose': False,  # 减少输出以避免触发下载逻辑
            }

            if detection_models and recognition_models:
                logger.info(f"Packaged mode: Complete offline setup with models from {model_storage_dir}")
            else:
                logger.warning("Some model files may be missing, but continuing with offline mode")

            return params

        # 开发环境：正常模式
        return {'verbose': True}
    
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
