import json
import os
from typing import Dict, Any
import threading

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = {}
        self.lock = threading.Lock()
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # 创建默认配置
                self.config = self._get_default_config()
                self.save_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = self._get_default_config()
        
        return self.config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with self.lock:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 自动保存
        self.save_config()
    
    def get_camera_config(self) -> Dict[str, Any]:
        """获取摄像头配置"""
        return self.get('camera', {})
    
    def set_camera_config(self, config: Dict[str, Any]):
        """设置摄像头配置"""
        self.set('camera', config)
    
    def get_ocr_config(self) -> Dict[str, Any]:
        """获取OCR配置"""
        return self.get('ocr', {})
    
    def set_ocr_config(self, config: Dict[str, Any]):
        """设置OCR配置"""
        self.set('ocr', config)
    
    def get_field_mappings(self) -> Dict[str, str]:
        """获取字段映射"""
        return self.get('ocr.field_mappings', {})
    
    def set_field_mappings(self, mappings: Dict[str, str]):
        """设置字段映射"""
        self.set('ocr.field_mappings', mappings)
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get('storage', {})
    
    def set_storage_config(self, config: Dict[str, Any]):
        """设置存储配置"""
        self.set('storage', config)
    
    def get_http_config(self) -> Dict[str, Any]:
        """获取HTTP配置"""
        return self.get('http', {})

    def get_screenshot_region(self) -> Dict[str, int]:
        """获取截图区域配置"""
        return self.get('screenshot.region', None)

    def set_screenshot_region(self, region: Dict[str, int]):
        """设置截图区域配置"""
        self.set('screenshot.region', region)
    
    def set_http_config(self, config: Dict[str, Any]):
        """设置HTTP配置"""
        self.set('http', config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "camera": {
                "selected_index": 1,
                "resolution": [
                    1920,
                    1080
                ],
                "fps": 30
            },
            "ocr": {
                "field_mappings": {
                    "平均速度 (rpm)": ["avg_speed"],
                    "最高速度 (rpm)": ["max_speed"],
                    "最低速度 (rpm)": ["min_speed"],
                    "速度偏差 (rpm)": ["speed_deviation"],
                    "位置波动 (max)": ["position_deviation_max"],
                    "位置波动 (min)": ["position_deviation1_min", "position_deviation2_min"],
                    "速度 (rpm)": ["current_speed", "real_time_speed"]
                },
                "language": "ch",
                "use_angle_cls": True,
                "use_absolute_value": True,
                "use_gpu": False,
                "easyocr": {
                    "use_gpu": False,
                    "verbose": True,
                    "model_storage_directory": "./easyocr_models"
                }
            },
            "storage": {
                "screenshot_dir": "./screenshots",
                "auto_cleanup_days": 30
            },
            "http": {
                "host": "0.0.0.0",
                "port": 19005,
                "debug": False
            }
        }
