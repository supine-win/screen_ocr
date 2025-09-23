#!/usr/bin/env python3
"""
健康检查和监控模块
提供系统健康状态监控和诊断功能
"""

import os
import psutil
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, request

from logger_config import get_logger
from performance_monitor import performance_monitor
from cache_manager import CacheManager
from error_handler import error_handler

logger = get_logger(__name__)

class HealthMonitor:
    """健康监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks_history = []
        self.alerts = []
        
        # 健康阈值配置
        self.thresholds = {
            'memory_mb': 1000,
            'cpu_percent': 80,
            'disk_usage_percent': 90,
            'error_rate_percent': 10,
            'avg_response_time_ms': 5000,
            'cache_hit_rate_min': 30
        }
    
    def check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'uptime_hours': (time.time() - self.start_time) / 3600,
            'checks': {}
        }
        
        # 1. 内存检查
        memory_check = self._check_memory()
        health_status['checks']['memory'] = memory_check
        
        # 2. CPU检查
        cpu_check = self._check_cpu()
        health_status['checks']['cpu'] = cpu_check
        
        # 3. 磁盘检查
        disk_check = self._check_disk()
        health_status['checks']['disk'] = disk_check
        
        # 4. OCR服务检查
        ocr_check = self._check_ocr_service()
        health_status['checks']['ocr'] = ocr_check
        
        # 5. 性能检查
        performance_check = self._check_performance()
        health_status['checks']['performance'] = performance_check
        
        # 6. 错误率检查
        error_check = self._check_error_rate()
        health_status['checks']['errors'] = error_check
        
        # 判断总体健康状态
        all_checks = [
            memory_check, cpu_check, disk_check,
            ocr_check, performance_check, error_check
        ]
        
        if any(check['status'] == 'critical' for check in all_checks):
            health_status['status'] = 'critical'
        elif any(check['status'] == 'warning' for check in all_checks):
            health_status['status'] = 'warning'
        
        # 记录历史
        self.checks_history.append(health_status)
        if len(self.checks_history) > 100:
            self.checks_history.pop(0)
        
        # 生成告警
        self._generate_alerts(health_status)
        
        return health_status
    
    def _check_memory(self) -> Dict[str, Any]:
        """检查内存使用"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        memory_percent = psutil.virtual_memory().percent
        
        status = 'healthy'
        if memory_mb > self.thresholds['memory_mb']:
            status = 'warning'
        if memory_mb > self.thresholds['memory_mb'] * 1.5:
            status = 'critical'
        
        return {
            'status': status,
            'memory_mb': round(memory_mb, 2),
            'memory_percent': round(memory_percent, 2),
            'threshold_mb': self.thresholds['memory_mb']
        }
    
    def _check_cpu(self) -> Dict[str, Any]:
        """检查CPU使用"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        status = 'healthy'
        if cpu_percent > self.thresholds['cpu_percent']:
            status = 'warning'
        if cpu_percent > 95:
            status = 'critical'
        
        return {
            'status': status,
            'cpu_percent': round(cpu_percent, 2),
            'cpu_count': psutil.cpu_count(),
            'threshold_percent': self.thresholds['cpu_percent']
        }
    
    def _check_disk(self) -> Dict[str, Any]:
        """检查磁盘使用"""
        disk_usage = psutil.disk_usage('/')
        
        status = 'healthy'
        if disk_usage.percent > self.thresholds['disk_usage_percent']:
            status = 'warning'
        if disk_usage.percent > 95:
            status = 'critical'
        
        return {
            'status': status,
            'disk_usage_percent': round(disk_usage.percent, 2),
            'free_gb': round(disk_usage.free / (1024**3), 2),
            'total_gb': round(disk_usage.total / (1024**3), 2),
            'threshold_percent': self.thresholds['disk_usage_percent']
        }
    
    def _check_ocr_service(self) -> Dict[str, Any]:
        """检查OCR服务状态"""
        try:
            # 检查OCR引擎是否可用
            ocr_available = False
            engines = []
            
            try:
                import easyocr
                engines.append('easyocr')
                ocr_available = True
            except ImportError:
                pass
            
            try:
                import paddleocr
                engines.append('paddleocr')
                ocr_available = True
            except ImportError:
                pass
            
            status = 'healthy' if ocr_available else 'critical'
            
            return {
                'status': status,
                'available': ocr_available,
                'engines': engines
            }
        except Exception as e:
            logger.error(f"OCR service check failed: {e}")
            return {
                'status': 'critical',
                'available': False,
                'error': str(e)
            }
    
    def _check_performance(self) -> Dict[str, Any]:
        """检查性能指标"""
        stats = performance_monitor.get_statistics()
        
        avg_response_time = stats['performance']['avg_ocr_time_ms']
        success_rate = stats['performance']['success_rate']
        
        status = 'healthy'
        if avg_response_time > self.thresholds['avg_response_time_ms']:
            status = 'warning'
        if success_rate < 80:
            status = 'warning'
        if success_rate < 50:
            status = 'critical'
        
        return {
            'status': status,
            'avg_response_time_ms': avg_response_time,
            'success_rate': success_rate,
            'total_requests': stats['performance']['total_requests']
        }
    
    def _check_error_rate(self) -> Dict[str, Any]:
        """检查错误率"""
        error_stats = error_handler.get_error_statistics()
        perf_stats = performance_monitor.get_statistics()
        
        total_requests = perf_stats['performance']['total_requests']
        total_errors = error_stats['total_errors']
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        status = 'healthy'
        if error_rate > self.thresholds['error_rate_percent']:
            status = 'warning'
        if error_rate > 20:
            status = 'critical'
        
        return {
            'status': status,
            'error_rate_percent': round(error_rate, 2),
            'total_errors': total_errors,
            'recent_errors': len(error_stats.get('recent_errors', []))
        }
    
    def _generate_alerts(self, health_status: Dict[str, Any]):
        """生成告警"""
        for check_name, check_result in health_status['checks'].items():
            if check_result['status'] in ['warning', 'critical']:
                alert = {
                    'timestamp': health_status['timestamp'],
                    'level': check_result['status'],
                    'component': check_name,
                    'message': f"{check_name} is {check_result['status']}",
                    'details': check_result
                }
                
                self.alerts.append(alert)
                
                # 保留最近100条告警
                if len(self.alerts) > 100:
                    self.alerts.pop(0)
                
                # 记录到日志
                if check_result['status'] == 'critical':
                    logger.error(f"Critical alert: {alert['message']}")
                else:
                    logger.warning(f"Warning alert: {alert['message']}")
    
    def get_alerts(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取告警"""
        if since:
            return [
                alert for alert in self.alerts
                if datetime.fromisoformat(alert['timestamp']) > since
            ]
        return self.alerts[-20:]  # 默认返回最近20条
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标"""
        # 性能指标
        perf_stats = performance_monitor.get_statistics()
        
        # 系统指标
        system_stats = {
            'memory': {
                'used_mb': psutil.Process().memory_info().rss / (1024 * 1024),
                'percent': psutil.virtual_memory().percent
            },
            'cpu': {
                'percent': psutil.cpu_percent(interval=0.1),
                'count': psutil.cpu_count()
            },
            'disk': {
                'usage_percent': psutil.disk_usage('/').percent,
                'free_gb': psutil.disk_usage('/').free / (1024**3)
            }
        }
        
        # 错误指标
        error_stats = error_handler.get_error_statistics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'uptime_hours': (time.time() - self.start_time) / 3600,
            'performance': perf_stats['performance'],
            'system': system_stats,
            'errors': {
                'total': error_stats['total_errors'],
                'by_type': error_stats.get('by_type', {})
            }
        }


# 创建Flask Blueprint用于健康检查API
health_blueprint = Blueprint('health', __name__)
health_monitor = HealthMonitor()


@health_blueprint.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    health_status = health_monitor.check_system_health()
    
    # 根据健康状态返回不同的HTTP状态码
    http_status = 200
    if health_status['status'] == 'warning':
        http_status = 200  # 仍然返回200，但状态为warning
    elif health_status['status'] == 'critical':
        http_status = 503  # Service Unavailable
    
    return jsonify(health_status), http_status


@health_blueprint.route('/health/detailed', methods=['GET'])
def detailed_health():
    """详细健康检查"""
    health_status = health_monitor.check_system_health()
    metrics = health_monitor.get_metrics()
    
    return jsonify({
        'health': health_status,
        'metrics': metrics,
        'alerts': health_monitor.get_alerts()
    })


@health_blueprint.route('/metrics', methods=['GET'])
def metrics():
    """获取监控指标"""
    return jsonify(health_monitor.get_metrics())


@health_blueprint.route('/alerts', methods=['GET'])
def alerts():
    """获取告警"""
    # 支持查询参数
    since_str = request.args.get('since')
    since = None
    
    if since_str:
        try:
            since = datetime.fromisoformat(since_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    return jsonify({
        'alerts': health_monitor.get_alerts(since),
        'total': len(health_monitor.alerts)
    })


@health_blueprint.route('/diagnostics', methods=['GET'])
def diagnostics():
    """系统诊断信息"""
    try:
        # 收集诊断信息
        diagnostics_info = {
            'timestamp': datetime.now().isoformat(),
            'python_version': os.sys.version,
            'platform': os.sys.platform,
            'working_directory': os.getcwd(),
            'environment': {
                'PYTHONPATH': os.environ.get('PYTHONPATH', 'Not set'),
                'PATH': os.environ.get('PATH', 'Not set')[:200]  # 截断避免太长
            },
            'process': {
                'pid': os.getpid(),
                'threads': psutil.Process().num_threads(),
                'open_files': len(psutil.Process().open_files()),
                'connections': len(psutil.Process().connections())
            },
            'modules': {
                'easyocr': _check_module('easyocr'),
                'paddleocr': _check_module('paddleocr'),
                'torch': _check_module('torch'),
                'cv2': _check_module('cv2')
            }
        }
        
        return jsonify(diagnostics_info)
        
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        return jsonify({'error': str(e)}), 500


def _check_module(module_name: str) -> Dict[str, Any]:
    """检查模块是否可用"""
    try:
        module = __import__(module_name)
        return {
            'available': True,
            'version': getattr(module, '__version__', 'Unknown')
        }
    except ImportError:
        return {
            'available': False,
            'version': None
        }
