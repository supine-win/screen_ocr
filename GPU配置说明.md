# GPU配置说明

## 概述

应用现在支持通过配置文件控制是否使用GPU进行OCR识别，提供更好的性能控制。

## 配置文件设置

在 `config.json` 文件的 `ocr` 部分，可以配置以下GPU相关选项：

```json
{
  "ocr": {
    "use_gpu": false,        // PaddleOCR的GPU设置
    "easyocr": {
      "use_gpu": false,      // EasyOCR的GPU设置
      "verbose": true        // EasyOCR详细日志
    }
  }
}
```

## 配置选项说明

### `use_gpu` (布尔值)
- **默认值**: `false`
- **作用**: 控制PaddleOCR是否使用GPU
- **适用**: 当应用回退到PaddleOCR时生效

### `easyocr.use_gpu` (布尔值)
- **默认值**: `false`
- **作用**: 控制EasyOCR是否使用GPU
- **适用**: 当应用使用EasyOCR时生效（优先使用）

### `easyocr.verbose` (布尔值)
- **默认值**: `true`
- **作用**: 控制EasyOCR是否输出详细日志
- **建议**: 开发调试时保持`true`，生产环境可设为`false`

## GPU环境要求

### 启用GPU前的前置条件

1. **硬件要求**
   - NVIDIA GPU（支持CUDA）
   - 足够的显存（建议4GB+）

2. **软件环境**
   ```bash
   # 安装CUDA版本的PyTorch
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # 安装GPU版本的PaddlePaddle
   pip install paddlepaddle-gpu
   ```

3. **验证GPU可用性**
   ```python
   import torch
   print(f"CUDA可用: {torch.cuda.is_available()}")
   print(f"GPU数量: {torch.cuda.device_count()}")
   ```

## 性能对比

| 模式 | 初始化时间 | 识别速度 | 内存占用 | 适用场景 |
|------|-----------|----------|----------|----------|
| CPU  | 快        | 较慢     | 低       | 无GPU环境、节能模式 |
| GPU  | 较慢      | 快       | 高       | 有GPU环境、高性能需求 |

## 使用建议

### 开发环境
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

### 生产环境（有GPU）
```json
{
  "ocr": {
    "use_gpu": true,
    "easyocr": {
      "use_gpu": true,
      "verbose": false
    }
  }
}
```

### 生产环境（无GPU）
```json
{
  "ocr": {
    "use_gpu": false,
    "easyocr": {
      "use_gpu": false,
      "verbose": false
    }
  }
}
```

## 故障排除

### 常见问题

1. **GPU设置为true但仍使用CPU**
   - 检查CUDA环境是否正确安装
   - 确认PyTorch能识别GPU：`torch.cuda.is_available()`

2. **GPU初始化失败**
   - 检查显存是否足够
   - 尝试重启应用释放显存
   - 降级到CPU模式

3. **性能没有提升**
   - 确认使用的是CUDA版本的PyTorch
   - 检查GPU利用率：`nvidia-smi`

### 日志查看

启用详细日志查看GPU使用情况：
```
[INFO] EasyOCR GPU设置: True
[INFO] EasyOCR初始化参数: {'lang_list': ['ch_sim', 'en'], 'gpu': True, 'verbose': True}
```

如果看到"Using CPU"警告，说明GPU未成功启用。

## 动态切换

修改配置文件后，重启应用即可应用新的GPU设置。暂不支持运行时动态切换。
