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
