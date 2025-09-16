#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows packaging script
Use PyInstaller to package the application as Windows executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_executable():
    """Build Windows executable"""
    
    print("Starting Windows executable build...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not installed, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Clean previous builds
    build_dirs = ["build", "dist", "__pycache__"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned directory: {dir_name}")
    
    # Copy PaddleOCR model files
    from model_manager import ModelManager
    model_manager = ModelManager()
    if not model_manager.copy_models_for_packaging():
        print("Model file copy failed, please run prepare_models.py first")
        return False
    
    # PyInstaller command parameters (macOS uses : separator)
    import platform
    separator = ":" if platform.system() != "Windows" else ";"
    
    cmd = [
        "pyinstaller",
        "--onefile",                    # Package as single file
        "--windowed",                   # Windows GUI application
        "--name=MonitorOCR",           # Executable name
        "--icon=icon.ico",             # Icon file (if exists)
        f"--add-data=config.json{separator}.",    # Include config file
        f"--add-data=paddlex_models{separator}paddlex_models",  # Include model files
        "--hidden-import=paddleocr",   # Hidden imports
        "--hidden-import=cv2",
        "--hidden-import=PIL",
        "--hidden-import=numpy",
        "--hidden-import=flask",
        "--hidden-import=tkinter",
        "--hidden-import=paddle",
        "--collect-all=paddleocr",     # Collect all paddleocr files
        "--collect-all=paddle",
        "--collect-all=paddlex",
        "main.py"
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        # Execute packaging command
        print("Executing PyInstaller packaging...")
        print(" ".join(cmd))
        subprocess.check_call(cmd)
        
        # Check output files (different for different platforms)
        import platform
        if platform.system() == "Darwin":  # macOS
            app_path = Path("dist/MonitorOCR.app")
            exe_path = app_path / "Contents/MacOS/MonitorOCR"
        else:  # Windows
            app_path = Path("dist/MonitorOCR.exe")
            exe_path = app_path
        
        if app_path.exists():
            print(f"Packaging successful!")
            print(f"Application location: {app_path.absolute()}")
            
            if exe_path.exists():
                print(f"Executable size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            # Create release directory
            release_dir = Path("release")
            release_dir.mkdir(exist_ok=True)
            
            # Copy files to release directory
            if platform.system() == "Darwin":
                # macOS: Copy entire .app bundle
                if (release_dir / "MonitorOCR.app").exists():
                    shutil.rmtree(release_dir / "MonitorOCR.app")
                shutil.copytree(app_path, release_dir / "MonitorOCR.app")
                
                # Create startup script
                with open(release_dir / "start.sh", "w", encoding="utf-8") as f:
                    f.write("#!/bin/bash\n")
                    f.write("echo 'Starting Monitor OCR System...'\n")
                    f.write("open MonitorOCR.app\n")
                os.chmod(release_dir / "start.sh", 0o755)
            else:
                # Windows: Copy exe file
                shutil.copy2(exe_path, release_dir / "MonitorOCR.exe")
                
                # Create startup script
                with open(release_dir / "start.bat", "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write("echo Starting Monitor OCR System...\n")
                    f.write("MonitorOCR.exe\n")
                    f.write("pause\n")
            
            # Copy config files and documentation
            shutil.copy2("config.json", release_dir / "config.json")
            shutil.copy2("README.md", release_dir / "README.md")
            
            print(f"Release package created: {release_dir.absolute()}")
            
        else:
            print("Packaging failed: Output file not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Packaging failed: {e}")
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
        # Check if running in CI environment (no interactive input available)
        import sys
        if sys.stdin.isatty():
            # Interactive mode
            print("\nCreate installer script? (y/n): ", end="")
            try:
                if input().lower().startswith('y'):
                    create_installer()
            except EOFError:
                print("Skipping installer creation (non-interactive environment)")
        else:
            # Non-interactive mode (CI/CD)
            print("Non-interactive environment, automatically creating installer script...")
            create_installer()
