#!/bin/bash
# 测试打包脚本

echo "================================"
echo "MonitorOCR 打包测试"
echo "================================"

# 检查PyInstaller
echo "检查PyInstaller..."
if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller未安装"
    exit 1
fi
echo "✅ PyInstaller已安装"

# 清理旧文件
echo "清理旧的打包文件..."
rm -rf build dist *.app

# 尝试打包
echo "开始打包（测试模式）..."
pyinstaller MonitorOCR_EasyOCR.spec --clean --noconfirm

# 检查结果
if [ -d "dist/MonitorOCR_EasyOCR.app" ]; then
    echo "✅ 打包成功！"
    
    # 显示大小
    echo ""
    echo "应用大小:"
    du -sh dist/MonitorOCR_EasyOCR.app
    
    # 检查模型文件
    echo ""
    echo "检查包含的模型文件:"
    find dist/MonitorOCR_EasyOCR.app -name "*.pth" -exec ls -lh {} \;
    
    # 统计文件
    echo ""
    echo "文件统计:"
    echo "- Python文件: $(find dist/MonitorOCR_EasyOCR.app -name "*.py" | wc -l)"
    echo "- 动态库: $(find dist/MonitorOCR_EasyOCR.app -name "*.dylib" | wc -l)"
    echo "- 模型文件: $(find dist/MonitorOCR_EasyOCR.app -name "*.pth" | wc -l)"
    
else
    echo "❌ 打包失败"
    echo ""
    echo "查看错误日志:"
    tail -20 build/MonitorOCR_EasyOCR/warn-MonitorOCR_EasyOCR.txt 2>/dev/null
fi

echo ""
echo "================================"
echo "打包测试完成"
echo "================================"
