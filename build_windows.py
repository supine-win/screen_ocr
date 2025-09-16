#!/usr/bin/env python3
"""
Windows打包脚本
使用PyInstaller将应用打包为Windows可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_executable():
    """构建Windows可执行文件"""
    
    print("开始构建Windows可执行文件...")
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 清理之前的构建
    build_dirs = ["build", "dist", "__pycache__"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"清理目录: {dir_name}")
    
    # 复制PaddleOCR模型文件
    from model_manager import ModelManager
    model_manager = ModelManager()
    if not model_manager.copy_models_for_packaging():
        print("❌ 模型文件复制失败，请先运行 prepare_models.py")
        return False
    
    # PyInstaller命令参数 (macOS使用:分隔符)
    import platform
    separator = ":" if platform.system() != "Windows" else ";"
    
    cmd = [
        "pyinstaller",
        "--onefile",                    # 打包为单个文件
        "--windowed",                   # Windows GUI应用
        "--name=MonitorOCR",           # 可执行文件名
        "--icon=icon.ico",             # 图标文件（如果存在）
        f"--add-data=config.json{separator}.",    # 包含配置文件
        f"--add-data=paddlex_models{separator}paddlex_models",  # 包含模型文件
        "--hidden-import=paddleocr",   # 隐式导入
        "--hidden-import=cv2",
        "--hidden-import=PIL",
        "--hidden-import=numpy",
        "--hidden-import=flask",
        "--hidden-import=tkinter",
        "--hidden-import=paddle",
        "--collect-all=paddleocr",     # 收集所有paddleocr文件
        "--collect-all=paddle",
        "--collect-all=paddlex",
        "main.py"
    ]
    
    # 如果图标文件不存在，移除图标参数
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        # 执行打包命令
        print("执行PyInstaller打包...")
        print(" ".join(cmd))
        subprocess.check_call(cmd)
        
        # 检查输出文件（根据平台不同）
        import platform
        if platform.system() == "Darwin":  # macOS
            app_path = Path("dist/MonitorOCR.app")
            exe_path = app_path / "Contents/MacOS/MonitorOCR"
        else:  # Windows
            app_path = Path("dist/MonitorOCR.exe")
            exe_path = app_path
        
        if app_path.exists():
            print(f"✅ 打包成功！")
            print(f"应用程序位置: {app_path.absolute()}")
            
            if exe_path.exists():
                print(f"可执行文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            # 创建发布目录
            release_dir = Path("release")
            release_dir.mkdir(exist_ok=True)
            
            # 复制文件到发布目录
            if platform.system() == "Darwin":
                # macOS: 复制整个.app包
                if (release_dir / "MonitorOCR.app").exists():
                    shutil.rmtree(release_dir / "MonitorOCR.app")
                shutil.copytree(app_path, release_dir / "MonitorOCR.app")
                
                # 创建启动脚本
                with open(release_dir / "start.sh", "w", encoding="utf-8") as f:
                    f.write("#!/bin/bash\n")
                    f.write("echo '启动监控OCR系统...'\n")
                    f.write("open MonitorOCR.app\n")
                os.chmod(release_dir / "start.sh", 0o755)
            else:
                # Windows: 复制exe文件
                shutil.copy2(exe_path, release_dir / "MonitorOCR.exe")
                
                # 创建启动脚本
                with open(release_dir / "start.bat", "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write("echo 启动监控OCR系统...\n")
                    f.write("MonitorOCR.exe\n")
                    f.write("pause\n")
            
            # 复制配置文件和文档
            shutil.copy2("config.json", release_dir / "config.json")
            shutil.copy2("README.md", release_dir / "README.md")
            
            print(f"✅ 发布包已创建: {release_dir.absolute()}")
            
        else:
            print("❌ 打包失败：找不到输出文件")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        return False
    
    return True

def create_installer():
    """创建Windows安装程序（需要NSIS）"""
    
    nsis_script = """
; MonitorOCR安装脚本
!define APPNAME "MonitorOCR"
!define COMPANYNAME "YourCompany"
!define DESCRIPTION "监控OCR系统"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "https://github.com/yourrepo"
!define UPDATEURL "https://github.com/yourrepo"
!define ABOUTURL "https://github.com/yourrepo"

!define INSTALLSIZE 200000

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\\${APPNAME}"

Name "${APPNAME}"
Icon "icon.ico"
outFile "MonitorOCR_Setup.exe"

!include LogicLib.nsh

page components
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "需要管理员权限才能安装此程序。"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    file "release\\MonitorOCR.exe"
    file "release\\config.json"
    file "release\\README.md"
    file "release\\start.bat"
    
    writeUninstaller "$INSTDIR\\uninstall.exe"
    
    createDirectory "$SMPROGRAMS\\${APPNAME}"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\MonitorOCR.exe"
    createShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\MonitorOCR.exe"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayIcon" "$INSTDIR\\MonitorOCR.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
sectionEnd

section "uninstall"
    delete "$INSTDIR\\MonitorOCR.exe"
    delete "$INSTDIR\\config.json"
    delete "$INSTDIR\\README.md"
    delete "$INSTDIR\\start.bat"
    delete "$INSTDIR\\uninstall.exe"
    
    rmDir "$INSTDIR"
    
    delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
    rmDir "$SMPROGRAMS\\${APPNAME}"
    delete "$DESKTOP\\${APPNAME}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
sectionEnd
"""
    
    with open("installer.nsi", "w", encoding="utf-8") as f:
        f.write(nsis_script)
    
    print("NSIS安装脚本已创建: installer.nsi")
    print("请安装NSIS并运行以下命令创建安装程序:")
    print("makensis installer.nsi")

if __name__ == "__main__":
    if build_windows_executable():
        print("\n是否创建安装程序脚本? (y/n): ", end="")
        if input().lower().startswith('y'):
            create_installer()
