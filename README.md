# 监控OCR系统

一个基于Python的后台服务程序，支持摄像头视频流捕获、OCR文字识别、HTTP API服务等功能。

## 功能特性

### 核心功能
1. **摄像头管理**: 自动检测可用摄像头，支持视频流捕获
2. **屏幕截图**: 支持全屏截图和区域截图，多种截图方法自动选择
3. **OCR识别**: 使用PaddleOCR进行中文文字识别，支持字段映射配置
4. **HTTP服务**: 提供健康检查、摄像头OCR和屏幕截图OCR等API接口
5. **截图存储**: 按年/月/日文件夹自动存储截图
6. **配置管理**: JSON格式配置文件，支持实时更新

### HTTP API接口

#### 健康检查
```
GET /health
```
返回系统状态信息

#### OCR识别

**摄像头OCR识别**
```
POST /ocr
```
捕获当前视频帧并进行OCR识别，返回字段映射结果

**屏幕截图OCR识别**
```
POST /screenshot/ocr
```
请求体参数：
- `region` (可选): 截图区域 `{"x": 0, "y": 0, "width": 1920, "height": 1080}`
- `method` (可选): 截图方法 `"auto"`, `"pyautogui"`, `"pil"`, `"screencapture"`, `"win32"`

**纯屏幕截图**
```
POST /screenshot/capture
```
请求体参数：
- `region` (可选): 截图区域
- `method` (可选): 截图方法
- `save` (可选): 是否保存文件，默认true

**屏幕截图信息**
```
GET /screenshot/info
```
返回屏幕尺寸、可用截图方法等信息

#### 字段映射管理
```
GET /config/mappings     # 获取字段映射
POST /config/mappings    # 更新字段映射
```

#### 系统状态
```
GET /camera/status       # 摄像头状态
GET /storage/stats       # 存储统计
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### GUI模式（推荐）
```bash
python main.py
```

GUI界面提供以下功能：
- **摄像头管理**: 选择和配置摄像头设备
- **实时视频预览**: 显示摄像头视频流
- **屏幕截图OCR**: 点击按钮进行全屏截图并OCR识别
- **摄像头OCR**: 对当前摄像头画面进行OCR识别
- **系统设置**: 配置OCR参数和字段映射
- **HTTP服务控制**: 启动/停止HTTP API服务

### 无GUI模式（服务器部署）
```bash
python main.py --no-gui
```

### 自定义配置文件
```bash
python main.py --config custom_config.json
```

## 配置说明

配置文件 `config.json` 包含以下设置：

```json
{
  "camera": {
    "selected_index": 0,        // 摄像头索引
    "resolution": [1920, 1080], // 分辨率
    "fps": 30                   // 帧率
  },
  "ocr": {
    "field_mappings": {         // 字段映射
      "温度": "temperature",
      "湿度": "humidity",
      "压力": "pressure",
      "流量": "flow_rate"
    },
    "language": "ch",           // OCR语言
    "use_angle_cls": true,      // 文字方向分类
    "use_space_char": true      // 空格字符识别
  },
  "storage": {
    "screenshot_dir": "./screenshots", // 截图存储目录
    "auto_cleanup_days": 30            // 自动清理天数
  },
  "http": {
    "host": "0.0.0.0",         // 服务地址
    "port": 9501,              // 服务端口
    "debug": false             // 调试模式
  }
}
```

## GUI界面

### 1. 主界面
- 显示系统状态（摄像头、HTTP服务）
- 实时视频预览
- 启动/停止HTTP服务
- 导航到其他界面

### 2. 摄像头选择界面
- 自动检测可用摄像头
- 显示摄像头信息（分辨率等）
- 选择并启动摄像头

### 3. 设置界面
- HTTP服务配置（端口等）
- 存储目录设置
- 字段映射管理（添加/删除映射关系）

## 项目结构

```
monitor_ocr/
├── main.py              # 主程序入口
├── gui_app.py           # GUI应用界面
├── camera_manager.py    # 摄像头管理
├── ocr_processor.py     # OCR处理器
├── storage_manager.py   # 存储管理
├── config_manager.py    # 配置管理
├── http_server.py       # HTTP服务器
├── config.json          # 配置文件
├── requirements.txt     # 依赖包列表
└── README.md           # 说明文档
```

## 开发环境

- Python 3.8+
- OpenCV 4.8+
- PaddleOCR 2.7+
- Flask 2.3+
- Tkinter (GUI)

## 部署说明

### Windows打包

#### 方法1: 在Windows环境中直接打包 (推荐)
```bash
# 1. 预下载PaddleOCR模型
python prepare_models.py

# 2. 执行打包脚本
python build_windows.py
```

#### 方法2: 使用GitHub Actions自动化打包
```bash
# 推送代码到GitHub，自动触发Windows构建
git push origin main
# 在GitHub Actions页面下载生成的Windows可执行文件
```

#### 方法3: 使用Docker交叉编译
```bash
python build_windows_docker.py
```

**打包输出:**
- `MonitorOCR.exe` (约400MB，包含所有OCR模型)
- `config.json` - 配置文件
- `start.bat` - Windows启动脚本
- `README.md` - 使用说明

### Docker部署
项目支持Docker容器化部署，适用于Linux环境和交叉编译。

```bash
# 标准部署
docker-compose up -d

