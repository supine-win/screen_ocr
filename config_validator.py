#!/usr/bin/env python3
"""
配置验证模块
确保配置文件的完整性和正确性
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from logger_config import get_logger

logger = get_logger(__name__)

class ConfigValidator:
    """配置验证器"""
    
    # 配置模板和默认值
    CONFIG_SCHEMA = {
        'camera': {
            'resolution': {'type': list, 'default': [1920, 1080], 'length': 2},
            'fps': {'type': int, 'default': 30, 'min': 1, 'max': 120}
        },
        'ocr': {
            'field_mappings': {
                'type': dict, 
                'default': {
                    '平均速度 (rpm)': 'avg_speed',
                    '最高速度 (rpm)': 'max_speed',
                    '最低速度 (rpm)': 'min_speed',
                    '速度偏差 (rpm)': 'speed_deviation',
                    '位置波动 (max)': 'position_deviation_max',
                    '位置波动 (min)': 'position_deviation_min'
                }
            },
            'language': {'type': str, 'default': 'ch', 'options': ['ch', 'en', 'ch_sim']},
            'use_angle_cls': {'type': bool, 'default': False},
            'use_absolute_value': {'type': bool, 'default': True}  # 是否取绝对值
        },
        'storage': {
            'screenshot_dir': {'type': str, 'default': './screenshots'},
            'auto_cleanup_days': {'type': int, 'default': 30, 'min': 1, 'max': 365},
            'max_storage_mb': {'type': int, 'default': 1000, 'min': 100}
        },
        'http': {
            'host': {'type': str, 'default': '0.0.0.0'},
            'port': {'type': int, 'default': 9501, 'min': 1024, 'max': 65535},
            'debug': {'type': bool, 'default': False},
            'enabled': {'type': bool, 'default': True},
            'cors_enabled': {'type': bool, 'default': True}
        },
        'performance': {
            'max_image_size': {'type': int, 'default': 1920, 'min': 480},
            'ocr_timeout': {'type': int, 'default': 30, 'min': 5},
            'enable_cache': {'type': bool, 'default': True},
            'cache_ttl': {'type': int, 'default': 300, 'min': 60}
        }
    }
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证配置"""
        errors = []
        
        for section, schema in cls.CONFIG_SCHEMA.items():
            if section not in config:
                logger.warning(f"Missing config section: {section}, using defaults")
                config[section] = {}
            
            for key, rules in schema.items():
                value = config[section].get(key)
                
                # 检查是否缺少必需字段
                if value is None:
                    if 'default' in rules:
                        config[section][key] = rules['default']
                        logger.info(f"Using default value for {section}.{key}: {rules['default']}")
                    else:
                        errors.append(f"Missing required field: {section}.{key}")
                    continue
                
                # 类型检查
                if 'type' in rules:
                    expected_type = rules['type']
                    if expected_type == int:
                        if not isinstance(value, int):
                            errors.append(f"{section}.{key} must be integer, got {type(value).__name__}")
                            continue
                        
                        # 范围检查
                        if 'min' in rules and value < rules['min']:
                            errors.append(f"{section}.{key} must be >= {rules['min']}, got {value}")
                        if 'max' in rules and value > rules['max']:
                            errors.append(f"{section}.{key} must be <= {rules['max']}, got {value}")
                    
                    elif expected_type == str:
                        if not isinstance(value, str):
                            errors.append(f"{section}.{key} must be string, got {type(value).__name__}")
                            continue
                        
                        # 选项检查
                        if 'options' in rules and value not in rules['options']:
                            errors.append(f"{section}.{key} must be one of {rules['options']}, got {value}")
                    
                    elif expected_type == bool:
                        if not isinstance(value, bool):
                            errors.append(f"{section}.{key} must be boolean, got {type(value).__name__}")
                    
                    elif expected_type == list:
                        if not isinstance(value, list):
                            errors.append(f"{section}.{key} must be list, got {type(value).__name__}")
                            continue
                        
                        # 长度检查
                        if 'length' in rules and len(value) != rules['length']:
                            errors.append(f"{section}.{key} must have {rules['length']} elements, got {len(value)}")
                    
                    elif expected_type == dict:
                        if not isinstance(value, dict):
                            errors.append(f"{section}.{key} must be dict, got {type(value).__name__}")
        
        return len(errors) == 0, errors
    
    @classmethod
    def load_and_validate(cls, config_path: str = 'config.json') -> Dict[str, Any]:
        """加载并验证配置文件"""
        config_file = Path(config_path)
        
        # 如果配置文件不存在，创建默认配置
        if not config_file.exists():
            logger.info(f"Config file not found, creating default: {config_path}")
            config = cls.create_default_config()
            cls.save_config(config, config_path)
            return config
        
        try:
            # 加载配置
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 验证配置
            is_valid, errors = cls.validate_config(config)
            
            if not is_valid:
                logger.error(f"Configuration validation failed: {errors}")
                # 使用默认值修复错误
                config = cls.fix_config(config)
                cls.save_config(config, config_path)
                logger.info("Configuration fixed and saved")
            else:
                logger.info("Configuration validation successful")
            
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.info("Creating default configuration")
            config = cls.create_default_config()
            cls.save_config(config, config_path)
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return cls.create_default_config()
    
    @classmethod
    def create_default_config(cls) -> Dict[str, Any]:
        """创建默认配置"""
        config = {}
        
        for section, schema in cls.CONFIG_SCHEMA.items():
            config[section] = {}
            for key, rules in schema.items():
                if 'default' in rules:
                    config[section][key] = rules['default']
        
        return config
    
    @classmethod
    def fix_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """修复配置错误"""
        for section, schema in cls.CONFIG_SCHEMA.items():
            if section not in config:
                config[section] = {}
            
            for key, rules in schema.items():
                value = config[section].get(key)
                
                # 使用默认值修复缺失或错误的字段
                if value is None or not cls._validate_value(value, rules):
                    if 'default' in rules:
                        config[section][key] = rules['default']
                        logger.info(f"Fixed {section}.{key} with default: {rules['default']}")
        
        return config
    
    @classmethod
    def _validate_value(cls, value: Any, rules: Dict[str, Any]) -> bool:
        """验证单个值"""
        if 'type' in rules:
            expected_type = rules['type']
            if not isinstance(value, expected_type):
                return False
            
            if expected_type == int:
                if 'min' in rules and value < rules['min']:
                    return False
                if 'max' in rules and value > rules['max']:
                    return False
            
            elif expected_type == str:
                if 'options' in rules and value not in rules['options']:
                    return False
            
            elif expected_type == list:
                if 'length' in rules and len(value) != rules['length']:
                    return False
        
        return True
    
    @classmethod
    def save_config(cls, config: Dict[str, Any], config_path: str = 'config.json'):
        """保存配置文件"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
