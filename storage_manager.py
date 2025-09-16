import os
import cv2
import numpy as np
from datetime import datetime
from typing import Optional
import shutil

class StorageManager:
    def __init__(self, base_dir: str = "./screenshots"):
        self.base_dir = base_dir
        self.ensure_base_directory()
    
    def ensure_base_directory(self):
        """确保基础目录存在"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def get_date_folder(self, date: Optional[datetime] = None) -> str:
        """获取日期文件夹路径"""
        if date is None:
            date = datetime.now()
        
        year = str(date.year)
        month = f"{date.month:02d}"
        day = f"{date.day:02d}"
        
        folder_path = os.path.join(self.base_dir, year, month, day)
        
        # 确保文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        return folder_path
    
    def save_screenshot(self, image: np.ndarray, prefix: str = "screenshot") -> str:
        """保存截图并返回文件路径"""
        timestamp = datetime.now()
        folder_path = self.get_date_folder(timestamp)
        
        # 生成文件名
        filename = f"{prefix}_{timestamp.strftime('%H%M%S_%f')[:-3]}.jpg"
        filepath = os.path.join(folder_path, filename)
        
        # 保存图片
        cv2.imwrite(filepath, image)
        
        return filepath
    
    def cleanup_old_files(self, days: int = 30):
        """清理指定天数前的文件"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.getmtime(filepath) < cutoff_date:
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass
        
        # 清理空文件夹
        self._remove_empty_folders(self.base_dir)
    
    def _remove_empty_folders(self, path: str):
        """递归删除空文件夹"""
        if not os.path.isdir(path):
            return
        
        # 递归处理子文件夹
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                self._remove_empty_folders(item_path)
        
        # 如果文件夹为空且不是根目录，则删除
        if not os.listdir(path) and path != self.base_dir:
            try:
                os.rmdir(path)
            except OSError:
                pass
    
    def get_storage_stats(self) -> dict:
        """获取存储统计信息"""
        total_files = 0
        total_size = 0
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if os.path.exists(filepath):
                    total_files += 1
                    total_size += os.path.getsize(filepath)
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'base_directory': self.base_dir
        }