# Windows交叉编译
docker build -f Dockerfile.windows -t monitor-ocr-windows .
```

## 模型管理

### 预下载模型
```bash
python prepare_models.py
```

### 模型文件信息
- **PP-OCRv5_server_det** (83.9MB) - 文字检测模型
- **PP-OCRv5_server_rec** (80.5MB) - 文字识别模型  
- **PP-LCNet_x1_0_textline_ori** (6.4MB) - 文字方向分类
- **UVDoc** (30.6MB) - 文档处理模型
- **PP-LCNet_x1_0_doc_ori** (6.4MB) - 文档方向分类
- **总大小**: 209.4MB

### 离线部署
打包后的可执行文件包含所有模型，支持完全离线运行，无需联网下载。

## 项目文件结构

```
monitor_ocr/
├── main.py                    # 主程序入口
├── gui_app.py                 # GUI应用界面
├── camera_manager.py          # 摄像头管理
├── screenshot_manager.py      # 屏幕截图管理
├── ocr_processor.py           # OCR处理器
├── storage_manager.py         # 存储管理
├── config_manager.py          # 配置管理
├── http_server.py             # HTTP服务器
├── model_manager.py           # 模型管理器
├── prepare_models.py          # 模型预下载脚本
├── build_windows.py           # Windows打包脚本
├── build_windows_docker.py    # Docker交叉编译脚本
├── test_api.py                # API测试脚本
├── config.json                # 配置文件
├── requirements.txt           # 依赖包列表
├── Dockerfile                 # Docker配置
├── Dockerfile.windows         # Windows Docker配置
├── docker-compose.yml         # Docker Compose配置
├── .github/workflows/         # GitHub Actions工作流
├── build_instructions.md      # 详细打包指南
└── README.md                  # 项目说明
```

## 屏幕截图功能详解

### 支持的截图方法
系统会自动检测并选择最佳的截图方法：

1. **PyAutoGUI** - 跨平台截图库，支持全屏和区域截图
2. **PIL ImageGrab** - Python Imaging Library的截图功能
3. **macOS screencapture** - macOS系统原生截图命令
4. **Windows API** - Windows系统原生截图接口

### 截图功能特性
- **自动方法选择**: 根据系统环境自动选择最佳截图方法
- **全屏截图**: 捕获整个屏幕内容
- **区域截图**: 指定坐标和尺寸截取特定区域
- **多显示器支持**: 支持多显示器环境的截图
- **高质量输出**: 保持原始分辨率和色彩

### 使用示例

**GUI界面使用**
1. 点击"屏幕截图OCR"按钮
2. 系统自动截取全屏并进行OCR识别
3. 在弹出窗口中查看识别结果

**API调用示例**
```bash
# 全屏截图OCR
curl -X POST http://localhost:9501/screenshot/ocr \
  -H "Content-Type: application/json" \
  -d "{}"

# 区域截图OCR
curl -X POST http://localhost:9501/screenshot/ocr \
  -H "Content-Type: application/json" \
  -d '{"region": {"x": 100, "y": 100, "width": 800, "height": 600}}'

# 获取屏幕信息
curl http://localhost:9501/screenshot/info
```

## 注意事项

1. **模型下载**: 首次运行或打包前需执行 `prepare_models.py`
2. **摄像头权限**: 确保摄像头权限已开启
3. **屏幕录制权限**: macOS需要授予屏幕录制权限才能截图
4. **网络安全**: HTTP服务默认监听所有网络接口，注意安全设置
5. **存储管理**: 截图文件按年/月/日自动分类存储
6. **自动清理**: 支持自动清理过期截图文件
7. **跨平台**: 支持macOS开发，Windows部署
8. **离线运行**: 打包后完全离线，无需Python环境

## 故障排除

### 摄像头无法启动
- 检查摄像头是否被其他程序占用
- 确认摄像头驱动正常
- 尝试不同的摄像头索引

### OCR识别不准确
- 调整摄像头焦距和光线
- 检查字段映射配置是否正确
- 确保文字清晰可见
- 验证PaddleOCR模型是否正确加载

### 屏幕截图失败
- 检查屏幕录制权限（macOS系统偏好设置 > 安全性与隐私 > 屏幕录制）
- 确认pyautogui库已正确安装
- 尝试不同的截图方法参数
- 检查是否有其他程序阻止截图

### HTTP服务启动失败
- 检查端口是否被占用
- 确认防火墙设置
- 查看错误日志信息

### 打包相关问题
- **模型缺失**: 确保运行 `prepare_models.py` 下载所有模型
- **依赖错误**: 检查 `requirements.txt` 中的包是否正确安装
- **平台兼容**: Windows打包需要在Windows环境或使用交叉编译
- **文件大小**: 最终可执行文件约400MB（包含所有OCR模型）

### 性能优化建议
- 使用SSD存储提升截图保存速度
- 调整摄像头分辨率平衡质量和性能
- 定期清理过期截图文件
- 在生产环境中使用专业WSGI服务器替代Flask开发服务器

## 更新日志

### v1.1.0 (最新)
- ✅ 新增屏幕截图OCR功能
- ✅ 支持多种截图方法自动选择
- ✅ GUI界面新增屏幕截图按钮
- ✅ HTTP API新增屏幕截图相关接口
- ✅ 支持全屏和区域截图
- ✅ 跨平台截图兼容性优化

### v1.0.0
- ✅ 完整的摄像头管理系统
- ✅ PaddleOCR中文识别支持
- ✅ 可配置字段映射系统
- ✅ HTTP API服务
- ✅ GUI三界面管理
- ✅ 按日期分类的截图存储
- ✅ 跨平台打包支持
- ✅ 离线模型打包
- ✅ Docker容器化部署
- ✅ GitHub Actions自动化构建

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至项目维护者
