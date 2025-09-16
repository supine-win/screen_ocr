import cv2
import threading
import time
from typing import List, Optional, Tuple
import numpy as np

class CameraManager:
    def __init__(self):
        self.camera = None
        self.camera_index = 0
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        
    def get_available_cameras(self) -> List[int]:
        """获取可用摄像头列表"""
        available_cameras = []
        for i in range(10):  # 检查前10个摄像头
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(i)
                cap.release()
        return available_cameras
    
    def get_camera_info(self, camera_index: int) -> dict:
        """获取摄像头信息"""
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return {}
        
        info = {
            'index': camera_index,
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(cap.get(cv2.CAP_PROP_FPS))
        }
        cap.release()
        return info
    
    def start_camera(self, camera_index: int, resolution: Tuple[int, int] = (1920, 1080)) -> bool:
        """启动摄像头"""
        if self.is_running:
            self.stop_camera()
        
        self.camera = cv2.VideoCapture(camera_index)
        if not self.camera.isOpened():
            return False
        
        # 设置分辨率
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        
        self.camera_index = camera_index
        self.is_running = True
        
        # 启动捕获线程
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        return True
    
    def stop_camera(self):
        """停止摄像头"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def _capture_loop(self):
        """摄像头捕获循环"""
        while self.is_running and self.camera:
            ret, frame = self.camera.read()
            if ret:
                with self.frame_lock:
                    self.current_frame = frame.copy()
            time.sleep(0.033)  # ~30 FPS
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """获取当前帧"""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def capture_screenshot(self) -> Optional[np.ndarray]:
        """捕获截图"""
        return self.get_current_frame()
    
    def is_camera_running(self) -> bool:
        """检查摄像头是否运行中"""
        return self.is_running and self.camera is not None
