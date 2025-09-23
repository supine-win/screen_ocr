#!/usr/bin/env python3
"""
屏幕截图管理器
支持全屏截图、区域截图、多显示器截图等功能
"""

import cv2
import numpy as np
import platform
from typing import Tuple, Optional, List
import time
import os

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ScreenshotManager:
    def __init__(self):
        """初始化屏幕截图管理器"""
        self.system = platform.system()
        self.available_methods = self._check_available_methods()
        
        # 设置pyautogui安全模式
        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = True
    
    def _check_available_methods(self) -> List[str]:
        """检查可用的截图方法"""
        methods = []
        
        if PYAUTOGUI_AVAILABLE:
            methods.append('pyautogui')
        
        if PIL_AVAILABLE:
            methods.append('pil')
        
        # macOS特有方法
        if self.system == 'Darwin':
            methods.append('screencapture')
        
        # Windows特有方法
        elif self.system == 'Windows':
            try:
                import win32gui
                import win32ui
                import win32con
                methods.append('win32')
            except ImportError:
                pass
        
        return methods
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        if PYAUTOGUI_AVAILABLE:
            return pyautogui.size()
        elif PIL_AVAILABLE:
            screenshot = ImageGrab.grab()
            return screenshot.size
        else:
            # 默认尺寸
            return (1920, 1080)
    
    def capture_fullscreen(self, method: str = 'auto') -> Optional[np.ndarray]:
        """
        捕获全屏截图
        
        Args:
            method: 截图方法 ('auto', 'pyautogui', 'pil', 'screencapture', 'win32')
        
        Returns:
            截图的numpy数组 (BGR格式)，失败返回None
        """
        if method == 'auto':
            method = self.available_methods[0] if self.available_methods else 'pyautogui'
        
        try:
            if method == 'pyautogui' and PYAUTOGUI_AVAILABLE:
                return self._capture_with_pyautogui()
            elif method == 'pil' and PIL_AVAILABLE:
                return self._capture_with_pil()
            elif method == 'screencapture' and self.system == 'Darwin':
                return self._capture_with_screencapture()
            elif method == 'win32' and self.system == 'Windows':
                return self._capture_with_win32()
            else:
                # 回退到可用方法
                for available_method in self.available_methods:
                    result = self.capture_fullscreen(available_method)
                    if result is not None:
                        return result
                return None
                
        except Exception as e:
            print(f"截图失败 (方法: {method}): {e}")
            return None
    
    def capture_region(self, x: int, y: int, width: int, height: int, 
                      method: str = 'auto') -> Optional[np.ndarray]:
        """
        捕获指定区域截图
        
        Args:
            x, y: 区域左上角坐标
            width, height: 区域宽度和高度
            method: 截图方法
        
        Returns:
            截图的numpy数组 (BGR格式)，失败返回None
        """
        if method == 'auto':
            method = self.available_methods[0] if self.available_methods else 'pyautogui'
        
        try:
            if method == 'pyautogui' and PYAUTOGUI_AVAILABLE:
                return self._capture_region_with_pyautogui(x, y, width, height)
            elif method == 'pil' and PIL_AVAILABLE:
                return self._capture_region_with_pil(x, y, width, height)
            else:
                # 先截全屏，然后裁剪
                fullscreen = self.capture_fullscreen(method)
                if fullscreen is not None:
                    return fullscreen[y:y+height, x:x+width]
                return None
                
        except Exception as e:
            print(f"区域截图失败: {e}")
            return None
    
    def _capture_with_pyautogui(self) -> Optional[np.ndarray]:
        """使用pyautogui截图"""
        screenshot = pyautogui.screenshot()
        # PIL Image转换为numpy数组
        screenshot_np = np.array(screenshot)
        # RGB转BGR (OpenCV格式)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        return screenshot_bgr
    
    def _capture_with_pil(self) -> Optional[np.ndarray]:
        """使用PIL截图"""
        screenshot = ImageGrab.grab()
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        return screenshot_bgr
    
    def _capture_with_screencapture(self) -> Optional[np.ndarray]:
        """使用macOS screencapture命令截图"""
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 使用screencapture命令
            subprocess.run(['screencapture', '-x', temp_path], check=True)
            
            # 读取图片
            screenshot = cv2.imread(temp_path)
            return screenshot
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _capture_with_win32(self) -> Optional[np.ndarray]:
        """使用Windows API截图"""
        try:
            import win32gui
            import win32ui
            import win32con
            
            # 获取桌面窗口
            hdesktop = win32gui.GetDesktopWindow()
            
            # 获取屏幕尺寸
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            
            # 创建设备上下文
            desktop_dc = win32gui.GetWindowDC(hdesktop)
            img_dc = win32ui.CreateDCFromHandle(desktop_dc)
            mem_dc = img_dc.CreateCompatibleDC()
            
            # 创建位图
            screenshot = win32ui.CreateBitmap()
            screenshot.CreateCompatibleBitmap(img_dc, width, height)
            mem_dc.SelectObject(screenshot)
            
            # 复制屏幕内容
            mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)
            
            # 获取位图数据
            bmpinfo = screenshot.GetInfo()
            bmpstr = screenshot.GetBitmapBits(True)
            
            # 转换为numpy数组
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)
            
            # 删除alpha通道并转换为BGR
            img = img[:, :, :3]
            img = np.flip(img, axis=2)  # RGB to BGR
            
            # 清理资源
            mem_dc.DeleteDC()
            win32gui.DeleteObject(screenshot.GetHandle())
            win32gui.ReleaseDC(hdesktop, desktop_dc)
            
            return img
            
        except Exception as e:
            print(f"Win32截图失败: {e}")
            return None
    
    def _capture_region_with_pyautogui(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """使用pyautogui截取区域"""
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        return screenshot_bgr
    
    def _capture_region_with_pil(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """使用PIL截取区域"""
        bbox = (x, y, x + width, y + height)
        screenshot = ImageGrab.grab(bbox)
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
        return screenshot_bgr
    
    def save_screenshot(self, image: np.ndarray, filepath: str) -> bool:
        """
        保存截图到文件
        
        Args:
            image: 图像数据
            filepath: 保存路径
        
        Returns:
            是否保存成功
        """
        try:
            return cv2.imwrite(filepath, image)
        except Exception as e:
            print(f"保存截图失败: {e}")
            return False
    
    def get_available_methods(self) -> List[str]:
        """获取可用的截图方法"""
        return self.available_methods.copy()
    
    def is_method_available(self, method: str) -> bool:
        """检查指定方法是否可用"""
        return method in self.available_methods

# 测试代码
if __name__ == "__main__":
    manager = ScreenshotManager()
    print(f"可用截图方法: {manager.get_available_methods()}")
    print(f"屏幕尺寸: {manager.get_screen_size()}")
    
    # 测试全屏截图
    screenshot = manager.capture_fullscreen()
    if screenshot is not None:
        print(f"截图成功，尺寸: {screenshot.shape}")
        # 保存测试截图
        if manager.save_screenshot(screenshot, "test_screenshot.png"):
            print("测试截图已保存为 test_screenshot.png")
    else:
        print("截图失败")
