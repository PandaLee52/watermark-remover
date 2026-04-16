#!/usr/bin/env python3
"""
Render 部署脚本 - 简化版
专注于完成关键的部署步骤
"""
import asyncio
import os
from playwright.async_api import async_playwright

GITHUB_USER = "PandaLee52"
REPO_NAME = "watermark-remover"

async def main():
    print("="*60)
    print("🎬 Watermark Remover - Render 部署")
    print("="*60)
    print(f"GitHub: {GITHUB_USER}/{REPO_NAME}")
    print()
    print("请在打开的浏览器中完成以下步骤:")
    print("1. 登录 Render (使用 GitHub)")
    print("2. 点击 'New +' → 'Web Service'")
    print("3. 选择 'watermark-remover' 仓库")
    print("4. 设置配置:")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: gunicorn backend.app:app --bind 0.0.0.0:$PORT")
    print("5. 点击 'Create Web Service'")
    print("6. 等待部署完成")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 直接打开 Render 部署页面
        await page.goto("https://dashboard.render.com/new/web-service")
        await page.wait_for_timeout(3000)
        
        print("浏览器已打开，请在浏览器中完成部署...")
        print("按 Enter 关闭浏览器...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
