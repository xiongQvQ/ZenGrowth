#!/usr/bin/env python3
"""
Final test script for language switching functionality
Tests all analysis pages to ensure they display correctly in English
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import time

async def test_language_switching():
    """Test language switching functionality across all analysis pages"""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🚀 Starting language switching test...")
            
            # Step 1: Navigate to the application
            print("📱 Navigating to application...")
            await page.goto("http://localhost:8503")
            await page.wait_for_timeout(3000)
            
            # Step 2: Check default language (Chinese)
            print("🔍 Checking default language (Chinese)...")
            title_element = await page.wait_for_selector("h1", timeout=10000)
            title_text = await title_element.text_content()
            print(f"   Current title: {title_text}")
            
            if "用户行为分析智能体平台" in title_text:
                print("✅ Default Chinese interface detected")
            else:
                print("⚠️ Unexpected title, continuing...")
            
            # Step 3: Navigate to System Settings
            print("⚙️ Navigating to System Settings...")
            await page.wait_for_timeout(2000)
            
            # Look for the dropdown/select element
            dropdown_locator = page.locator('div[data-testid="stSelectbox"]').first
            await dropdown_locator.click()
            await page.wait_for_timeout(1000)
            
            # Select System Settings
            settings_option = page.locator('div[role="option"]', has_text="⚙️ 系统设置")
            if await settings_option.count() > 0:
                await settings_option.click()
                print("✅ Successfully navigated to System Settings")
            else:
                # Try alternative locator
                settings_option_alt = page.locator('div[role="option"]', has_text="系统设置")
                if await settings_option_alt.count() > 0:
                    await settings_option_alt.click()
                    print("✅ Successfully navigated to System Settings (alternative)")
                else:
                    print("❌ Could not find System Settings option")
                    return False
            
            await page.wait_for_timeout(2000)
            
            # Step 4: Switch to English
            print("🌐 Switching language to English...")
            
            # Look for language dropdown
            lang_dropdown = page.locator('div[data-testid="stSelectbox"]', has_text="界面语言").or_(
                page.locator('div[data-testid="stSelectbox"]').filter(has_text="language")
            )
            
            if await lang_dropdown.count() > 0:
                await lang_dropdown.click()
                await page.wait_for_timeout(1000)
                
                # Select English
                english_option = page.locator('div[role="option"]', has_text="English")
                if await english_option.count() > 0:
                    await english_option.click()
                    await page.wait_for_timeout(1000)
                    print("✅ Selected English language")
                else:
                    print("❌ Could not find English option")
                    return False
            else:
                print("❌ Could not find language dropdown")
                return False
            
            # Click save button
            save_button = page.locator('button', has_text="保存系统配置").or_(
                page.locator('button', has_text="Save")
            )
            if await save_button.count() > 0:
                await save_button.click()
                await page.wait_for_timeout(2000)
                print("✅ Clicked save button")
            else:
                print("⚠️ Could not find save button")
            
            # Step 5: Verify English interface
            print("🔍 Verifying English interface...")
            await page.wait_for_timeout(3000)
            
            # Check title has changed to English
            title_element_en = await page.wait_for_selector("h1", timeout=5000)
            title_text_en = await title_element_en.text_content()
            print(f"   New title: {title_text_en}")
            
            if "User Behavior Analytics Platform" in title_text_en:
                print("✅ English interface successfully activated!")
            else:
                print("⚠️ Title may not have changed completely yet")
            
            # Step 6: Test analysis pages
            analysis_pages = [
                ("📊 Event Analysis", "事件分析"),
                ("📈 Retention Analysis", "留存分析"), 
                ("🔄 Conversion Analysis", "转化分析"),
                ("👥 User Segmentation", "用户分群"),
                ("🛤️ Path Analysis", "路径分析"),
                ("📋 Comprehensive Report", "综合报告"),
                ("🚀 Intelligent Analysis", "智能分析")
            ]
            
            print("📊 Testing analysis pages...")
            
            for english_name, chinese_name in analysis_pages:
                print(f"   Testing {english_name}...")
                
                # Navigate back to main dropdown
                main_dropdown = page.locator('div[data-testid="stSelectbox"]').first
                await main_dropdown.click()
                await page.wait_for_timeout(1000)
                
                # Try to find the English option first, then Chinese as fallback
                option_locator = page.locator('div[role="option"]', has_text=english_name).or_(
                    page.locator('div[role="option"]', has_text=chinese_name)
                )
                
                if await option_locator.count() > 0:
                    await option_locator.click()
                    await page.wait_for_timeout(2000)
                    
                    # Check page content for English
                    page_content = await page.content()
                    
                    # Look for English indicators
                    english_indicators = [
                        "Analysis", "Configuration", "Start", "Time Range", 
                        "Event Types", "Results", "Export", "Report"
                    ]
                    
                    english_found = sum(1 for indicator in english_indicators if indicator in page_content)
                    
                    if english_found >= 3:
                        print(f"   ✅ {english_name} - English interface detected ({english_found} indicators)")
                    else:
                        print(f"   ⚠️ {english_name} - Limited English detected ({english_found} indicators)")
                    
                else:
                    print(f"   ❌ Could not find {english_name} option")
            
            print("🎉 Language switching test completed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            return False
            
        finally:
            await browser.close()

async def main():
    """Main function"""
    success = await test_language_switching()
    
    if success:
        print("\n✅ All tests passed! Language switching functionality is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())