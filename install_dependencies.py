#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI-QING 依赖安装脚本
自动检测和安装所需的Python包
"""

import subprocess
import sys
import importlib
import os
from pathlib import Path

# 依赖配置
REQUIRED_PACKAGES = {
    'Pillow': '>=9.0.0',
    'opencv-python': '>=4.5.0', 
    'scipy': '>=1.7.0',
    'scikit-image': '>=0.18.0',
    'cairosvg': '>=2.5.0',
}

# AI API依赖
AI_API_PACKAGES = {
    'openai': '>=1.0.0',
}

OPTIONAL_PACKAGES = {
    'svglib': '>=1.4.0',
    'reportlab': '>=3.6.0',
}

BUILTIN_PACKAGES = ['torch', 'numpy']  # ComfyUI内置，无需安装

def check_package_installed(package_name):
    """检查包是否已安装"""
    try:
        # 特殊包名映射
        import_name_map = {
            'opencv-python': 'cv2',
            'scikit-image': 'skimage',
            'openai': 'openai',
            'Pillow': 'PIL',
        }
        
        import_name = import_name_map.get(package_name, package_name.replace('-', '_'))
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def install_package(package_name, version_spec=''):
    """安装单个包"""
    package_spec = f"{package_name}{version_spec}"
    try:
        print(f"正在安装 {package_spec}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_spec])
        print(f"✓ {package_name} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {package_name} 安装失败: {e}")
        return False

def check_ffmpeg():
    """检查FFmpeg是否可用"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """主安装流程"""
    print("=" * 60)
    print("ComfyUI-QING 依赖检查和安装工具")
    print("=" * 60)
    
    # 检查内置依赖
    print("\n🔍 检查ComfyUI内置依赖...")
    for package in BUILTIN_PACKAGES:
        if check_package_installed(package):
            print(f"✓ {package} - ComfyUI内置，已可用")
        else:
            print(f"⚠ {package} - 未找到，请确保ComfyUI正确安装")
    
    # 安装必需依赖
    print("\n📦 检查并安装必需依赖...")
    failed_packages = []
    
    for package, version in REQUIRED_PACKAGES.items():
        if check_package_installed(package):
            print(f"✓ {package} - 已安装")
        else:
            print(f"⚠ {package} - 未安装，开始安装...")
            if not install_package(package, version):
                failed_packages.append(package)
    
    # 安装AI API依赖
    print("\n🤖 检查并安装AI API依赖...")
    for package, version in AI_API_PACKAGES.items():
        if check_package_installed(package):
            print(f"✓ {package} - 已安装")
        else:
            print(f"⚠ {package} - 未安装，开始安装...")
            if not install_package(package, version):
                failed_packages.append(package)
    
    # 询问是否安装可选依赖
    print("\n🎯 可选依赖 (增强SVG处理功能):")
    for package, version in OPTIONAL_PACKAGES.items():
        if check_package_installed(package):
            print(f"✓ {package} - 已安装")
        else:
            response = input(f"是否安装 {package}? (y/n): ").lower().strip()
            if response in ['y', 'yes', '是']:
                if not install_package(package, version):
                    failed_packages.append(package)
    
    # 检查FFmpeg
    print("\n🎬 检查系统级依赖...")
    if check_ffmpeg():
        print("✓ FFmpeg - 已安装，视频合成功能可用")
    else:
        print("⚠ FFmpeg - 未找到")
        print("  视频合成节点需要FFmpeg支持")
        print("  安装方法:")
        print("  - Windows: https://ffmpeg.org/download.html")
        print("  - Linux: sudo apt-get install ffmpeg")
        print("  - macOS: brew install ffmpeg")
    
    # 安装结果总结
    print("\n" + "=" * 60)
    if failed_packages:
        print(f"⚠ 安装完成，但以下包安装失败: {', '.join(failed_packages)}")
        print("请手动安装或检查网络连接")
        print("\n手动安装命令:")
        for package in failed_packages:
            if package in REQUIRED_PACKAGES:
                version = REQUIRED_PACKAGES[package]
            elif package in AI_API_PACKAGES:
                version = AI_API_PACKAGES[package]
            else:
                version = OPTIONAL_PACKAGES.get(package, '')
            print(f"  pip install {package}{version}")
        return 1
    else:
        print("✅ 所有依赖安装完成！")
        print("\n🎉 ComfyUI-QING 功能模块状态:")
        print("  ✓ 图像处理 - 完全可用")
        print("  ✓ SVG处理 - 完全可用") 
        print("  ✓ 遮罩工程 - 完全可用")
        print("  ✓ AI对话引擎 - 完全可用 (需配置API密钥)")
        if check_ffmpeg():
            print("  ✓ 视频合成 - 完全可用")
        else:
            print("  ⚠ 视频合成 - 需要安装FFmpeg")
        print("\n重启ComfyUI后即可使用ComfyUI-QING的所有功能")
        print("API密钥配置: ComfyUI设置 → 🎨QING → API配置")
        return 0

if __name__ == "__main__":
    sys.exit(main())
