#!/usr/bin/env python3
"""
简单日志管理器 - 用于原版
支持打包环境的日志输出
"""

import os
import sys
from pathlib import Path
from datetime import datetime

class SimpleLogger:
    """简单的日志管理器"""
    
    def __init__(self):
        self.log_file = None
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        try:
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
            log_filename = f"monitor_ocr_{datetime.now().strftime('%Y%m%d')}.log"
            self.log_file = log_dir / log_filename
            
            # 记录启动信息
            self.log("INFO", "日志系统初始化成功")
            self.log("INFO", f"日志文件: {self.log_file}")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
    
    def log(self, level, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level}] {message}"
        
        # 输出到控制台
        print(log_line)
        
        # 写入文件
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line + '\n')
            except Exception as e:
                print(f"写入日志文件失败: {e}")
    
    def info(self, message):
        """信息日志"""
        self.log("INFO", message)
    
    def error(self, message):
        """错误日志"""
        self.log("ERROR", message)
    
    def warning(self, message):
        """警告日志"""
        self.log("WARNING", message)
    
    def debug(self, message):
        """调试日志"""
        self.log("DEBUG", message)

# 全局日志实例
_logger = None

def get_logger():
    """获取日志实例"""
    global _logger
    if _logger is None:
        _logger = SimpleLogger()
    return _logger

def log_info(message):
    """快捷信息日志"""
    get_logger().info(message)

def log_error(message):
    """快捷错误日志"""
    get_logger().error(message)

def log_warning(message):
    """快捷警告日志"""
    get_logger().warning(message)
