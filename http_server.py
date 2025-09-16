from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
from datetime import datetime
from typing import Optional

class HTTPServer:
    def __init__(self, camera_manager, ocr_processor, storage_manager, config_manager):
        self.app = Flask(__name__)
        CORS(self.app)
        
        self.camera_manager = camera_manager
        self.ocr_processor = ocr_processor
        self.storage_manager = storage_manager
        self.config_manager = config_manager
        
        self.server_thread = None
        self.is_running = False
        
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """健康检查服务"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'camera_running': self.camera_manager.is_camera_running(),
                'server_uptime': time.time() - getattr(self, 'start_time', time.time())
            })
        
        @self.app.route('/ocr', methods=['POST'])
        def ocr_endpoint():
            """OCR识别服务"""
            try:
                # 获取当前视频帧
                frame = self.camera_manager.capture_screenshot()
                if frame is None:
                    return jsonify({
                        'error': '无法获取摄像头画面',
                        'timestamp': datetime.now().isoformat()
                    }), 500
                
                # 保存截图
                screenshot_path = self.storage_manager.save_screenshot(frame, "ocr_request")
                
                # OCR识别
                ocr_results = self.ocr_processor.process_image(frame)
                
                return jsonify({
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'screenshot_path': screenshot_path,
                    'results': ocr_results
                })
                
            except Exception as e:
                return jsonify({
                    'error': f'OCR处理失败: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/config/mappings', methods=['GET'])
        def get_mappings():
            """获取字段映射配置"""
            return jsonify({
                'mappings': self.config_manager.get_field_mappings()
            })
        
        @self.app.route('/config/mappings', methods=['POST'])
        def update_mappings():
            """更新字段映射配置"""
            try:
                data = request.get_json()
                if not data or 'mappings' not in data:
                    return jsonify({'error': '无效的请求数据'}), 400
                
                mappings = data['mappings']
                self.config_manager.set_field_mappings(mappings)
                self.ocr_processor.update_field_mappings(mappings)
                
                return jsonify({
                    'success': True,
                    'message': '字段映射已更新'
                })
                
            except Exception as e:
                return jsonify({
                    'error': f'更新字段映射失败: {str(e)}'
                }), 500
        
        @self.app.route('/camera/status', methods=['GET'])
        def camera_status():
            """获取摄像头状态"""
            return jsonify({
                'running': self.camera_manager.is_camera_running(),
                'camera_index': self.camera_manager.camera_index,
                'available_cameras': self.camera_manager.get_available_cameras()
            })
        
        @self.app.route('/storage/stats', methods=['GET'])
        def storage_stats():
            """获取存储统计信息"""
            return jsonify(self.storage_manager.get_storage_stats())
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': '接口不存在'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': '服务器内部错误'}), 500
    
    def start_server(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """启动HTTP服务器"""
        if self.is_running:
            return False
        
        self.start_time = time.time()
        self.is_running = True
        
        def run_server():
            self.app.run(host=host, port=port, debug=debug, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        return True
    
    def stop_server(self):
        """停止HTTP服务器"""
        self.is_running = False
        # Flask服务器停止需要通过其他方式实现
        # 这里只是标记状态
    
    def get_server_status(self) -> dict:
        """获取服务器状态"""
        return {
            'running': self.is_running,
            'start_time': getattr(self, 'start_time', None),
            'uptime': time.time() - getattr(self, 'start_time', time.time()) if self.is_running else 0
        }
