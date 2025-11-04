#!/usr/bin/env python3
"""
服务器启动脚本
支持两种运行模式:
1. 开发模式: 使用uvicorn --reload，支持代码热更新
2. 生产模式: 在Unix系统上使用gunicorn多worker部署，在Windows上使用uvicorn多worker
"""

import os
import sys
import argparse
import subprocess
import platform

def start_development():
    """开发模式启动"""
    print("以开发模式启动服务器...")
    print("使用命令: uvicorn api:app --reload")
    
    # 使用uvicorn启动开发服务器
    subprocess.run([
        "uvicorn", 
        "api:app", 
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

def start_production():
    """生产模式启动"""
    system = platform.system()
    print(f"检测到操作系统: {system}")
    
    if system == "Windows":
        print("Windows环境下使用uvicorn多worker模式...")
        # Windows环境下使用uvicorn多worker模式
        subprocess.run([
            "uvicorn", 
            "api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--workers", "4"  # 设置worker数量为4
        ])
    else:
        print("Unix环境下使用Gunicorn多Worker部署...")
        # Unix环境下使用gunicorn启动生产服务器
        subprocess.run([
            "gunicorn", 
            "-c", "gunicorn.conf.py",
            "api:app"
        ])

def main():
    parser = argparse.ArgumentParser(description="重复检测服务启动脚本")
    parser.add_argument(
        "--mode", 
        choices=["dev", "prod"], 
        default="dev",
        help="运行模式: dev(开发模式) | prod(生产模式)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "dev":
        start_development()
    elif args.mode == "prod":
        start_production()

if __name__ == "__main__":
    main()