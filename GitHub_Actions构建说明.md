# GitHub Actions 自动构建Windows可执行文件

## 概述

这个配置将自动在GitHub Actions中构建包含EasyOCR模型的Windows exe文件，完全离线运行，无需用户下载模型。

## 构建流程

### 1. **触发条件**
- 推送到 `main` 分支
- 创建Pull Request到 `main` 分支  
- 手动触发 (workflow_dispatch)

### 2. **构建步骤**

```yaml
# 环境: Windows Server 2022
# Python: 3.9
# 缓存: pip包 + EasyOCR模型
```

1. **环境准备**
   - 设置Python 3.9环境
   - 缓存pip依赖和EasyOCR模型（加速后续构建）

2. **依赖安装**
   ```bash
   pip install -r requirements.txt
   ```

3. **模型准备**
   ```bash
   python prepare_models_easyocr.py
   ```
   - 下载 `craft_mlt_25k.pth` (检测模型)
   - 下载 `zh_sim_g2.pth` (中文识别模型)

4. **配置验证**
   ```bash
   python test_packaging_config.py
   ```
   - 验证模型文件存在
   - 检查spec配置正确
   - 测试离线补丁功能

5. **构建exe**
   ```bash
   python build_windows_with_models.py
   ```
   - 使用PyInstaller打包
   - 包含EasyOCR模型到exe中
   - 应用离线补丁阻止网络下载

6. **输出artifacts**
   - 文件位置: `release/` 目录
   - 包含: `MonitorOCR_EasyOCR.exe`、`config.json`、`README.md`
   - 保留时间: 30天

## 关键特性

### 🔒 **完全离线**
- ✅ 模型文件打包在exe内
- ✅ 网络下载功能被完全屏蔽
- ✅ 支持断网环境运行

### ⚡ **优化性能**
- ✅ 模型缓存 - 后续构建更快
- ✅ pip缓存 - 依赖安装更快
- ✅ 一次构建，处处运行

### 📦 **完整打包**
- ✅ 单个exe文件包含所有依赖
- ✅ 配置文件和说明文档
- ✅ GPU设置支持

## 文件结构

构建完成后的artifacts包含:

```
release/
├── MonitorOCR_EasyOCR.exe    # 主程序 (预计150MB+)
├── config.json               # 配置文件
└── README.md                 # 使用说明
```

## 使用方法

### 手动触发构建

1. 访问GitHub仓库的 **Actions** 页面
2. 选择 **Build Windows Executable** workflow
3. 点击 **Run workflow** 按钮
4. 等待构建完成（约10-15分钟）
5. 下载 **MonitorOCR-Windows-EasyOCR** artifacts

### 自动触发构建

推送代码到main分支即可自动触发构建。

## 验证清单

构建成功后，exe文件应该：

- ✅ 文件大小 > 100MB (包含模型)
- ✅ 在无Python环境的Windows机器上运行
- ✅ 断网状态下正常启动
- ✅ 日志显示 "Found X model files in packaged directory"
- ❌ 没有 "Downloading detection/recognition model" 信息

## 故障排除

### 常见问题

1. **构建失败: 模型下载超时**
   - GitHub Actions网络环境问题
   - 会自动重试，或手动重新运行

2. **exe文件太小**
   - 模型文件未正确打包
   - 检查spec文件中的models配置

3. **运行时仍然下载模型**
   - 离线补丁未生效
   - 检查`easyocr_offline_patch.py`是否包含在打包中

### 调试信息

构建过程中的关键日志:
```
✅ EasyOCR离线补丁已应用
✅ Network functions blocked
✅ Found EasyOCR models in: C:\Users\runneradmin\.EasyOCR\model
✅ Added craft model: ...
✅ Added zh model: ...
✅ 文件大小: XXX.X MB
```

## 本地测试

在提交前，可以本地测试:

```bash
# 1. 验证配置
python test_packaging_config.py

# 2. 构建测试
python build_windows_with_models.py
```

## 配置文件

### requirements.txt
确保包含必要的依赖:
```txt
PyInstaller>=5.0
easyocr
torch
torchvision
opencv-python
pillow
numpy
flask
flask-cors
```

### config.json
默认配置支持CPU和GPU切换:
```json
{
  "ocr": {
    "use_gpu": false,
    "easyocr": {
      "use_gpu": false,
      "verbose": true
    }
  }
}
```

## 更新说明

当需要更新模型或修改打包配置时:

1. 修改相关文件
2. 推送到main分支
3. 自动触发新的构建
4. 下载新的exe文件

构建产物会自动包含最新的修复和功能！
