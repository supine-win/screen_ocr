#!/usr/bin/env python3
"""
统一日志配置模块
提供整个应用的日志管理
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class LoggerConfig:
    """日志配置管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            self._initialized = True
    
    def setup_logging(self):
        """设置日志配置"""
        import sys
        
        # 获取应用程序目录（支持打包环境）
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            app_dir = Path(sys.executable).parent
        else:
            # 开发环境
            app_dir = Path.cwd()
        
        # 创建日志目录
        log_dir = app_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 日志文件名（按日期）
        log_file = log_dir / f"monitor_ocr_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 文件处理器（详细日志）
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 控制台处理器（简洁日志）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # 添加处理器
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # 设置第三方库日志级别
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)
    
    @staticmethod
    def cleanup_old_logs(days: int = 30):
        """清理旧日志文件"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        current_time = datetime.now()
        for log_file in log_dir.glob("*.log*"):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if (current_time - file_time).days > days:
                try:
                    log_file.unlink()
                    print(f"Deleted old log: {log_file}")
                except Exception as e:
                    print(f"Failed to delete {log_file}: {e}")

# 全局日志配置实例
logger_config = LoggerConfig()

# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return logger_config.get_logger(name)
