import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import cv2
from PIL import Image, ImageTk
import numpy as np
from camera_manager import CameraManager
from ocr_processor import OCRProcessor
from storage_manager import StorageManager
from config_manager import ConfigManager
from http_server import HTTPServer
from screenshot_manager import ScreenshotManager

class MonitorOCRApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("监控OCR系统")
        self.root.geometry("800x600")
        
        # 初始化组件
        self.config_manager = ConfigManager()
        self.camera_manager = CameraManager()
        self.storage_manager = StorageManager(
            self.config_manager.get('storage.screenshot_dir', './screenshots')
        )
        self.ocr_processor = OCRProcessor(self.config_manager.get_ocr_config())
        self.screenshot_manager = ScreenshotManager()
        self.http_server = HTTPServer(
            self.camera_manager, 
            self.ocr_processor, 
            self.storage_manager, 
            self.config_manager
        )
        
        # GUI状态
        self.current_screen = "main"
        self.video_label = None
        self.is_preview_running = False
        
        # 截图区域设置
        self.screenshot_region = None  # None表示全屏，否则为{'x': x, 'y': y, 'width': w, 'height': h}
        
        # 创建主界面
        self.create_main_screen()
        
        # 启动视频预览更新
        self.update_video_preview()
    
    def create_main_screen(self):
        """创建主界面"""
        self.clear_screen()
        self.current_screen = "main"
        
        # 标题
        title_label = tk.Label(self.root, text="监控OCR系统", font=("Arial", 20, "bold"))
        title_label.pack(pady=20)
        
        # 状态信息框架
        status_frame = ttk.LabelFrame(self.root, text="系统状态", padding=10)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        # 摄像头状态
        self.camera_status_label = tk.Label(status_frame, text="摄像头: 未连接", font=("Arial", 12))
        self.camera_status_label.pack(anchor="w")
        
        # HTTP服务状态
        self.http_status_label = tk.Label(status_frame, text="HTTP服务: 未启动", font=("Arial", 12))
        self.http_status_label.pack(anchor="w")
        
        # 当前配置
        config_text = f"端口: {self.config_manager.get('http.port', 8080)}"
        self.config_label = tk.Label(status_frame, text=config_text, font=("Arial", 12))
        self.config_label.pack(anchor="w")
        
        # 视频预览框架
        video_frame = ttk.LabelFrame(self.root, text="视频预览", padding=10)
        video_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.video_label = tk.Label(video_frame, text="无视频信号", bg="black", fg="white")
        self.video_label.pack(fill="both", expand=True)
        
        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        # 按钮
        ttk.Button(button_frame, text="选择摄像头", command=self.show_camera_screen).pack(side="left", padx=5)
        ttk.Button(button_frame, text="设置", command=self.show_settings_screen).pack(side="left", padx=5)
        
        # 截图相关按钮
        ttk.Button(button_frame, text="屏幕截图OCR", command=self.screenshot_ocr).pack(side="left", padx=5)
        ttk.Button(button_frame, text="截图设置", command=self.show_screenshot_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text="摄像头OCR", command=self.camera_ocr).pack(side="left", padx=5)
        
        self.http_button = ttk.Button(button_frame, text="启动HTTP服务", command=self.toggle_http_server)
        self.http_button.pack(side="right", padx=5)
        
        # 更新状态
        self.update_status()
    
    def create_camera_screen(self):
        """创建摄像头选择界面"""
        self.clear_screen()
        self.current_screen = "camera"
        
        # 标题
        title_label = tk.Label(self.root, text="摄像头选择", font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # 摄像头列表框架
        list_frame = ttk.LabelFrame(self.root, text="可用摄像头", padding=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 摄像头列表
        self.camera_listbox = tk.Listbox(list_frame, font=("Arial", 12))
        self.camera_listbox.pack(fill="both", expand=True)
        
        # 刷新摄像头列表
        self.refresh_camera_list()
        
        # 按钮框架
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(button_frame, text="刷新", command=self.refresh_camera_list).pack(side="left", padx=5)
        ttk.Button(button_frame, text="选择", command=self.select_camera).pack(side="left", padx=5)
        ttk.Button(button_frame, text="返回", command=self.create_main_screen).pack(side="right", padx=5)
    
    def create_settings_screen(self):
        """创建设置界面"""
        self.clear_screen()
        self.current_screen = "settings"
        
        # 标题
        title_label = tk.Label(self.root, text="系统设置", font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # 创建滚动框架
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # HTTP设置
        http_frame = ttk.LabelFrame(scrollable_frame, text="HTTP服务设置", padding=10)
        http_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(http_frame, text="端口:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.port_var = tk.StringVar(value=str(self.config_manager.get('http.port', 8080)))
        tk.Entry(http_frame, textvariable=self.port_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        # 存储设置
        storage_frame = ttk.LabelFrame(scrollable_frame, text="存储设置", padding=10)
        storage_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(storage_frame, text="截图目录:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.storage_dir_var = tk.StringVar(value=self.config_manager.get('storage.screenshot_dir', './screenshots'))
        tk.Entry(storage_frame, textvariable=self.storage_dir_var, width=40).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(storage_frame, text="浏览", command=self.browse_storage_dir).grid(row=0, column=2, padx=5, pady=2)
        
        # 字段映射设置
        mapping_frame = ttk.LabelFrame(scrollable_frame, text="字段映射设置", padding=10)
        mapping_frame.pack(fill="x", padx=20, pady=5)
        
        # 映射列表
        self.mapping_tree = ttk.Treeview(mapping_frame, columns=("field", "key"), show="headings", height=6)
        self.mapping_tree.heading("field", text="字段名")
        self.mapping_tree.heading("key", text="映射键")
        self.mapping_tree.column("field", width=150)
        self.mapping_tree.column("key", width=150)
        self.mapping_tree.pack(fill="x", pady=5)
        
        # 映射操作按钮
        mapping_btn_frame = tk.Frame(mapping_frame)
        mapping_btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(mapping_btn_frame, text="添加", command=self.add_mapping).pack(side="left", padx=5)
        ttk.Button(mapping_btn_frame, text="删除", command=self.delete_mapping).pack(side="left", padx=5)
        
        # 加载映射数据
        self.load_mappings()
        
        # 按钮框架
        button_frame = tk.Frame(scrollable_frame)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        ttk.Button(button_frame, text="保存设置", command=self.save_settings).pack(side="left", padx=5)
        ttk.Button(button_frame, text="返回", command=self.create_main_screen).pack(side="right", padx=5)
        
        # 打包滚动组件
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def clear_screen(self):
        """清空屏幕"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def refresh_camera_list(self):
        """刷新摄像头列表"""
        if hasattr(self, 'camera_listbox'):
            self.camera_listbox.delete(0, tk.END)
            cameras = self.camera_manager.get_available_cameras()
            for i, camera_index in enumerate(cameras):
                info = self.camera_manager.get_camera_info(camera_index)
                text = f"摄像头 {camera_index}: {info.get('width', 'N/A')}x{info.get('height', 'N/A')}"
                self.camera_listbox.insert(tk.END, text)
    
    def select_camera(self):
        """选择摄像头"""
        selection = self.camera_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择一个摄像头")
            return
        
        cameras = self.camera_manager.get_available_cameras()
        selected_index = cameras[selection[0]]
        
        # 启动摄像头
        if self.camera_manager.start_camera(selected_index):
            self.config_manager.set('camera.selected_index', selected_index)
            messagebox.showinfo("成功", f"摄像头 {selected_index} 已启动")
            self.create_main_screen()
        else:
            messagebox.showerror("错误", "启动摄像头失败")
    
    def load_mappings(self):
        """加载字段映射"""
        if hasattr(self, 'mapping_tree'):
            for item in self.mapping_tree.get_children():
                self.mapping_tree.delete(item)
            
            mappings = self.config_manager.get_field_mappings()
            for field, key in mappings.items():
                self.mapping_tree.insert("", "end", values=(field, key))
    
    def add_mapping(self):
        """添加字段映射"""
        dialog = MappingDialog(self.root)
        if dialog.result:
            field, key = dialog.result
            mappings = self.config_manager.get_field_mappings()
            mappings[field] = key
            self.config_manager.set_field_mappings(mappings)
            self.load_mappings()
    
    def delete_mapping(self):
        """删除字段映射"""
        selection = self.mapping_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的映射")
            return
        
        item = self.mapping_tree.item(selection[0])
        field = item['values'][0]
        
        mappings = self.config_manager.get_field_mappings()
        if field in mappings:
            del mappings[field]
            self.config_manager.set_field_mappings(mappings)
            self.load_mappings()
    
    def browse_storage_dir(self):
        """浏览存储目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.storage_dir_var.set(directory)
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存HTTP设置
            port = int(self.port_var.get())
            self.config_manager.set('http.port', port)
            
            # 保存存储设置
            storage_dir = self.storage_dir_var.get()
            self.config_manager.set('storage.screenshot_dir', storage_dir)
            
            messagebox.showinfo("成功", "设置已保存")
            
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
    
    def toggle_http_server(self):
        """切换HTTP服务状态"""
        if self.http_server.is_running:
            self.http_server.stop_server()
            self.http_button.config(text="启动HTTP服务")
        else:
            config = self.config_manager.get_http_config()
            if self.http_server.start_server(
                host=config.get('host', '0.0.0.0'),
                port=config.get('port', 8080),
                debug=config.get('debug', False)
            ):
                self.http_button.config(text="停止HTTP服务")
            else:
                messagebox.showerror("错误", "启动HTTP服务失败")
        
        self.update_status()
    
    def update_status(self):
        """更新状态显示"""
        if hasattr(self, 'camera_status_label'):
            if self.camera_manager.is_camera_running():
                self.camera_status_label.config(
                    text=f"摄像头: 运行中 (索引: {self.camera_manager.camera_index})",
                    fg="green"
                )
            else:
                self.camera_status_label.config(text="摄像头: 未连接", fg="red")
        
        if hasattr(self, 'http_status_label'):
            if self.http_server.is_running:
                port = self.config_manager.get('http.port', 8080)
                self.http_status_label.config(
                    text=f"HTTP服务: 运行中 (端口: {port})",
                    fg="green"
                )
            else:
                self.http_status_label.config(text="HTTP服务: 未启动", fg="red")
    
    def update_video_preview(self):
        """更新视频预览"""
        if self.current_screen == "main" and hasattr(self, 'video_label'):
            frame = self.camera_manager.get_current_frame()
            if frame is not None:
                # 调整图像大小以适应显示
                height, width = frame.shape[:2]
                max_width, max_height = 400, 300
                
                if width > max_width or height > max_height:
                    scale = min(max_width/width, max_height/height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # 转换为PIL图像
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                
                # 更新显示
                self.video_label.config(image=photo, text="")
                self.video_label.image = photo
            else:
                self.video_label.config(image="", text="无视频信号")
        
        # 定期更新
        self.root.after(100, self.update_video_preview)
    
    def show_camera_screen(self):
        """显示摄像头选择界面"""
        self.create_camera_screen()
    
    def show_settings_screen(self):
        """显示设置界面"""
        self.create_settings_screen()
    
    def run(self):
        """运行应用"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """关闭应用"""
        self.camera_manager.stop_camera()
        self.http_server.stop_server()
        self.root.destroy()
    
    def screenshot_ocr(self):
        """执行屏幕截图OCR"""
        try:
            # 显示处理中提示
            region_text = "区域截图" if self.screenshot_region else "全屏截图"
            self.show_processing_message(f"正在进行{region_text}OCR...")
            
            # 在后台线程中执行截图OCR
            def do_screenshot_ocr():
                try:
                    # 根据设置选择截图方式
                    if self.screenshot_region:
                        # 区域截图
                        screenshot = self.screenshot_manager.capture_region(
                            self.screenshot_region['x'],
                            self.screenshot_region['y'],
                            self.screenshot_region['width'],
                            self.screenshot_region['height']
                        )
                    else:
                        # 全屏截图
                        screenshot = self.screenshot_manager.capture_fullscreen()
                    
                    if screenshot is None:
                        self.root.after(0, lambda: messagebox.showerror("错误", "屏幕截图失败"))
                        return
                    
                    # 保存截图
                    screenshot_path = self.storage_manager.save_screenshot(screenshot, "screen_ocr")
                    
                    # OCR识别
                    ocr_results = self.ocr_processor.process_image(screenshot)
                    
                    # 在主线程中显示结果
                    title = f"{region_text}OCR结果"
                    self.root.after(0, lambda: self.show_ocr_results(title, ocr_results, screenshot_path))
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("错误", f"屏幕截图OCR失败: {str(e)}"))
                finally:
                    self.root.after(0, self.hide_processing_message)
            
            # 在后台线程中执行
            threading.Thread(target=do_screenshot_ocr, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动屏幕截图OCR失败: {str(e)}")
    
    def camera_ocr(self):
        """执行摄像头OCR"""
        try:
            if not self.camera_manager.is_camera_running():
                messagebox.showwarning("警告", "请先启动摄像头")
                return
            
            # 显示处理中提示
            self.show_processing_message("正在进行摄像头OCR...")
            
            # 在后台线程中执行摄像头OCR
            def do_camera_ocr():
                try:
                    # 获取当前视频帧
                    frame = self.camera_manager.capture_screenshot()
                    
                    if frame is None:
                        self.root.after(0, lambda: messagebox.showerror("错误", "无法获取摄像头画面"))
                        return
                    
                    # 保存截图
                    screenshot_path = self.storage_manager.save_screenshot(frame, "camera_ocr")
                    
                    # OCR识别
                    ocr_results = self.ocr_processor.process_image(frame)
                    
                    # 在主线程中显示结果
                    self.root.after(0, lambda: self.show_ocr_results("摄像头OCR结果", ocr_results, screenshot_path))
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("错误", f"摄像头OCR失败: {str(e)}"))
                finally:
                    self.root.after(0, self.hide_processing_message)
            
            # 在后台线程中执行
            threading.Thread(target=do_camera_ocr, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动摄像头OCR失败: {str(e)}")
    
    def show_processing_message(self, message):
        """显示处理中消息"""
        if hasattr(self, 'processing_label'):
            self.processing_label.destroy()
        
        self.processing_label = tk.Label(
            self.root, 
            text=message, 
            font=("Arial", 12), 
            fg="blue",
            bg="lightyellow"
        )
        self.processing_label.pack(pady=5)
        self.root.update()
    
    def hide_processing_message(self):
        """隐藏处理中消息"""
        if hasattr(self, 'processing_label'):
            self.processing_label.destroy()
    
    def show_ocr_results(self, title, results, screenshot_path):
        """显示OCR结果"""
        # 创建结果窗口
        result_window = tk.Toplevel(self.root)
        result_window.title(title)
        result_window.geometry("600x400")
        
        # 标题
        title_label = tk.Label(result_window, text=title, font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 截图路径
        path_label = tk.Label(result_window, text=f"截图保存路径: {screenshot_path}", font=("Arial", 10))
        path_label.pack(pady=5)
        
        # 结果框架
        result_frame = ttk.LabelFrame(result_window, text="识别结果", padding=10)
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 结果文本框
        result_text = tk.Text(result_frame, wrap=tk.WORD, font=("Arial", 11))
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=result_text.yview)
        result_text.configure(yscrollcommand=scrollbar.set)
        
        result_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 显示结果
        if results:
            result_text.insert(tk.END, "识别到的字段值:\n\n")
            for key, value in results.items():
                result_text.insert(tk.END, f"{key}: {value}\n")
        else:
            result_text.insert(tk.END, "未识别到任何字段值")
        
        result_text.config(state=tk.DISABLED)
        
        # 按钮框架
        button_frame = tk.Frame(result_window)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        # 打开截图文件按钮
        def open_screenshot():
            try:
                import os
                import platform
                if platform.system() == "Darwin":  # macOS
                    os.system(f"open '{screenshot_path}'")
                elif platform.system() == "Windows":
                    os.system(f"start '{screenshot_path}'")
                else:  # Linux
                    os.system(f"xdg-open '{screenshot_path}'")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开截图文件: {str(e)}")
        
        ttk.Button(button_frame, text="打开截图", command=open_screenshot).pack(side="left", padx=5)
        ttk.Button(button_frame, text="关闭", command=result_window.destroy).pack(side="right", padx=5)
        
        # 居中显示
        result_window.update_idletasks()
        x = (result_window.winfo_screenwidth() // 2) - (result_window.winfo_width() // 2)
        y = (result_window.winfo_screenheight() // 2) - (result_window.winfo_height() // 2)
        result_window.geometry(f"+{x}+{y}")
    
    def show_screenshot_settings(self):
        """显示截图设置界面"""
        # 创建简单的选择对话框
        settings_window = tk.Toplevel(self.root)
        settings_window.title("截图区域设置")
        settings_window.geometry("350x200")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 标题
        title_label = tk.Label(settings_window, text="选择截图模式", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # 当前设置显示
        if self.screenshot_region:
            current_text = f"当前: 区域截图 ({self.screenshot_region['x']}, {self.screenshot_region['y']}) " \
                          f"{self.screenshot_region['width']} x {self.screenshot_region['height']}"
        else:
            current_text = "当前: 全屏截图"
        
        current_label = tk.Label(settings_window, text=current_text, font=("Arial", 10))
        current_label.pack(pady=10)
        
        # 按钮框架
        button_frame = tk.Frame(settings_window)
        button_frame.pack(pady=20)
        
        def set_fullscreen():
            """设置全屏截图"""
            self.screenshot_region = None
            messagebox.showinfo("成功", "已设置为全屏截图")
            settings_window.destroy()
        
        def select_region():
            """选择区域截图"""
            settings_window.destroy()
            self.show_region_selector()
        
        ttk.Button(button_frame, text="全屏截图", command=set_fullscreen).pack(side="left", padx=10)
        ttk.Button(button_frame, text="选择区域", command=select_region).pack(side="left", padx=10)
        ttk.Button(button_frame, text="取消", command=settings_window.destroy).pack(side="left", padx=10)
        
        # 居中显示
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (settings_window.winfo_width() // 2)
        y = (settings_window.winfo_screenheight() // 2) - (settings_window.winfo_height() // 2)
        settings_window.geometry(f"+{x}+{y}")
    
    def show_region_selector(self):
        """显示可视化区域选择器"""
        # 创建全屏透明窗口
        selector = tk.Toplevel(self.root)
        selector.title("选择截图区域")
        
        # 设置为全屏
        screen_width = selector.winfo_screenwidth()
        screen_height = selector.winfo_screenheight()
        selector.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # 设置窗口属性
        selector.configure(bg='black')
        selector.attributes('-alpha', 0.3)  # 半透明
        selector.attributes('-topmost', True)  # 置顶
        selector.overrideredirect(True)  # 无边框
        
        # 创建画布
        canvas = tk.Canvas(selector, width=screen_width, height=screen_height, 
                          bg='black', highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        # 选择区域的变量
        start_x = start_y = 0
        current_rect = None
        
        # 提示文本
        info_text = canvas.create_text(screen_width//2, 50, 
                                     text="拖拽鼠标选择截图区域，按ESC取消", 
                                     fill="white", font=("Arial", 16))
        
        def on_mouse_press(event):
            nonlocal start_x, start_y, current_rect
            start_x, start_y = event.x, event.y
            if current_rect:
                canvas.delete(current_rect)
            current_rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, 
                                                 outline="red", width=2, fill="white", stipple="gray25")
        
        def on_mouse_drag(event):
            nonlocal current_rect
            if current_rect:
                canvas.coords(current_rect, start_x, start_y, event.x, event.y)
                # 显示当前尺寸
                width = abs(event.x - start_x)
                height = abs(event.y - start_y)
                canvas.itemconfig(info_text, 
                                text=f"区域: {min(start_x, event.x)}, {min(start_y, event.y)} | 尺寸: {width} x {height}")
        
        def on_mouse_release(event):
            nonlocal current_rect
            if current_rect:
                # 计算最终区域
                x1, y1 = min(start_x, event.x), min(start_y, event.y)
                x2, y2 = max(start_x, event.x), max(start_y, event.y)
                width, height = x2 - x1, y2 - y1
                
                if width > 10 and height > 10:  # 最小尺寸检查
                    # 保存区域设置
                    self.screenshot_region = {
                        'x': x1,
                        'y': y1,
                        'width': width,
                        'height': height
                    }
                    
                    selector.destroy()
                    messagebox.showinfo("成功", f"已设置区域截图: ({x1}, {y1}) {width} x {height}")
                else:
                    canvas.itemconfig(info_text, text="区域太小，请重新选择")
        
        def on_key_press(event):
            if event.keysym == 'Escape':
                selector.destroy()
            elif event.keysym == 'Return':
                # 回车确认当前选择
                if current_rect:
                    coords = canvas.coords(current_rect)
                    if len(coords) == 4:
                        x1, y1, x2, y2 = coords
                        x1, y1 = min(x1, x2), min(y1, y2)
                        width, height = abs(x2 - x1), abs(y2 - y1)
                        
                        if width > 10 and height > 10:
                            self.screenshot_region = {
                                'x': int(x1),
                                'y': int(y1),
                                'width': int(width),
                                'height': int(height)
                            }
                            selector.destroy()
                            messagebox.showinfo("成功", f"已设置区域截图: ({int(x1)}, {int(y1)}) {int(width)} x {int(height)}")
        
        # 绑定事件
        canvas.bind("<Button-1>", on_mouse_press)
        canvas.bind("<B1-Motion>", on_mouse_drag)
        canvas.bind("<ButtonRelease-1>", on_mouse_release)
        
        # 绑定键盘事件
        selector.bind("<Key>", on_key_press)
        selector.focus_set()
        
        # 添加更多提示
        canvas.create_text(screen_width//2, screen_height - 50, 
                         text="按 ESC 取消 | 按 Enter 确认选择", 
                         fill="white", font=("Arial", 12))


class MappingDialog:
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("添加字段映射")
        self.dialog.geometry("300x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 字段名
        tk.Label(self.dialog, text="字段名:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.field_var = tk.StringVar()
        tk.Entry(self.dialog, textvariable=self.field_var, width=20).grid(row=0, column=1, padx=10, pady=10)
        
        # 映射键
        tk.Label(self.dialog, text="映射键:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.key_var = tk.StringVar()
        tk.Entry(self.dialog, textvariable=self.key_var, width=20).grid(row=1, column=1, padx=10, pady=10)
        
        # 按钮
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok_clicked).pack(side="left", padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel_clicked).pack(side="left", padx=5)
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def ok_clicked(self):
        field = self.field_var.get().strip()
        key = self.key_var.get().strip()
        
        if not field or not key:
            messagebox.showwarning("警告", "请填写完整信息")
            return
        
        self.result = (field, key)
        self.dialog.destroy()
    
    def cancel_clicked(self):
        self.dialog.destroy()


if __name__ == "__main__":
    app = MonitorOCRApp()
    app.run()
