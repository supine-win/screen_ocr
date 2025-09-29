# 端口更新说明

## 📡 端口变更

为了避免与其他软件的端口冲突，MonitorOCR的默认HTTP端口已从 **8080** 更改为 **9501**。

## 🔧 更新的文件

- `config.json` - 配置文件中的端口设置
- `config_validator.py` - 配置验证器的默认端口
- `main_v2.py` - 主程序的默认端口
- `OPTIMIZATION_GUIDE.md` - 文档中的端口引用
- `start_debug.bat` - Windows启动脚本

## 🌐 API端点更新

**新的默认地址：**
- 健康检查: `http://localhost:9501/api/health`
- 性能指标: `http://localhost:9501/api/metrics`
- 告警信息: `http://localhost:9501/api/alerts`
- 系统诊断: `http://localhost:9501/api/diagnostics`

## 📋 测试命令

```bash
# 健康检查
curl http://localhost:9501/api/health

# 获取指标
curl http://localhost:9501/api/metrics

# 查看告警
curl http://localhost:9501/api/alerts
```

## ⚙️ 自定义端口

如果需要使用其他端口，可以修改 `config.json`:

```json
{
  "http": {
    "host": "0.0.0.0",
    "port": 您的端口号,
    "debug": false
  }
}
```

## 🚀 兼容性

- ✅ 原版和v2版本都已更新
- ✅ Windows打包版本支持
- ✅ 配置验证器自动使用新端口
- ✅ 调试工具显示正确端口

## 🔍 常见端口选择

- **9501** (默认) - 避免冲突的好选择
- **9502-9510** - 备选端口范围
- **8000-8999** - Web开发常用范围

选择9501的原因：
1. 不与常见Web服务冲突 (80, 443, 8080, 8000等)
2. 不与数据库服务冲突 (3306, 5432, 6379等)
3. 在用户端口范围内 (1024-65535)
4. 易于记忆
