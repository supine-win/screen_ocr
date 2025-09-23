#!/bin/bash
# 测试打包后的应用

echo "==============================================="
echo "MonitorOCR 打包应用测试"
echo "==============================================="

APP_PATH="dist/MonitorOCR_EasyOCR.app"
EXE_PATH="$APP_PATH/Contents/MacOS/MonitorOCR_EasyOCR"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ 应用未找到: $APP_PATH"
    echo "请先运行打包脚本: ./build_app.sh"
    exit 1
fi

echo "✅ 应用找到: $APP_PATH"
echo ""

# 显示应用信息
echo "📦 应用信息："
echo "- 大小: $(du -sh $APP_PATH | cut -f1)"
echo "- 可执行文件: $(ls -lh $EXE_PATH | awk '{print $5}')"
echo ""

# 选择测试模式
echo "请选择测试模式："
echo "1) GUI模式 - 打开图形界面"
echo "2) API模式 - 启动API服务器（无GUI）"
echo "3) 帮助信息 - 查看命令行选项"
echo "4) 退出"
echo ""
read -p "选择 (1-4): " choice

case $choice in
    1)
        echo "启动GUI模式..."
        open $APP_PATH
        ;;
    2)
        echo "启动API服务器模式..."
        echo "服务器将在 http://localhost:8080 运行"
        echo "按 Ctrl+C 停止服务器"
        $EXE_PATH --no-gui
        ;;
    3)
        echo "显示帮助信息..."
        $EXE_PATH --help
        ;;
    4)
        echo "退出测试"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
