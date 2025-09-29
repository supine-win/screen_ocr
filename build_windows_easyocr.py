#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows packaging script with EasyOCR support
Use PyInstaller to package the application as Windows executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_executable():
    """Build Windows executable with EasyOCR"""
    
    print("Starting Windows executable build with EasyOCR...")
    
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
    
    # Copy EasyOCR model files
    home_dir = Path.home()
    easyocr_model_dir = home_dir / ".EasyOCR" / "model"
    local_easyocr_dir = Path("easyocr_models")
    
    if easyocr_model_dir.exists():
        local_easyocr_dir.mkdir(exist_ok=True)
        for model_file in easyocr_model_dir.glob("*.pth"):
            shutil.copy2(model_file, local_easyocr_dir / model_file.name)
            print(f"Copied EasyOCR model: {model_file.name}")
    
    # Copy PaddleOCR models as fallback (optional)
    from model_manager import ModelManager
    try:
        model_manager = ModelManager()
        model_manager.copy_models_for_packaging()
        print("PaddleOCR models copied (fallback)")
    except Exception as e:
        print(f"PaddleOCR models not available (optional): {e}")
    
    # PyInstaller command parameters
    import platform
    separator = ":" if platform.system() != "Windows" else ";"
    
    cmd = [
        "pyinstaller",
        "--onefile",                    # Package as single file
        "--windowed",                   # Windows GUI application
        "--name=MonitorOCR_EasyOCR",   # Executable name
        "--icon=icon.ico",             # Icon file (if exists)
        f"--add-data=config.json{separator}.",    # Include config file
        f"--add-data=debug_windows.py{separator}.",  # Include debug script
        "--console",                    # Show console for debugging
    ]
    
    # Add EasyOCR models if they exist
    if local_easyocr_dir.exists():
        cmd.append(f"--add-data=easyocr_models{separator}easyocr_models")
    
    # Add PaddleOCR models if they exist (fallback)
    if Path("paddlex_models").exists():
        cmd.append(f"--add-data=paddlex_models{separator}paddlex_models")
    
    # Hidden imports for EasyOCR and optimization modules
    hidden_imports = [
        # EasyOCR and dependencies
        "easyocr",
        "easyocr.detection",
        "easyocr.recognition",
        
        # Optimization modules (v2)
        "logger_config",
        "model_path_manager", 
        "performance_monitor",
        "cache_manager",
        "error_handler",
        "health_monitor",
        "config_validator",
        "ocr_processor_v2",
        
        # Original version modules
        "simple_logger",
        "ocr_processor",
        "easyocr.utils",
        "easyocr.config",
        "torch",
        "torch._C",
        "torchvision",
        "torchvision.ops",
        "torchvision.transforms",
        "scipy",
        "scipy.ndimage",
        "skimage",
        "python_bidi",
        "shapely",
        "pyclipper",
        "ninja",
        # PaddleOCR as fallback
        "paddleocr",
        "paddle",
        "paddlex",
        # Common dependencies
        "cv2",
        "PIL",
        "numpy",
        "flask",
        "tkinter",
    ]
    
    for import_name in hidden_imports:
        cmd.append(f"--hidden-import={import_name}")
    
    # Collect all packages
    collect_packages = [
        "easyocr",
        "torch",
        "torchvision",
        "scipy",
        "skimage",
        "paddleocr",
        "paddle",
        "paddlex",
    ]
    
    for package in collect_packages:
        cmd.append(f"--collect-all={package}")
    
    # Add main script
    cmd.append("main.py")
    
    # Remove icon parameter if icon file doesn't exist
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        # Execute packaging command
        print("Executing PyInstaller packaging...")
        print("Command: " + " ".join(cmd))
        subprocess.check_call(cmd)
        
        # Check output files
        if platform.system() == "Darwin":  # macOS
            app_path = Path("dist/MonitorOCR_EasyOCR.app")
            exe_path = app_path / "Contents/MacOS/MonitorOCR_EasyOCR"
        else:  # Windows
            app_path = Path("dist/MonitorOCR_EasyOCR.exe")
            exe_path = app_path
        
        if app_path.exists():
            print(f"✅ Packaging successful!")
            print(f"Application location: {app_path.absolute()}")
            
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"Executable size: {size_mb:.1f} MB")
            
            # Create release directory
            release_dir = Path("release")
            release_dir.mkdir(exist_ok=True)
            
            # Copy files to release directory
            if platform.system() == "Darwin":
                # macOS: Copy entire .app bundle
                if (release_dir / "MonitorOCR_EasyOCR.app").exists():
                    shutil.rmtree(release_dir / "MonitorOCR_EasyOCR.app")
                shutil.copytree(app_path, release_dir / "MonitorOCR_EasyOCR.app")
                
                # Create startup script
                with open(release_dir / "start.sh", "w", encoding="utf-8") as f:
                    f.write("#!/bin/bash\n")
                    f.write("echo 'Starting Monitor OCR System with EasyOCR...'\n")
                    f.write("open MonitorOCR_EasyOCR.app\n")
                os.chmod(release_dir / "start.sh", 0o755)
            else:
                # Windows: Copy exe file
                shutil.copy2(exe_path, release_dir / "MonitorOCR_EasyOCR.exe")
                
                # Create startup script
                with open(release_dir / "start.bat", "w", encoding="utf-8") as f:
                    f.write("@echo off\n")
                    f.write("echo Starting Monitor OCR System with EasyOCR...\n")
                    f.write("MonitorOCR_EasyOCR.exe\n")
                    f.write("pause\n")
            
            # Copy config files and documentation
            shutil.copy2("config.json", release_dir / "config.json")
            if Path("README.md").exists():
                shutil.copy2("README.md", release_dir / "README.md")
            
            # Create version info
            with open(release_dir / "version.txt", "w", encoding="utf-8") as f:
                f.write("MonitorOCR with EasyOCR\n")
                f.write("Version: 1.1.0\n")
                f.write("OCR Engine: EasyOCR (Primary), PaddleOCR (Fallback)\n")
                f.write("Supported Languages: Chinese (Simplified), English\n")
            
            print(f"✅ Release package created: {release_dir.absolute()}")
            
            # Display package contents
            print("\nRelease package contents:")
            for item in release_dir.iterdir():
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    print(f"  - {item.name}: {size_mb:.2f} MB")
                else:
                    print(f"  - {item.name}/ (directory)")
            
        else:
            print("❌ Packaging failed: Output file not found")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Packaging failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def create_installer():
    """Create Windows installer (requires NSIS)"""
    
    nsis_script = """
; MonitorOCR with EasyOCR Installation Script
!define APPNAME "MonitorOCR EasyOCR"
!define COMPANYNAME "Windsurf"
!define DESCRIPTION "Monitor OCR System with EasyOCR Support"
!define VERSIONMAJOR 1
!define VERSIONMINOR 1
!define VERSIONBUILD 0

!define HELPURL "https://github.com/supine-win/screen_ocr"
!define UPDATEURL "https://github.com/supine-win/screen_ocr/releases"
!define ABOUTURL "https://github.com/supine-win/screen_ocr"

!define INSTALLSIZE 500000

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\\${APPNAME}"

Name "${APPNAME}"
Icon "icon.ico"
outFile "MonitorOCR_EasyOCR_Setup.exe"

!include LogicLib.nsh

page components
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Administrator privileges required to install this program."
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
    file "release\\MonitorOCR_EasyOCR.exe"
    file "release\\config.json"
    file "release\\README.md"
    file "release\\version.txt"
    file "release\\start.bat"
    
    writeUninstaller "$INSTDIR\\uninstall.exe"
    
    createDirectory "$SMPROGRAMS\\${APPNAME}"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk" "$INSTDIR\\MonitorOCR_EasyOCR.exe"
    createShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\MonitorOCR_EasyOCR.exe"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayIcon" "$INSTDIR\\MonitorOCR_EasyOCR.exe"
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
    delete "$INSTDIR\\MonitorOCR_EasyOCR.exe"
    delete "$INSTDIR\\config.json"
    delete "$INSTDIR\\README.md"
    delete "$INSTDIR\\version.txt"
    delete "$INSTDIR\\start.bat"
    delete "$INSTDIR\\uninstall.exe"
    
    rmDir "$INSTDIR"
    
    delete "$SMPROGRAMS\\${APPNAME}\\${APPNAME}.lnk"
    rmDir "$SMPROGRAMS\\${APPNAME}"
    delete "$DESKTOP\\${APPNAME}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
sectionEnd
"""
    
    with open("installer_easyocr.nsi", "w", encoding="utf-8") as f:
        f.write(nsis_script)
    
    print("\n✅ NSIS installer script created: installer_easyocr.nsi")
    print("To create the installer, install NSIS and run:")
    print("  makensis installer_easyocr.nsi")

if __name__ == "__main__":
    if build_windows_executable():
        print("\n✅ Build completed successfully!")
        
        # Check if running in CI environment
        if not sys.stdin.isatty():
            # Non-interactive mode (CI/CD)
            print("CI environment detected, creating installer script...")
            create_installer()
        else:
            # Interactive mode
            print("\nCreate installer script? (y/n): ", end="")
            try:
                response = input().strip().lower()
                if response.startswith('y'):
                    create_installer()
            except EOFError:
                print("Skipping installer creation")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)
