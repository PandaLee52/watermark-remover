#!/usr/bin/env python3
"""
Watermark Remover - Render 自动部署脚本 v2
增强版，更稳定
"""
import asyncio
import os
import time
from playwright.async_api import async_playwright

# 配置
GITHUB_USER = "PandaLee52"
REPO_NAME = "watermark-remover"
PROJECT_DIR = "watermark-remover"

SCREENSHOT_DIR = "./render_deploy_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def save_screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/{name}.png"
    try:
        await page.screenshot(path=path, full_page=True)
        print(f"   📸 截图: {path}")
    except Exception as e:
        print(f"   ⚠️ 截图失败: {e}")
    return path

async def try_click(page, selectors, timeout=5000):
    """尝试多种选择器点击"""
    for sel in selectors:
        try:
            elem = page.locator(sel).first
            if await elem.is_visible(timeout=2000):
                await elem.click(timeout=5000)
                print(f"   ✅ 点击: {sel}")
                return True
        except Exception as e:
            continue
    return False

async def deploy_to_render():
    """部署到 Render"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={'width': 1400, 'height': 900},
            ignore_https_errors=True
        )
        page = await context.new_page()
        
        try:
            print("=" * 60)
            print("🚀 开始 Render 部署")
            print("=" * 60)
            
            # Step 1: 访问 Render 登录页
            print("\n[Step 1] 访问 Render...")
            try:
                await page.goto("https://dashboard.render.com/login", timeout=60000)
            except Exception as e:
                print(f"   ⚠️ 访问超时: {e}")
                await save_screenshot(page, "01_timeout")
                return False
            
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            await save_screenshot(page, "01_render_login")
            
            print(f"   当前URL: {page.url}")
            
            # Step 2: 检查是否需要登录
            if "login" in page.url.lower():
                print("\n⚠️ 需要登录")
                print("请在浏览器中完成 GitHub 登录...")
                print("登录后按 Enter 继续...")
                input()
            
            await save_screenshot(page, "02_after_login")
            
            # Step 3: 点击 New +
            print("\n[Step 2] 点击 New + ...")
            await page.wait_for_timeout(2000)
            
            new_selectors = [
                'button:has-text("New")',
                '[aria-label="New"]',
                'a:has-text("New")',
                'button[data-testid="new-button"]'
            ]
            await try_click(page, new_selectors)
            await page.wait_for_timeout(1500)
            
            # Step 4: 选择 Web Service
            print("\n[Step 3] 选择 Web Service...")
            web_selectors = [
                'text="Web Service"',
                'a:has-text("Web Service")',
                'button:has-text("Web Service")',
                '[data-testid="web-service"]'
            ]
            await try_click(page, web_selectors)
            await page.wait_for_load_state("networkidle", timeout=30000)
            await save_screenshot(page, "03_web_service")
            
            # Step 5: 等待 GitHub 连接
            print("\n[Step 4] 等待 GitHub 仓库列表...")
            await page.wait_for_timeout(5000)
            await save_screenshot(page, "04_github_list")
            
            # Step 6: 查找并选择仓库
            print("\n[Step 5] 查找仓库...")
            
            # 尝试搜索
            try:
                search = page.locator('input[type="search"], input[placeholder*="earch"], input[placeholder*="仓库"]').first
                if await search.is_visible(timeout=3000):
                    await search.fill(REPO_NAME)
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            await save_screenshot(page, "05_search")
            
            # 选择仓库
            repo_selectors = [
                f'text="{REPO_NAME}"',
                f'text="{GITHUB_USER}/{REPO_NAME}"',
                f'a:has-text("{REPO_NAME}")',
                f'button:has-text("{REPO_NAME}")'
            ]
            
            repo_found = await try_click(page, repo_selectors)
            
            if not repo_found:
                print("   ⚠️ 未找到仓库，尝试滚动...")
                for _ in range(5):
                    await page.keyboard.press("End")
                    await page.wait_for_timeout(500)
                    repo_found = await try_click(page, repo_selectors)
                    if repo_found:
                        break
            
            await page.wait_for_load_state("networkidle", timeout=30000)
            await save_screenshot(page, "06_repo_selected")
            
            # Step 7: 配置部署
            print("\n[Step 6] 配置部署...")
            await page.wait_for_timeout(3000)
            
            # 填写配置
            try:
                # Build Command
                build = page.locator('#buildCommand, [name="buildCommand"], input[placeholder*="Build"]').first
                if await build.is_visible(timeout=2000):
                    await build.clear()
                    await build.fill("pip install -r requirements.txt")
                    print("   ✅ 设置 Build Command")
                
                # Start Command
                start = page.locator('#startCommand, [name="startCommand"], input[placeholder*="Start"]').first
                if await start.is_visible(timeout=2000):
                    await start.clear()
                    await start.fill("gunicorn backend.app:app --bind 0.0.0.0:$PORT")
                    print("   ✅ 设置 Start Command")
            except Exception as e:
                print(f"   ⚠️ 配置填写: {e}")
            
            await save_screenshot(page, "07_configured")
            
            # Step 8: 创建 Web Service
            print("\n[Step 7] 创建 Web Service...")
            create_selectors = [
                'button:has-text("Create Web Service")',
                'button:has-text("Create")',
                'button[type="submit"]'
            ]
            await try_click(page, create_selectors)
            
            await page.wait_for_timeout(5000)
            await save_screenshot(page, "08_creating")
            
            # Step 9: 等待部署
            print("\n[Step 8] 等待部署 (最多5分钟)...")
            for i in range(30):
                await page.wait_for_timeout(10000)
                
                await save_screenshot(page, f"09_deploy_{i+1}")
                
                # 检查状态
                try:
                    url = page.url
                    print(f"   当前URL: {url}")
                    
                    # 检查是否有错误
                    error_elem = page.locator('text="Failed"').first
                    if await error_elem.is_visible(timeout=1000):
                        print("   ⚠️ 检测到部署失败")
                        await save_screenshot(page, "10_failed")
                        break
                    
                    # 检查是否成功
                    live_elem = page.locator('text="Live"').first
                    if await live_elem.is_visible(timeout=1000):
                        print("   ✅ 部署成功!")
                        await save_screenshot(page, "10_live")
                        break
                    
                except:
                    pass
                
                print(f"   等待中... ({i+1}/30)")
            
            print(f"\n   最终URL: {page.url}")
            
        except Exception as e:
            print(f"\n⚠️ 错误: {e}")
            await save_screenshot(page, "error")
            return False
        finally:
            await browser.close()
        
        return True

async def main():
    print("="*60)
    print("🎬 Watermark Remover - Render 部署")
    print("="*60)
    print(f"GitHub: {GITHUB_USER}/{REPO_NAME}")
    print("-"*60)
    
    success = await deploy_to_render()
    
    print("\n" + "="*60)
    if success:
        print("✅ 部署流程完成!")
    else:
        print("⚠️ 请手动完成部署")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
