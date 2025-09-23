#!/bin/bash
# MonitorOCR打包脚本

echo "开始打包MonitorOCR (with EasyOCR)..."

# 清理旧的打包文件
rm -rf build dist *.app

# 使用PyInstaller打包
pyinstaller MonitorOCR_EasyOCR.spec --clean

# 检查打包结果
if [ -d "dist/MonitorOCR_EasyOCR.app" ]; then
    echo "✅ 打包成功！"
    echo "应用位置: dist/MonitorOCR_EasyOCR.app"
    
    # 显示包大小
    du -sh dist/MonitorOCR_EasyOCR.app
    
    # 创建DMG（可选）
    # hdiutil create -volname "MonitorOCR" -srcfolder dist/MonitorOCR_EasyOCR.app -ov -format UDZO MonitorOCR.dmg
else
    echo "❌ 打包失败！"
    exit 1
fi
