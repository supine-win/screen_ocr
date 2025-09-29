#!/usr/bin/env python3
"""
监控OCR系统主程序
支持摄像头视频流捕获、OCR识别、HTTP服务等功能
"""

import sys
import os
from pathlib import Path

# 在打包环境中，首先应用所有优化
if getattr(sys, 'frozen', False):
    print("  启动exe环境优化...")
    
    # 1. 应用EasyOCR离线补丁
    try:
        import easyocr_offline_patch
        print("  EasyOCR离线补丁已应用")
    except Exception as e:
        print(f"   EasyOCR离线补丁应用失败: {e}")
    
    # 2. 应用exe优化设置
    try:
        from exe_optimization import optimize_for_exe, get_performance_tips
        if optimize_for_exe():
            # 首次启动提示
            if not os.path.exists("./first_run_complete.flag"):
                print("\n   首次启动说明:")
                tips = get_performance_tips()
                for tip in tips[:3]:  # 显示前3个关键提示
                    print(f"    {tip}")
                # 创建首次运行标记
                with open("./first_run_complete.flag", "w") as f:
                    f.write("first_run_completed")
                print()
    except ImportError:
        print("   exe优化模块未找到，使用基础优化")
        
        # 基础优化设置
        os.environ['TORCH_DISABLE_PIN_MEMORY_WARNING'] = '1'
        os.environ['OMP_NUM_THREADS'] = '2'
        
        try:
            import torch
            if not torch.cuda.is_available():
                torch.set_num_threads(2)
                torch.backends.cudnn.enabled = False
                print("   基础Torch优化已应用")
        except ImportError:
            pass

from gui_app import MonitorOCRApp
from model_path_manager import ModelPathManager
from simple_logger import get_logger, log_info, log_error

def main():
    """主函数"""
    import argparse
    
    # 创建调试信息（用于诊断Windows打包问题）
    try:
        debug_info = ModelPathManager.create_debug_info()
        print(f"运行环境: {debug_info['environment']}")
    except Exception as e:
        print(f"调试信息创建失败: {e}")
    
    parser = argparse.ArgumentParser(description='监控OCR系统')
    parser.add_argument('--no-gui', action='store_true', help='无GUI模式运行')
    parser.add_argument('--config', default='config.json', help='配置文件路径')
    parser.add_argument('--debug', action='store_true', help='运行调试检查')
    
    args = parser.parse_args()
    
    # 调试模式
    if args.debug:
        try:
            import debug_windows
            debug_windows.main()
            return
        except ImportError:
            print("调试模块不可用")
        except Exception as e:
            print(f"调试失败: {e}")
        return
    
    if args.no_gui:
        # 无GUI模式 - 仅启动HTTP服务
        from camera_manager import CameraManager
        from ocr_processor import OCRProcessor
        from storage_manager import StorageManager
        from config_manager import ConfigManager
        from http_server import HTTPServer
        
        log_info("启动无GUI模式...")
        
        # 初始化组件
        config_manager = ConfigManager(args.config)
        camera_manager = CameraManager()
        storage_manager = StorageManager(
            config_manager.get('storage.screenshot_dir', './screenshots')
        )
        ocr_processor = OCRProcessor(config_manager.get_ocr_config())
        http_server = HTTPServer(
            camera_manager, 
            ocr_processor, 
            storage_manager, 
            config_manager
        )
        
        # 启动摄像头
        camera_index = config_manager.get('camera.selected_index', 0)
        resolution = config_manager.get('camera.resolution', [1920, 1080])
        
        if camera_manager.start_camera(camera_index, tuple(resolution)):
            print(f"摄像头 {camera_index} 启动成功")
        else:
            print(f"摄像头 {camera_index} 启动失败")
            return 1
        
        # 启动HTTP服务
        http_config = config_manager.get_http_config()
        host = http_config.get('host', '0.0.0.0')
        port = http_config.get('port', 8080)
        debug = http_config.get('debug', False)
        
        print(f"启动HTTP服务: http://{host}:{port}")
        
        try:
            http_server.start_server(host, port, debug)
            print("HTTP服务启动成功")
            print("按 Ctrl+C 退出")
            
            # 保持运行
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n正在关闭服务...")
            camera_manager.stop_camera()
            http_server.stop_server()
            print("服务已关闭")
            return 0
        except Exception as e:
            print(f"服务启动失败: {e}")
            return 1
    
    else:
        # GUI模式
        try:
            app = MonitorOCRApp()
            app.run()
            return 0
        except Exception as e:
            print(f"GUI启动失败: {e}")
            return 1

if __name__ == "__main__":
    sys.exit(main())
