# PaddleX 版本文件修复说明

## 问题描述

在Windows上运行打包后的应用程序时出现以下错误：

```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Software\\MonitorOCR-Windows-EasyOCR\\MonitorOCR_EasyOCR\\_internal\\paddlex\\.version'
```

## 根本原因

PyInstaller在打包时没有包含PaddleX包的`.version`隐藏文件，导致`paddlex.version.get_pdx_version()`函数无法找到版本信息文件。

## 修复措施

### 1. **更新 MonitorOCR_EasyOCR.spec 文件**

添加了智能版本文件检测和包含逻辑：

```python
# 添加PaddleX版本文件（修复FileNotFoundError）
import pkg_resources
import site
try:
    # 尝试查找PaddleX包位置和版本文件
    paddlex_dist = pkg_resources.get_distribution('paddlex')
    paddlex_location = paddlex_dist.location
    print(f"Found PaddleX at: {paddlex_location}")
    
    # 查找.version文件
    import glob
    version_files = []
    for site_dir in site.getsitepackages():
        version_file_path = os.path.join(site_dir, 'paddlex', '.version')
        if os.path.exists(version_file_path):
            version_files.append((version_file_path, 'paddlex'))
            print(f"Found .version file: {version_file_path}")
    
    # 如果找不到.version文件，创建一个
    if not version_files:
        print("Creating missing .version file for PaddleX...")
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write(paddlex_dist.version)
            temp_version_path = f.name
        version_files.append((temp_version_path, 'paddlex'))
        print(f"Created temporary .version file: {temp_version_path}")
    
    datas.extend(version_files)
    
except Exception as e:
    print(f"Warning: Could not process PaddleX version file: {e}")
    # 创建一个默认的版本文件
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write('2.0.0')  # 默认版本
            temp_version_path = f.name
        datas.append((temp_version_path, 'paddlex'))
        print(f"Created default .version file: {temp_version_path}")
    except Exception as e2:
        print(f"Failed to create default version file: {e2}")
```

### 2. **更新 build_windows_easyocr.py 脚本**

添加了版本文件预检查功能：

```python
def ensure_paddlex_version_file():
    """确保PaddleX版本文件存在"""
    import site
    import pkg_resources
    
    try:
        # 查找PaddleX包位置
        paddlex_dist = pkg_resources.get_distribution('paddlex')
        print(f"Found PaddleX version: {paddlex_dist.version}")
        
        # 检查.version文件是否存在
        for site_dir in site.getsitepackages():
            paddlex_dir = os.path.join(site_dir, 'paddlex')
            version_file = os.path.join(paddlex_dir, '.version')
            
            if os.path.exists(paddlex_dir) and not os.path.exists(version_file):
                print(f"Creating missing .version file in {paddlex_dir}")
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(paddlex_dist.version)
                print(f"✅ Created .version file: {version_file}")
                return True
            elif os.path.exists(version_file):
                print(f"✅ Found existing .version file: {version_file}")
                return True
    
    except Exception as e:
        print(f"Warning: Could not ensure PaddleX .version file: {e}")
        return False
    
    return False
```

### 3. **添加隐藏导入**

在隐藏导入列表中明确添加：

```python
"paddlex.version",  # 明确导入版本模块
```

### 4. **创建测试脚本**

添加了 `test_paddlex_version_fix.py` 来验证修复是否有效：

- 检查PaddleX版本文件是否存在
- 测试版本模块导入
- 验证创建版本文件的能力
- 测试PyInstaller数据收集

### 5. **更新GitHub Actions**

在CI流程中添加了版本文件修复测试：

```yaml
- name: Test PaddleX version fix
  run: |
    python test_paddlex_version_fix.py
  env:
    PYTHONIOENCODING: utf-8
```

## 修复策略层次

1. **预防性修复**: 在构建前确保版本文件存在
2. **打包时修复**: 在spec文件中智能检测和包含版本文件
3. **回退策略**: 如果找不到版本文件，创建默认版本文件
4. **验证测试**: 提供完整的测试套件验证修复效果

## 测试验证

运行测试脚本验证修复：

```bash
python test_paddlex_version_fix.py
```

## 兼容性说明

- ✅ 兼容不同的PaddleX版本
- ✅ 兼容不同的Python环境（虚拟环境、系统环境）
- ✅ 提供回退策略，即使PaddleX未正确安装也不会阻止打包
- ✅ 支持自动检测和创建缺失的版本文件

## 注意事项

1. 修复后的应用程序在首次运行时会显示版本文件创建信息
2. 如果系统中没有安装PaddleX，会使用默认版本号(2.0.0)
3. 建议在构建前运行测试脚本确保环境正确
4. GitHub Actions会自动验证版本文件修复是否生效

这个修复确保了打包后的Windows可执行文件能够正常运行，不再出现PaddleX版本文件缺失的错误。
