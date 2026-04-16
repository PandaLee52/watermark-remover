#!/usr/bin/env python3
"""
Watermark Remover - Render 自动部署脚本
"""
import asyncio
import os
import sys
from playwright.async_api import async_playwright

# 配置
GITHUB_USER = "PandaLee52"
REPO_NAME = "watermark-remover"
PROJECT_DIR = "watermark-remover"

SCREENSHOT_DIR = "./render_deploy_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def save_screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/{name}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"   📸 截图: {path}")
    return path

async def click_by_text(page, text_pattern, timeout=5000):
    """通过文本点击元素"""
    try:
        # 尝试多种选择器
        selectors = [
            f'text="{text_pattern}"',
            f'button:has-text("{text_pattern}")',
            f'a:has-text("{text_pattern}")',
            f'span:has-text("{text_pattern}")'
        ]
        for sel in selectors:
            try:
                elem = page.locator(sel).first
                if await elem.is_visible(timeout=2000):
                    await elem.click(timeout=5000)
                    print(f"   ✅ 点击成功: {sel}")
                    return True
            except:
                continue
        return False
    except Exception as e:
        print(f"   ⚠️ 点击失败: {e}")
        return False

async def deploy_to_render():
    """部署到 Render"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(viewport={'width': 1400, 'height': 900})
        page = await context.new_page()
        
        try:
            print("=" * 60)
            print("🚀 开始 Render 部署")
            print("=" * 60)
            
            # Step 1: 访问 Render
            print("\n[Step 1] 访问 Render...")
            await page.goto("https://dashboard.render.com", timeout=60000)
            await page.wait_for_load_state("networkidle")
            await save_screenshot(page, "01_render_dashboard")
            
            # 检查是否已登录
            if "login" in page.url:
                print("\n⚠️ 需要登录 Render")
                print("请在浏览器中完成 GitHub 登录")
                print("登录完成后按回车继续...")
                input()
            
            await save_screenshot(page, "02_after_login")
            
            # Step 2: 点击 New +
            print("\n[Step 2] 点击 New + ...")
            await page.click('button:has-text("New")', timeout=5000)
            await page.wait_for_timeout(1000)
            
            # Step 3: 选择 Web Service
            print("\n[Step 3] 选择 Web Service...")
            await page.click('text="Web Service"', timeout=5000)
            await page.wait_for_load_state("networkidle")
            await save_screenshot(page, "03_connect_github")
            
            # Step 4: 等待加载 GitHub 仓库列表
            print("\n[Step 4] 等待 GitHub 仓库列表...")
            await page.wait_for_timeout(3000)
            await save_screenshot(page, "04_github_repos")
            
            # 查找仓库
            print("\n[Step 5] 查找仓库...")
            repo_found = False
            try:
                # 尝试直接搜索
                search_box = page.locator('input[placeholder*="Search"], input[type="search"]').first
                if await search_box.is_visible(timeout=3000):
                    await search_box.fill(REPO_NAME)
                    await page.wait_for_timeout(2000)
                    await save_screenshot(page, "05_search_result")
            except:
                pass
            
            # 滚动查找仓库
            repo_selectors = [
                f'text="{REPO_NAME}"',
                f'text="{GITHUB_USER}/{REPO_NAME}"',
                f'a:has-text("{REPO_NAME}")'
            ]
            
            for sel in repo_selectors:
                try:
                    repo_link = page.locator(sel).first
                    if await repo_link.is_visible(timeout=3000):
                        await repo_link.click()
                        repo_found = True
                        print(f"   ✅ 找到仓库并点击")
                        break
                except:
                    continue
            
            await page.wait_for_load_state("networkidle")
            await save_screenshot(page, "06_repo_selected")
            
            # Step 5: 配置部署
            print("\n[Step 6] 配置部署...")
            await page.wait_for_timeout(2000)
            
            # 设置构建命令
            build_input = page.locator('input[name="buildCommand"], #buildCommand, input[placeholder*="Build"]').first
            if await build_input.is_visible(timeout=3000):
                await build_input.clear()
                await build_input.fill("pip install -r requirements.txt")
            
            # 设置启动命令
            start_input = page.locator('input[name="startCommand"], #startCommand, input[placeholder*="Start"]').first
            if await start_input.is_visible(timeout=3000):
                await start_input.clear()
                await start_input.fill("gunicorn backend.app:app --bind 0.0.0.0:$PORT")
            
            await save_screenshot(page, "07_configured")
            
            # Step 6: 点击 Create Web Service
            print("\n[Step 7] 创建 Web Service...")
            await page.click('button:has-text("Create Web Service")', timeout=5000)
            await page.wait_for_timeout(5000)
            
            await save_screenshot(page, "08_creating")
            
            # 等待部署
            print("\n[Step 8] 等待部署...")
            for i in range(30):
                await page.wait_for_timeout(10000)
                await save_screenshot(page, f"09_deploying_{i+1}")
                
                # 检查是否完成
                try:
                    status = page.locator('text="Live"').first
                    if await status.is_visible(timeout=2000):
                        print("   ✅ 部署完成!")
                        break
                    
                    error = page.locator('text="Failed"').first
                    if await error.is_visible(timeout=2000):
                        print("   ⚠️ 部署失败")
                        break
                except:
                    pass
                
                print(f"   等待部署中... ({i+1}/30)")
            
            await save_screenshot(page, "10_final")
            
            # 获取 URL
            url = page.url
            print(f"\n   部署URL: {url}")
            
            return True
            
        except Exception as e:
            print(f"\n⚠️ 部署过程中出错: {e}")
            await save_screenshot(page, "error")
            return False
        finally:
            await browser.close()

async def main():
    print("="*60)
    print("🎬 Watermark Remover - Render 部署脚本")
    print("="*60)
    print(f"\nGitHub 仓库: {GITHUB_USER}/{REPO_NAME}")
    print("-"*60)
    
    await deploy_to_render()
    
    print("\n" + "="*60)
    print("📋 下一步")
    print("="*60)
    print("1. 访问 Render Dashboard 检查部署状态")
    print("2. 如果部署成功，更新前端 API 地址")
    print("3. 部署前端到 Vercel")

if __name__ == "__main__":
    asyncio.run(main())
