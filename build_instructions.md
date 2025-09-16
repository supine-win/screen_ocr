# Windows平台打包指南

## 方法1: 在Windows环境中直接打包 (推荐)

### 环境要求
- Windows 10/11 x64
- Python 3.9+ 
- Git

### 打包步骤

1. **准备环境**
```bash
# 克隆项目到Windows机器
git clone <your-repo-url>
cd monitor_ocr

# 安装Python依赖
pip install -r requirements.txt
```

2. **预下载模型**
```bash
python prepare_models.py
```

3. **执行打包**
```bash
python build_windows.py
```

4. **获取结果**
打包完成后，在 `release/` 目录下会生成：
- `MonitorOCR.exe` - Windows可执行文件
- `config.json` - 配置文件
- `README.md` - 说明文档
- `start.bat` - 启动脚本

## 方法2: 使用GitHub Actions (自动化)

1. **推送代码到GitHub**
```bash
git add .
git commit -m "Add Windows build workflow"
git push origin main
```

2. **触发构建**
- 访问GitHub仓库的Actions页面
- 手动触发"Build Windows Executable"工作流
- 等待构建完成后下载artifacts

## 方法3: 使用虚拟机

### VMware/VirtualBox方案
1. 在macOS上安装VMware Fusion或VirtualBox
2. 创建Windows 10/11虚拟机
3. 在虚拟机中按方法1执行打包

### Parallels Desktop方案 (macOS)
1. 安装Parallels Desktop
2. 创建Windows虚拟机
3. 在Windows环境中执行打包

## 方法4: 云服务器

### 使用AWS/Azure/阿里云
1. 创建Windows Server实例
2. 远程桌面连接
3. 安装开发环境并执行打包

## 打包脚本说明

当前的 `build_windows.py` 脚本已经支持跨平台：

- **macOS**: 生成 `.app` 包
- **Windows**: 生成 `.exe` 文件
- **自动检测**: 根据运行平台选择正确的打包方式

## 注意事项

1. **模型文件**: 确保运行 `prepare_models.py` 下载所有OCR模型
2. **依赖包**: Windows环境需要安装所有Python依赖
3. **文件大小**: 最终exe文件约400MB+（包含模型）
4. **兼容性**: 生成的exe支持Windows 10/11 x64

## 故障排除

### 常见问题
- **缺少模型**: 运行 `prepare_models.py`
- **依赖错误**: 检查 `requirements.txt` 安装
- **打包失败**: 查看PyInstaller错误日志

### 性能优化
- 使用 `--onedir` 模式可减少启动时间
- 排除不必要的模块可减小文件大小
