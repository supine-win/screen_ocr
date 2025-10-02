from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
import uuid
from datetime import datetime
from typing import Optional
from screenshot_manager import ScreenshotManager
from api_response import APIResponse

class HTTPServer:
    def __init__(self, camera_manager, ocr_processor, storage_manager, config_manager):
        self.app = Flask(__name__)
        
        # 从配置文件读取CORS设置
        cors_config = config_manager.get('http.cors', {})
        if cors_config.get('enabled', True):
            CORS(self.app, 
                 origins=cors_config.get('origins', ['*']),
                 methods=cors_config.get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']),
                 allow_headers=cors_config.get('allow_headers', ['Content-Type', 'Authorization', 'X-Request-ID']),
                 supports_credentials=cors_config.get('supports_credentials', True)
            )
        
        self.camera_manager = camera_manager
        self.ocr_processor = ocr_processor
        self.storage_manager = storage_manager
        self.config_manager = config_manager
        self.screenshot_manager = ScreenshotManager()

        # 截图区域设置 (从配置文件加载)
        self.screenshot_region = self.config_manager.get_screenshot_region()
        
        self.server_thread = None
        self.is_running = False
        
        self._setup_routes()
    
    def _get_request_id(self):
        """获取或生成request_id"""
        return request.headers.get('X-Request-ID') or str(uuid.uuid4())

    def _setup_routes(self):
        """设置路由"""
        
        @self.app.before_request
        def handle_preflight():
            """处理预检请求"""
            if request.method == "OPTIONS":
                cors_config = self.config_manager.get('http.cors', {})
                if cors_config.get('enabled', True):
                    response = jsonify({})
                    
                    # 设置CORS头部
                    origins = cors_config.get('origins', ['*'])
                    if origins == ['*'] or len(origins) == 1 and origins[0] == '*':
                        response.headers.add("Access-Control-Allow-Origin", "*")
                    else:
                        # 如果指定了特定域名，检查请求的Origin
                        origin = request.headers.get('Origin')
                        if origin in origins:
                            response.headers.add("Access-Control-Allow-Origin", origin)
                    
                    headers = ",".join(cors_config.get('allow_headers', ['Content-Type', 'Authorization', 'X-Request-ID']))
                    methods = ",".join(cors_config.get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']))
                    
                    response.headers.add('Access-Control-Allow-Headers', headers)
                    response.headers.add('Access-Control-Allow-Methods', methods)
                    
                    if cors_config.get('supports_credentials', True):
                        response.headers.add('Access-Control-Allow-Credentials', "true")
                    
                    return response

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """健康检查服务"""
            request_id = self._get_request_id()
            
            health_data = {
                'status': 'healthy',
                'camera_running': self.camera_manager.is_camera_running(),
                'server_uptime': time.time() - getattr(self, 'start_time', time.time())
            }
            
            return APIResponse.success_json(
                data=health_data,
                message="系统健康",
                request_id=request_id
            )
        
        @self.app.route('/ocr', methods=['POST'])
        def ocr_endpoint():
            """OCR识别服务"""
            request_id = self._get_request_id()
            
            try:
                # 获取当前视频帧
                frame = self.camera_manager.capture_screenshot()
                if frame is None:
                    return APIResponse.error_json(
                        message="无法获取摄像头画面",
                        code=1001,
                        request_id=request_id,
                        status_code=500
                    )
                
                # 保存截图
                screenshot_path = self.storage_manager.save_screenshot(frame, "ocr_request")
                
                # OCR识别
                ocr_results = self.ocr_processor.process_image(frame)
                
                # 包含field_mappings信息
                data = {
                    'screenshot_path': screenshot_path,
                    'field_mappings': ocr_results,
                    'screenshot_info': {
                        'width': frame.shape[1] if frame is not None else 0,
                        'height': frame.shape[0] if frame is not None else 0
                    }
                }
                
                return APIResponse.success_json(
                    data=data,
                    message="OCR识别成功",
                    request_id=request_id
                )
                
            except Exception as e:
                return APIResponse.from_exception(
                    exception=e,
                    message="OCR处理失败",
                    code=1002,
                    request_id=request_id
                )
        
        @self.app.route('/config/mappings', methods=['GET'])
        def get_mappings():
            """获取字段映射配置"""
            request_id = self._get_request_id()
            
            mappings = self.config_manager.get_field_mappings()
            data = {
                'field_mappings': mappings
            }
            
            return APIResponse.success_json(
                data=data,
                message="获取字段映射成功",
                request_id=request_id
            )
        
        @self.app.route('/config/mappings', methods=['POST'])
        def update_mappings():
            """更新字段映射配置"""
            request_id = self._get_request_id()
            
            try:
                data = request.get_json()
                if not data or 'mappings' not in data:
                    return APIResponse.error_json(
                        message="无效的请求数据，缺少mappings字段",
                        code=2001,
                        request_id=request_id,
                        status_code=400
                    )
                
                mappings = data['mappings']
                self.config_manager.set_field_mappings(mappings)
                self.ocr_processor.update_field_mappings(mappings)
                
                result_data = {
                    'field_mappings': mappings,
                    'updated_count': len(mappings)
                }
                
                return APIResponse.success_json(
                    data=result_data,
                    message="字段映射更新成功",
                    request_id=request_id
                )
                
            except Exception as e:
                return APIResponse.from_exception(
                    exception=e,
                    message="更新字段映射失败",
                    code=2002,
                    request_id=request_id
                )
        
        @self.app.route('/camera/status', methods=['GET'])
        def camera_status():
            """获取摄像头状态"""
            request_id = self._get_request_id()
            
            camera_data = {
                'running': self.camera_manager.is_camera_running(),
                'camera_index': self.camera_manager.camera_index,
                'available_cameras': self.camera_manager.get_available_cameras()
            }
            
            return APIResponse.success_json(
                data=camera_data,
                message="获取摄像头状态成功",
                request_id=request_id
            )
        
        @self.app.route('/storage/stats', methods=['GET'])
        def storage_stats():
            """获取存储统计信息"""
            request_id = self._get_request_id()
            
            stats_data = self.storage_manager.get_storage_stats()
            
            return APIResponse.success_json(
                data=stats_data,
                message="获取存储统计成功",
                request_id=request_id
            )
        
        @self.app.route('/screenshot/ocr', methods=['POST'])
        def screenshot_ocr():
            """屏幕截图OCR识别服务"""
            request_id = self._get_request_id()
            
            try:
                data = request.get_json() or {}
                
                # 获取截图参数 - 优先使用请求中的region，然后使用服务器设置的region
                region = data.get('region') or self.screenshot_region
                method = data.get('method', 'auto')  # 截图方法
                
                # 捕获屏幕截图
                if region:
                    # 区域截图
                    screenshot = self.screenshot_manager.capture_region(
                        region['x'], region['y'], 
                        region['width'], region['height'], 
                        method
                    )
                else:
                    # 全屏截图
                    screenshot = self.screenshot_manager.capture_fullscreen(method)
                
                if screenshot is None:
                    return APIResponse.error_json(
                        message="屏幕截图失败",
                        code=3001,
                        request_id=request_id,
                        status_code=500
                    )
                
                # 保存截图
                screenshot_path = self.storage_manager.save_screenshot(screenshot, "screen_ocr")
                
                # OCR识别
                ocr_results = self.ocr_processor.process_image(screenshot)
                
                # 返回数据
                result_data = {
                    'screenshot_path': screenshot_path,
                    'field_mappings': ocr_results,
                    'screenshot_info': {
                        'width': screenshot.shape[1],
                        'height': screenshot.shape[0],
                        'region': region,
                        'method': method
                    }
                }
                
                return APIResponse.success_json(
                    data=result_data,
                    message="屏幕截图OCR识别成功",
                    request_id=request_id
                )
                
            except Exception as e:
                return APIResponse.from_exception(
                    exception=e,
                    message="屏幕截图OCR处理失败",
                    code=3002,
                    request_id=request_id
                )
        
        @self.app.route('/screenshot/capture', methods=['POST'])
        def screenshot_capture():
            """纯屏幕截图服务（不进行OCR）"""
            try:
                data = request.get_json() or {}
                
                # 获取截图参数 - 优先使用请求中的region，然后使用服务器设置的region
                region = data.get('region') or self.screenshot_region
                method = data.get('method', 'auto')
                save_file = data.get('save', True)  # 是否保存文件
                
                # 捕获屏幕截图
                if region:
                    screenshot = self.screenshot_manager.capture_region(
                        region['x'], region['y'], 
                        region['width'], region['height'], 
                        method
                    )
                else:
                    screenshot = self.screenshot_manager.capture_fullscreen(method)
                
                if screenshot is None:
                    return jsonify({
                        'error': '屏幕截图失败',
                        'timestamp': datetime.now().isoformat()
                    }), 500
                
                result = {
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'screenshot_size': {
                        'width': screenshot.shape[1],
                        'height': screenshot.shape[0]
                    }
                }
                
                # 保存截图文件
                if save_file:
                    screenshot_path = self.storage_manager.save_screenshot(screenshot, "screen_capture")
                    result['screenshot_path'] = screenshot_path
                
                return jsonify(result)
                
            except Exception as e:
                return jsonify({
                    'error': f'屏幕截图失败: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.route('/screenshot/info', methods=['GET'])
        def screenshot_info():
            """获取屏幕截图相关信息"""
            return jsonify({
                'screen_size': self.screenshot_manager.get_screen_size(),
                'available_methods': self.screenshot_manager.get_available_methods(),
                'system': self.screenshot_manager.system,
                'current_region': self.screenshot_region
            })
        
        @self.app.route('/screenshot/region', methods=['GET'])
        def get_screenshot_region():
            """获取当前截图区域设置"""
            return jsonify({
                'region': self.screenshot_region,
                'mode': 'region' if self.screenshot_region else 'fullscreen'
            })
        
        @self.app.route('/screenshot/region', methods=['POST'])
        def set_screenshot_region():
            """设置截图区域"""
            try:
                data = request.get_json() or {}
                
                if data.get('mode') == 'fullscreen':
                    self.screenshot_region = None
                    self.config_manager.set_screenshot_region(None)
                    return jsonify({
                        'success': True,
                        'message': '已设置为全屏截图',
                        'region': None
                    })
                
                elif data.get('mode') == 'region':
                    region = data.get('region')
                    if not region:
                        return jsonify({'error': '区域截图模式需要提供region参数'}), 400
                    
                    # 验证区域参数
                    required_keys = ['x', 'y', 'width', 'height']
                    if not all(key in region for key in required_keys):
                        return jsonify({'error': f'region必须包含: {required_keys}'}), 400
                    
                    # 验证数值
                    try:
                        x, y, width, height = region['x'], region['y'], region['width'], region['height']
                        x, y, width, height = int(x), int(y), int(width), int(height)
                    except (ValueError, TypeError):
                        return jsonify({'error': '区域坐标必须为整数'}), 400
                    
                    # 检查边界
                    screen_width, screen_height = self.screenshot_manager.get_screen_size()
                    if x < 0 or y < 0 or width <= 0 or height <= 0:
                        return jsonify({'error': '坐标和尺寸必须为正数'}), 400
                    
                    if x + width > screen_width or y + height > screen_height:
                        return jsonify({'error': '截图区域超出屏幕范围'}), 400

                    self.screenshot_region = {'x': x, 'y': y, 'width': width, 'height': height}
                    self.config_manager.set_screenshot_region(self.screenshot_region)

                    return jsonify({
                        'success': True,
                        'message': f'已设置区域截图: ({x}, {y}) {width}x{height}',
                        'region': self.screenshot_region
                    })
                
                else:
                    return jsonify({'error': 'mode必须为fullscreen或region'}), 400
                    
            except Exception as e:
                return jsonify({
                    'error': f'设置截图区域失败: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': '接口不存在'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': '服务器内部错误'}), 500
    
    def start_server(self, host: str = '0.0.0.0', port: int = 9501, debug: bool = False):
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
