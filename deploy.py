#!/usr/bin/env python3
"""
Watermark Remover 部署脚本
部署到 Render + Vercel
"""
import os
import subprocess
import requests
import time
import json

# 配置
GITHUB_USER = "PandaLee52"
REPO_NAME = "watermark-remover"
PROJECT_DIR = "watermark-remover"

def run_cmd(cmd, cwd=None):
    """执行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print(f"⚠️ 错误: {result.stderr}")
    return result.returncode == 0

def create_github_repo():
    """创建 GitHub 仓库"""
    print("\n" + "="*60)
    print("📦 步骤1: 创建 GitHub 仓库")
    print("="*60)
    
    # 检查远程是否已存在
    result = subprocess.run("git remote -v", shell=True, capture_output=True, text=True)
    if "origin" in result.stdout:
        print("远程仓库已配置")
        return True
    
    # 创建 GitHub 仓库
    repo_url = f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"
    
    # 使用 gh cli 或直接添加远程
    cmd = f'git remote add origin {repo_url}'
    run_cmd(cmd, cwd=PROJECT_DIR)
    
    # 尝试推送
    cmd = f'git push -u origin main --force'
    if run_cmd(cmd, cwd=PROJECT_DIR):
        print(f"✅ 仓库已创建并推送")
        return True
    
    return False

def deploy_to_render_via_api():
    """使用 Render API 部署"""
    print("\n" + "="*60)
    print("🚀 步骤2: 部署到 Render")
    print("="*60)
    
    # Render API 配置
    RENDER_API_KEY = os.environ.get('RENDER_API_KEY')
    if not RENDER_API_KEY:
        print("⚠️ 未设置 RENDER_API_KEY 环境变量")
        print("请手动部署:")
        print(f"1. 访问 https://dashboard.render.com")
        print(f"2. 连接 GitHub 仓库: {GITHUB_USER}/{REPO_NAME}")
        print("3. 创建 Web Service，设置:")
        print("   - Build Command: pip install -r requirements.txt")
        print("   - Start Command: gunicorn backend.app:app --bind 0.0.0.0:$PORT")
        return False
    
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 创建 Blueprint
    blueprint_spec = {
        "resources": [
            {
                "kind": "web",
                "name": "watermark-remover-api",
                "serviceType": "web",
                "env": "python",
                "region": "singapore",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "gunicorn backend.app:app --bind 0.0.0.0:$PORT",
                "plan": "free"
            }
        ]
    }
    
    try:
        # 创建或更新 Blueprint
        response = requests.post(
            "https://api.render.com/v1/blueprints",
            headers=headers,
            json=blueprint_spec
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ 部署成功!")
            if isinstance(data, list) and len(data) > 0:
                print(f"   URL: {data[0].get('service', {}).get('url', 'N/A')}")
            return True
        else:
            print(f"⚠️ 部署响应: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"⚠️ API 部署失败: {e}")
        return False

def deploy_frontend_to_vercel():
    """部署前端到 Vercel"""
    print("\n" + "="*60)
    print("🌐 步骤3: 部署前端到 Vercel")
    print("="*60)
    
    frontend_dir = os.path.join(PROJECT_DIR, "frontend")
    
    # 更新前端 API 地址
    api_url = "https://watermark-remover-api.onrender.com"
    
    # 创建 vercel.json
    vercel_config = {
        "version": 2,
        "builds": [
            {
                "src": "index.html",
                "use": "@vercel/static"
            }
        ],
        "routes": [
            {"src": "/(.*)", "dest": "index.html"}
        ]
    }
    
    with open(os.path.join(frontend_dir, "vercel.json"), "w") as f:
        json.dump(vercel_config, f, indent=2)
    
    # 部署
    print("运行 vercel deploy...")
    
    # 尝试使用 vercel CLI
    result = subprocess.run(
        "vercel --yes --prod",
        shell=True,
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ 前端部署成功!")
        print(result.stdout)
        return True
    else:
        print("⚠️ Vercel 部署需要手动操作")
        print(f"请手动部署 frontend 目录到 Vercel")
        print("或设置 VERCEL_API_KEY 环境变量")
        return False

def main():
    print("="*60)
    print("🎬 Watermark Remover 部署脚本")
    print("="*60)
    
    # 步骤1: 确保仓库已创建
    create_github_repo()
    
    # 步骤2: 部署后端到 Render
    render_ok = deploy_to_render_via_api()
    
    if not render_ok:
        print("\n⚠️ 请手动完成 Render 部署")
        print(f"GitHub 仓库: https://github.com/{GITHUB_USER}/{REPO_NAME}")
    
    # 步骤3: 部署前端
    deploy_frontend_to_vercel()
    
    print("\n" + "="*60)
    print("📋 部署总结")
    print("="*60)
    print(f"📁 代码仓库: https://github.com/{GITHUB_USER}/{REPO_NAME}")
    print(f"🔧 后端 API: https://watermark-remover-api.onrender.com (部署后)")
    print(f"🌐 前端地址: (需要 Vercel 部署)")
    print("\n如需手动部署，请访问:")
    print("- Render: https://dashboard.render.com")
    print("- Vercel: https://vercel.com")

if __name__ == "__main__":
    main()
