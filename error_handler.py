#!/usr/bin/env python3
"""
错误处理和重试机制
提供统一的错误处理、重试逻辑和降级策略
"""

import time
import functools
import traceback
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from logger_config import get_logger

logger = get_logger(__name__)

class ErrorType(Enum):
    """错误类型枚举"""
    OCR_FAILURE = "OCR识别失败"
    SCREENSHOT_FAILURE = "截图失败"
    CAMERA_FAILURE = "摄像头错误"
    NETWORK_ERROR = "网络错误"
    FILE_IO_ERROR = "文件IO错误"
    CONFIG_ERROR = "配置错误"
    MEMORY_ERROR = "内存错误"
    TIMEOUT_ERROR = "超时错误"
    UNKNOWN_ERROR = "未知错误"

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.error_count = {}
        self.error_history = []
        self.max_history = 100
        
    def log_error(self, error_type: ErrorType, error: Exception, context: Optional[Dict] = None):
        """记录错误"""
        error_info = {
            'type': error_type.value,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': time.time(),
            'context': context or {}
        }
        
        # 更新错误计数
        if error_type not in self.error_count:
            self.error_count[error_type] = 0
        self.error_count[error_type] += 1
        
        # 添加到历史记录
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # 记录日志
        logger.error(f"{error_type.value}: {error}", exc_info=True)
        
        return error_info
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        total_errors = sum(self.error_count.values())
        
        # 按错误类型分组
        error_by_type = {}
        for error_type, count in self.error_count.items():
            error_by_type[error_type.value] = {
                'count': count,
                'percentage': round(count / total_errors * 100, 2) if total_errors > 0 else 0
            }
        
        # 获取最近的错误
        recent_errors = self.error_history[-10:]
        
        return {
            'total_errors': total_errors,
            'by_type': error_by_type,
            'recent_errors': recent_errors
        }
    
    def should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """判断是否应该重试"""
        # 某些错误类型不重试
        no_retry_types = [ErrorType.CONFIG_ERROR, ErrorType.MEMORY_ERROR]
        if error_type in no_retry_types:
            return False
        
        # 基于错误频率决定是否重试
        recent_count = self.error_count.get(error_type, 0)
        if recent_count > 10:  # 如果该类型错误太频繁，停止重试
            logger.warning(f"Too many {error_type.value} errors, stopping retry")
            return False
        
        # 最多重试3次
        return attempt < 3


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    fallback: Optional[Callable] = None
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍增因子
        exceptions: 需要重试的异常类型
        fallback: 失败后的降级函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                            f", retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
            
            # 所有重试都失败，使用降级策略
            if fallback:
                logger.info(f"Using fallback for {func.__name__}")
                return fallback(*args, **kwargs)
            else:
                raise last_exception
        
        return wrapper
    return decorator


def timeout(seconds: int):
    """
    超时装饰器（使用signal，仅Unix系统）
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Function timed out after {seconds} seconds")
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 设置超时处理器
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # 取消超时
                signal.alarm(0)
            
            return result
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    default: Any = None,
    error_handler: Optional[ErrorHandler] = None,
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR
) -> Any:
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        args: 函数参数
        kwargs: 函数关键字参数
        default: 出错时的默认返回值
        error_handler: 错误处理器
        error_type: 错误类型
    
    Returns:
        函数执行结果或默认值
    """
    kwargs = kwargs or {}
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler.log_error(error_type, e, {
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            })
        else:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
        
        return default


class CircuitBreaker:
    """
    熔断器模式实现
    当错误率过高时，自动熔断，避免连续失败
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Args:
            failure_threshold: 失败阈值，连续失败这么多次后熔断
            recovery_timeout: 恢复超时时间（秒）
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器调用函数"""
        # 检查是否应该尝试恢复
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half_open'
                logger.info(f"Circuit breaker entering half-open state for {func.__name__}")
            else:
                raise Exception(f"Circuit breaker is open for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            
            # 成功调用，重置失败计数
            if self.state == 'half_open':
                self.state = 'closed'
                logger.info(f"Circuit breaker closed for {func.__name__}")
            
            self.failure_count = 0
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
                logger.error(f"Circuit breaker opened for {func.__name__} after {self.failure_count} failures")
            
            raise e
    
    def reset(self):
        """重置熔断器"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'


# 全局错误处理器
error_handler = ErrorHandler()
