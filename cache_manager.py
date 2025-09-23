#!/usr/bin/env python3
"""
缓存管理模块
提供OCR结果缓存，减少重复处理
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
import pickle
from logger_config import get_logger

logger = get_logger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = ".cache", ttl: int = 300, max_size_mb: int = 100):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            ttl: 缓存生存时间（秒）
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl
        self.max_size_mb = max_size_mb
        self.memory_cache = {}  # 内存缓存
        self.hits = 0
        self.misses = 0
        
        # 启动时清理过期缓存
        self.cleanup_expired()
    
    def _generate_key(self, data: Any) -> str:
        """生成缓存键"""
        if isinstance(data, bytes):
            return hashlib.md5(data).hexdigest()
        elif isinstance(data, str):
            return hashlib.md5(data.encode()).hexdigest()
        else:
            # 对于复杂对象，序列化后生成键
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 先检查内存缓存
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                self.hits += 1
                logger.debug(f"Cache hit (memory): {key}")
                return entry['data']
            else:
                # 过期，删除
                del self.memory_cache[key]
        
        # 检查磁盘缓存
        cache_file = self.cache_dir / f"{key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                if time.time() - entry['timestamp'] < self.ttl:
                    # 加载到内存缓存
                    self.memory_cache[key] = entry
                    self.hits += 1
                    logger.debug(f"Cache hit (disk): {key}")
                    return entry['data']
                else:
                    # 过期，删除
                    cache_file.unlink()
            except Exception as e:
                logger.error(f"Failed to load cache {key}: {e}")
                cache_file.unlink()
        
        self.misses += 1
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, data: Any):
        """设置缓存"""
        entry = {
            'timestamp': time.time(),
            'data': data
        }
        
        # 保存到内存缓存
        self.memory_cache[key] = entry
        
        # 检查内存缓存大小，必要时清理
        if len(self.memory_cache) > 100:  # 最多保留100个内存缓存
            self._cleanup_memory_cache()
        
        # 保存到磁盘缓存
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
            logger.debug(f"Cache set: {key}")
        except Exception as e:
            logger.error(f"Failed to save cache {key}: {e}")
        
        # 检查磁盘缓存大小
        self._check_disk_size()
    
    def _cleanup_memory_cache(self):
        """清理内存缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if current_time - entry['timestamp'] >= self.ttl
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # 如果还是太多，删除最旧的
        if len(self.memory_cache) > 50:
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            # 保留最新的50个
            self.memory_cache = dict(sorted_items[-50:])
    
    def _check_disk_size(self):
        """检查磁盘缓存大小"""
        total_size = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.cache")
        )
        
        if total_size > self.max_size_mb * 1024 * 1024:
            # 删除最旧的文件
            cache_files = sorted(
                self.cache_dir.glob("*.cache"),
                key=lambda f: f.stat().st_mtime
            )
            
            # 删除最旧的文件，直到大小合适
            for cache_file in cache_files[:len(cache_files)//3]:
                cache_file.unlink()
                logger.info(f"Deleted old cache: {cache_file.name}")
    
    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        deleted_count = 0
        
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                if current_time - entry['timestamp'] >= self.ttl:
                    cache_file.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to check cache {cache_file}: {e}")
                cache_file.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired cache files")
    
    def clear(self):
        """清空所有缓存"""
        # 清空内存缓存
        self.memory_cache.clear()
        
        # 清空磁盘缓存
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
        
        logger.info("All cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        disk_size = sum(
            f.stat().st_size for f in self.cache_dir.glob("*.cache")
        ) / (1024 * 1024)  # MB
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': round(hit_rate, 2),
            'memory_entries': len(self.memory_cache),
            'disk_entries': len(list(self.cache_dir.glob("*.cache"))),
            'disk_size_mb': round(disk_size, 2),
            'ttl_seconds': self.ttl
        }


class OCRCache:
    """OCR专用缓存"""
    
    def __init__(self, ttl: int = 300):
        self.cache_manager = CacheManager(cache_dir=".ocr_cache", ttl=ttl)
    
    def get_ocr_result(self, image_hash: str, region: Optional[Dict] = None) -> Optional[Dict]:
        """获取OCR结果缓存"""
        # 生成包含区域信息的键
        cache_key = f"ocr_{image_hash}"
        if region:
            region_str = f"{region.get('x', 0)}_{region.get('y', 0)}_{region.get('width', 0)}_{region.get('height', 0)}"
            cache_key = f"{cache_key}_{region_str}"
        
        return self.cache_manager.get(cache_key)
    
    def set_ocr_result(self, image_hash: str, result: Dict, region: Optional[Dict] = None):
        """设置OCR结果缓存"""
        cache_key = f"ocr_{image_hash}"
        if region:
            region_str = f"{region.get('x', 0)}_{region.get('y', 0)}_{region.get('width', 0)}_{region.get('height', 0)}"
            cache_key = f"{cache_key}_{region_str}"
        
        self.cache_manager.set(cache_key, result)
    
    def clear(self):
        """清空OCR缓存"""
        self.cache_manager.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取OCR缓存统计"""
        stats = self.cache_manager.get_statistics()
        stats['type'] = 'OCR Cache'
        return stats
