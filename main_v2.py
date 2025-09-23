#!/usr/bin/env python3
"""
MonitorOCR v2 - 优化版主入口
集成所有优化模块，提供更好的性能和稳定性
"""

import argparse
import sys
import signal
import time
from pathlib import Path

# 导入优化模块
from logger_config import logger_config, get_logger
from config_validator import ConfigValidator
from performance_monitor import performance_monitor
from cache_manager import CacheManager, OCRCache
from error_handler import error_handler, ErrorType
from health_monitor import health_blueprint, health_monitor

# 导入核心模块
from config_manager import ConfigManager
from camera_manager import CameraManager
from ocr_processor_v2 import OCRProcessorV2
from screenshot_manager import ScreenshotManager
from storage_manager import StorageManager
from http_server import HTTPServer
from gui_app import MonitorOCRApp

logger = get_logger(__name__)

class MonitorOCRV2:
    """优化版MonitorOCR应用"""
    
    def __init__(self):
        """初始化应用"""
        logger.info("=" * 60)
        logger.info("MonitorOCR v2 - Starting up...")
        logger.info("=" * 60)
        
        # 加载和验证配置
        self.config = ConfigValidator.load_and_validate()
        logger.info("Configuration loaded and validated")
        
        # 初始化核心组件
        self.camera_manager = None
        self.ocr_processor = None
        self.screenshot_manager = None
        self.storage_manager = None
        self.http_server = None
        self.gui_app = None
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        # 清理旧日志
        logger_config.cleanup_old_logs(days=7)
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize_components(self, no_gui: bool = False):
        """初始化组件"""
        try:
            # 初始化存储管理器
            storage_dir = self.config.get('storage', {}).get('screenshot_dir', './screenshots')
            self.storage_manager = StorageManager(storage_dir)
            logger.info("Storage manager initialized")
            
            # 初始化摄像头管理器
            self.camera_manager = CameraManager()
            camera_config = self.config.get('camera', {})
            camera_index = camera_config.get('selected_index', 1)
            resolution = tuple(camera_config.get('resolution', [1920, 1080]))
            
            if self.camera_manager.start_camera(camera_index, resolution):
                logger.info(f"Camera {camera_index} started successfully")
            else:
                logger.warning(f"Failed to start camera {camera_index}")
            
            # 初始化OCR处理器V2
            self.ocr_processor = OCRProcessorV2(self.config)
            logger.info("OCR processor v2 initialized")
            
            # 初始化截图管理器
            self.screenshot_manager = ScreenshotManager()
            logger.info("Screenshot manager initialized")
            
            # 初始化HTTP服务器（带健康检查）
            if not no_gui or self.config.get('http', {}).get('enabled', True):
                self.http_server = HTTPServer(
                    self.config,
                    self.camera_manager,
                    self.ocr_processor,
                    self.screenshot_manager,
                    self.storage_manager
                )
                
                # 注册健康检查蓝图
                self.http_server.app.register_blueprint(health_blueprint, url_prefix='/api')
                
                # 启动HTTP服务器
                host = self.config.get('http', {}).get('host', '0.0.0.0')
                port = self.config.get('http', {}).get('port', 8080)
                debug = self.config.get('http', {}).get('debug', False)
                
                self.http_server.start(host, port, debug)
                logger.info(f"HTTP server started on {host}:{port}")
                
                # 打印健康检查URL
                logger.info(f"Health check available at http://{host}:{port}/api/health")
                logger.info(f"Metrics available at http://{host}:{port}/api/metrics")
            
            # 初始化GUI（如果需要）
            if not no_gui:
                self.gui_app = MonitorOCRApp(
                    self.config_manager,
                    self.camera_manager,
                    self.ocr_processor,
                    self.screenshot_manager,
                    self.storage_manager
                )
                logger.info("GUI application initialized")
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            error_handler.log_error(ErrorType.UNKNOWN_ERROR, e)
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def run(self, no_gui: bool = False):
        """运行应用"""
        try:
            # 初始化组件
            if not self.initialize_components(no_gui):
                logger.error("Failed to initialize, exiting...")
                return 1
            
            # 执行启动健康检查
            health_status = health_monitor.check_system_health()
            if health_status['status'] == 'critical':
                logger.error("System health check failed, please check alerts")
                logger.error(f"Alerts: {health_monitor.get_alerts()}")
                
                # 询问是否继续
                if not no_gui:
                    response = input("System has critical issues. Continue anyway? (y/n): ")
                    if response.lower() != 'y':
                        return 1
            
            # 运行主循环
            if no_gui:
                logger.info("Running in no-GUI mode (API server only)")
                logger.info("Press Ctrl+C to quit")
                
                # 定期健康检查和性能报告
                last_report_time = time.time()
                
                try:
                    while True:
                        time.sleep(10)
                        
                        # 每分钟输出一次性能报告
                        if time.time() - last_report_time > 60:
                            self._print_performance_report()
                            last_report_time = time.time()
                            
                            # 执行健康检查
                            health_status = health_monitor.check_system_health()
                            if health_status['status'] != 'healthy':
                                logger.warning(f"Health status: {health_status['status']}")
                
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt")
            
            else:
                # 运行GUI
                logger.info("Starting GUI application")
                self.gui_app.run()
            
            return 0
            
        except Exception as e:
            error_handler.log_error(ErrorType.UNKNOWN_ERROR, e)
            logger.error(f"Application error: {e}")
            return 1
        
        finally:
            self.shutdown()
    
    def _print_performance_report(self):
        """打印性能报告"""
        stats = performance_monitor.get_statistics()
        cache_stats = OCRCache().get_statistics()
        
        logger.info("=" * 60)
        logger.info("Performance Report")
        logger.info("-" * 60)
        logger.info(f"OCR Performance:")
        logger.info(f"  - Average time: {stats['performance']['avg_ocr_time_ms']:.2f} ms")
        logger.info(f"  - Success rate: {stats['performance']['success_rate']:.2f}%")
        logger.info(f"  - Total requests: {stats['performance']['total_requests']}")
        logger.info(f"Cache Performance:")
        logger.info(f"  - Hit rate: {cache_stats['hit_rate']:.2f}%")
        logger.info(f"  - Memory entries: {cache_stats['memory_entries']}")
        logger.info(f"  - Disk entries: {cache_stats['disk_entries']}")
        logger.info(f"System Resources:")
        logger.info(f"  - Memory: {stats['system']['memory_mb']:.2f} MB")
        logger.info(f"  - CPU: {stats['system']['cpu_percent']:.2f}%")
        logger.info(f"  - Uptime: {stats['system']['uptime_hours']:.2f} hours")
        logger.info("=" * 60)
    
    def shutdown(self):
        """关闭应用"""
        logger.info("Shutting down MonitorOCR v2...")
        
        # 停止HTTP服务器
        if self.http_server:
            self.http_server.stop()
            logger.info("HTTP server stopped")
        
        # 停止摄像头
        if self.camera_manager:
            self.camera_manager.stop_camera()
            logger.info("Camera stopped")
        
        # 清理OCR处理器
        if self.ocr_processor:
            self.ocr_processor.cleanup()
            logger.info("OCR processor cleaned up")
        
        # 清理存储
        if self.storage_manager:
            cleanup_days = self.config.get('storage', {}).get('auto_cleanup_days', 30)
            self.storage_manager.cleanup_old_files(cleanup_days)
            logger.info(f"Cleaned up files older than {cleanup_days} days")
        
        # 打印最终统计
        self._print_performance_report()
        
        # 保存错误日志
        error_stats = error_handler.get_error_statistics()
        if error_stats['total_errors'] > 0:
            logger.warning(f"Total errors during session: {error_stats['total_errors']}")
            
            # 保存错误报告
            error_report_path = Path("logs") / f"error_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            try:
                import json
                with open(error_report_path, 'w', encoding='utf-8') as f:
                    json.dump(error_stats, f, indent=2)
                logger.info(f"Error report saved to {error_report_path}")
            except Exception as e:
                logger.error(f"Failed to save error report: {e}")
        
        logger.info("MonitorOCR v2 shutdown complete")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MonitorOCR v2 - Optimized OCR System')
    parser.add_argument('--no-gui', action='store_true', help='Run without GUI (API server only)')
    parser.add_argument('--config', type=str, default='config.json', help='Configuration file path')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level')
    parser.add_argument('--clean-cache', action='store_true', help='Clean all cache before starting')
    parser.add_argument('--health-check', action='store_true', help='Run health check and exit')
    
    args = parser.parse_args()
    
    # 设置日志级别
    import logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # 清理缓存（如果需要）
    if args.clean_cache:
        logger.info("Cleaning all cache...")
        OCRCache().clear()
        logger.info("Cache cleaned")
    
    # 健康检查模式
    if args.health_check:
        logger.info("Running health check...")
        health_status = health_monitor.check_system_health()
        print(f"Health Status: {health_status['status']}")
        
        for component, result in health_status['checks'].items():
            print(f"  {component}: {result['status']}")
        
        if health_status['status'] != 'healthy':
            print("\nAlerts:")
            for alert in health_monitor.get_alerts()[:5]:
                print(f"  - [{alert['level']}] {alert['message']}")
        
        return 0 if health_status['status'] != 'critical' else 1
    
    # 运行应用
    app = MonitorOCRV2()
    return app.run(args.no_gui)


if __name__ == '__main__':
    sys.exit(main())
