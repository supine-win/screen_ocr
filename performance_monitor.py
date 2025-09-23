#!/usr/bin/env python3
"""
性能监控模块
监控OCR处理性能、内存使用和系统资源
"""

import time
import psutil
import functools
from typing import Dict, List, Any, Callable
from collections import deque
from datetime import datetime
from logger_config import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.ocr_times = deque(maxlen=max_history)
        self.screenshot_times = deque(maxlen=max_history)
        self.memory_usage = deque(maxlen=max_history)
        self.cpu_usage = deque(maxlen=max_history)
        self.success_count = 0
        self.failure_count = 0
        self.start_time = time.time()
    
    def record_ocr_time(self, duration: float):
        """记录OCR处理时间"""
        self.ocr_times.append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })
        logger.debug(f"OCR processing took {duration:.3f} seconds")
    
    def record_screenshot_time(self, duration: float):
        """记录截图时间"""
        self.screenshot_times.append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })
        logger.debug(f"Screenshot took {duration:.3f} seconds")
    
    def record_success(self):
        """记录成功次数"""
        self.success_count += 1
    
    def record_failure(self):
        """记录失败次数"""
        self.failure_count += 1
    
    def update_system_metrics(self):
        """更新系统指标"""
        try:
            # 内存使用
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.memory_usage.append({
                'timestamp': datetime.now().isoformat(),
                'memory_mb': memory_mb
            })
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage.append({
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent
            })
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取性能统计"""
        self.update_system_metrics()
        
        # 计算平均值
        avg_ocr_time = sum(t['duration'] for t in self.ocr_times) / len(self.ocr_times) if self.ocr_times else 0
        avg_screenshot_time = sum(t['duration'] for t in self.screenshot_times) / len(self.screenshot_times) if self.screenshot_times else 0
        avg_memory = sum(m['memory_mb'] for m in self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        avg_cpu = sum(c['cpu_percent'] for c in self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        
        # 计算成功率
        total_requests = self.success_count + self.failure_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        
        # 运行时间
        uptime_seconds = time.time() - self.start_time
        uptime_hours = uptime_seconds / 3600
        
        return {
            'performance': {
                'avg_ocr_time_ms': round(avg_ocr_time * 1000, 2),
                'avg_screenshot_time_ms': round(avg_screenshot_time * 1000, 2),
                'total_requests': total_requests,
                'success_count': self.success_count,
                'failure_count': self.failure_count,
                'success_rate': round(success_rate, 2)
            },
            'system': {
                'memory_mb': round(avg_memory, 2),
                'cpu_percent': round(avg_cpu, 2),
                'uptime_hours': round(uptime_hours, 2)
            },
            'recent': {
                'last_ocr_times': list(self.ocr_times)[-10:],
                'last_screenshot_times': list(self.screenshot_times)[-10:]
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        stats = self.get_statistics()
        
        # 判断健康状态
        health_issues = []
        
        if stats['performance']['avg_ocr_time_ms'] > 5000:
            health_issues.append("OCR处理时间过长")
        
        if stats['performance']['success_rate'] < 90:
            health_issues.append("成功率偏低")
        
        if stats['system']['memory_mb'] > 1000:
            health_issues.append("内存使用过高")
        
        if stats['system']['cpu_percent'] > 80:
            health_issues.append("CPU使用率过高")
        
        return {
            'status': 'healthy' if not health_issues else 'warning',
            'issues': health_issues,
            'statistics': stats
        }


def performance_timer(func: Callable) -> Callable:
    """性能计时装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {duration:.3f} seconds")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f} seconds: {e}")
            raise
    return wrapper


def monitor_memory(threshold_mb: float = 500):
    """内存监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            process = psutil.Process()
            memory_before = process.memory_info().rss / (1024 * 1024)
            
            result = func(*args, **kwargs)
            
            memory_after = process.memory_info().rss / (1024 * 1024)
            memory_increase = memory_after - memory_before
            
            if memory_increase > threshold_mb:
                logger.warning(
                    f"{func.__name__} increased memory by {memory_increase:.2f} MB "
                    f"(before: {memory_before:.2f} MB, after: {memory_after:.2f} MB)"
                )
            
            return result
        return wrapper
    return decorator


# 全局性能监控实例
performance_monitor = PerformanceMonitor()
