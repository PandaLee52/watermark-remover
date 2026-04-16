#!/usr/bin/env python3
"""
Render 自动部署脚本 - 完全自动化版本
使用 Render API 进行部署
"""
import os
import sys
import time
import requests
import json

# 配置
GITHUB_USER = "PandaLee52"
REPO_NAME = "watermark-remover"

RENDER_API_KEY = os.environ.get('RENDER_API_KEY', '')

def check_api_key():
    """检查 API Key"""
    if not RENDER_API_KEY:
        print("❌ RENDER_API_KEY 环境变量未设置")
        print()
        print("请设置 RENDER_API_KEY:")
        print("1. 访问 https://dashboard.render.com/api-keys")
        print("2. 点击 'Create API Key'")
        print("3. 复制生成的 API Key")
        print("4. 设置环境变量:")
        print("   export RENDER_API_KEY='your-api-key-here'")
        return False
    return True

def get_headers():
    """获取请求头"""
    return {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def create_blueprint():
    """使用 Blueprint 创建服务"""
    blueprint = {
        "github": {
            "repo": f"{GITHUB_USER}/{REPO_NAME}"
        },
        "services": [
            {
                "name": "watermark-remover-api",
                "type": "web",
                "env": "python",
                "region": "singapore",
                "plan": "free",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "gunicorn backend.app:app --bind 0.0.0.0:$PORT",
                "autoDeploy": True
            }
        ]
    }
    
    return blueprint

def deploy_via_api():
    """通过 API 部署"""
    print("=" * 60)
    print("🚀 Watermark Remover - Render API 部署")
    print("=" * 60)
    
    if not check_api_key():
        print()
        print("⚠️ 无法自动部署，请选择以下方案之一:")
        print()
        print("方案 1: 手动部署")
        print("   1. 访问 https://dashboard.render.com")
        print("   2. 点击 'New +' → 'Web Service'")
        print("   3. 选择 'watermark-remover' 仓库")
        print("   4. 配置:")
        print("      - Build Command: pip install -r requirements.txt")
        print("      - Start Command: gunicorn backend.app:app --bind 0.0.0.0:$PORT")
        print("   5. 点击 'Create Web Service'")
        print()
        print("方案 2: 使用 Railway")
        print("   npm install -g @railway/cli")
        print("   railway login")
        print("   cd watermark-remover && railway up")
        print()
        return False
    
    print(f"\n✅ API Key 已设置")
    print(f"   正在连接 Render API...")
    
    # 检查现有服务
    try:
        response = requests.get(
            "https://api.render.com/v1/services",
            headers=get_headers()
        )
        
        if response.status_code == 200:
            services = response.json()
            for svc in services:
                if svc.get('name') == 'watermark-remover-api':
                    print(f"\n⚠️ 服务 'watermark-remover-api' 已存在")
                    print(f"   正在触发重新部署...")
                    
                    # 触发部署
                    service_id = svc.get('id')
                    deploy_response = requests.post(
                        f"https://api.render.com/v1/services/{service_id}/deploys",
                        headers=get_headers()
                    )
                    
                    if deploy_response.status_code == 200:
                        print("✅ 部署已触发!")
                        print(f"   访问 https://dashboard.render.com 检查状态")
                        return True
        
        print(f"\n📦 正在创建新服务...")
        
        # 使用 Blueprint 创建
        blueprint = create_blueprint()
        
        response = requests.post(
            "https://api.render.com/v1/blueprints",
            headers=get_headers(),
            json=blueprint
        )
        
        if response.status_code in [200, 201]:
            print("✅ Blueprint 创建成功!")
            data = response.json()
            print(f"   访问 https://dashboard.render.com 查看服务")
            
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    if item.get('type') == 'web':
                        print(f"\n   服务详情:")
                        print(f"   - Name: {item.get('name')}")
                        print(f"   - Status: {item.get('status')}")
            
            return True
        else:
            print(f"❌ Blueprint 创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API 请求失败: {e}")
        return False

if __name__ == "__main__":
    deploy_via_api()
