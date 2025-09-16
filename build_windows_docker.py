#!/usr/bin/env python3
"""
使用Docker进行Windows交叉编译的脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_with_docker():
    """使用Docker构建Windows可执行文件"""
    
    print("开始使用Docker进行Windows交叉编译...")
    
    # 检查Docker是否可用
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker未安装或不可用")
        print("请安装Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False
    
    # 构建Docker镜像
    print("构建Windows编译环境...")
    try:
        subprocess.run([
            "docker", "build", 
            "-f", "Dockerfile.windows",
            "-t", "monitor-ocr-windows-builder",
            "."
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker镜像构建失败: {e}")
        return False
    
    # 运行容器进行编译
    print("在Windows容器中编译...")
    try:
        # 创建输出目录
        output_dir = Path("windows_build")
        output_dir.mkdir(exist_ok=True)
        
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{output_dir.absolute()}:/app/output",
            "monitor-ocr-windows-builder",
            "powershell", "-Command",
            "python build_windows.py; Copy-Item -Recurse release/* /app/output/"
        ], check=True)
        
        print(f"✅ Windows可执行文件已生成到: {output_dir.absolute()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows编译失败: {e}")
        return False

def build_with_wine():
    """使用Wine在macOS上运行Windows Python"""
    
    print("开始使用Wine进行Windows编译...")
    
    # 检查Wine是否安装
    try:
        subprocess.run(["wine", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Wine未安装")
        print("请安装Wine: brew install wine")
        return False
    
    # 这里需要安装Windows版本的Python和依赖
    print("⚠️  Wine方法需要手动配置Windows Python环境")
    print("建议使用Docker方法或在真实Windows环境中编译")
    return False

if __name__ == "__main__":
    print("Windows交叉编译选项:")
    print("1. 使用Docker (推荐)")
    print("2. 使用Wine")
    print("3. 退出")
    
    choice = input("请选择编译方法 (1-3): ").strip()
    
    if choice == "1":
        build_with_docker()
    elif choice == "2":
        build_with_wine()
    else:
        print("退出")
