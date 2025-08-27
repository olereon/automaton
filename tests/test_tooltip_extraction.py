#!/usr/bin/env python3
"""
Test script to investigate tooltip/hover mechanisms for extracting full prompt text.
Based on the finding that spans contain only 103 chars, but Element 31 showed 325 chars.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from playwright.async_api import async_playwright

async def test_tooltip_mechanisms():
    """Test various methods to extract full prompt text from tooltips"""
    
    print("🔍 Tooltip/Hover Text Extraction Test")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch browser with same settings as automation
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--window-size=2560,1080"
            ]
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        
        try:
            # Navigate and login (same as other tests)
            print("🌐 Navigating to wan.video/generate...")
            await page.goto("https://wan.video/generate", timeout=30000)
            
            print("🔑 Logging in...")
            await page.fill('input[placeholder="Email address"]', 'shyraoleg@outlook.com')
            await page.fill('input[type="password"]', 'Wanv!de025')
            await page.click('button:has-text("Log in")[type="submit"]')
            await page.wait_for_timeout(5000)
            
            # Navigate to completed tasks
            print("📱 Navigating to completed tasks page...")
            await page.click("div[id$='__9']", timeout=15000)
            await page.wait_for_timeout(3000)
            await page.wait_for_selector(".thumsItem, .thumbnail-item", timeout=15000)
            
            # Find the first prompt span to test on
            print("🎯 Finding first prompt span...")
            prompt_spans = await page.query_selector_all("span[aria-describedby]")
            
            test_span = None
            for span in prompt_spans:
                text = await span.text_content()
                if text and len(text) > 50 and 'camera' in text.lower():
                    test_span = span
                    break
            
            if not test_span:
                print("❌ No suitable test span found")
                return
            
            aria_id = await test_span.get_attribute('aria-describedby')
            print(f"🔍 Testing span with aria-describedby='{aria_id}'")
            
            # Get initial text
            initial_text = await test_span.text_content()
            print(f"📝 Initial text ({len(initial_text)} chars): {initial_text}")
            
            # METHOD 1: Look for tooltip element using aria-describedby
            print(f"\n🔍 METHOD 1: Looking for tooltip element with id='{aria_id}'")
            try:
                tooltip_element = await page.query_selector(f"#{aria_id}")
                if tooltip_element:
                    tooltip_text = await tooltip_element.text_content()
                    tooltip_visible = await tooltip_element.is_visible()
                    print(f"✅ Found tooltip element: visible={tooltip_visible}")
                    print(f"📝 Tooltip text ({len(tooltip_text) if tooltip_text else 0} chars): {tooltip_text[:200]}...")
                else:
                    print("❌ No tooltip element found with that ID")
            except Exception as e:
                print(f"❌ Error finding tooltip: {e}")
            
            # METHOD 2: Hover over span to reveal tooltip
            print(f"\n🔍 METHOD 2: Hovering over span to reveal tooltip")
            try:
                # Hover over the span
                await test_span.hover()
                await page.wait_for_timeout(1000)  # Wait for tooltip to appear
                
                # Check if tooltip appeared
                tooltip_element = await page.query_selector(f"#{aria_id}")
                if tooltip_element:
                    tooltip_visible = await tooltip_element.is_visible()
                    if tooltip_visible:
                        tooltip_text = await tooltip_element.text_content()
                        print(f"✅ Tooltip appeared on hover!")
                        print(f"📝 Hovered tooltip text ({len(tooltip_text) if tooltip_text else 0} chars): {tooltip_text}")
                    else:
                        print("⚠️ Tooltip element exists but not visible after hover")
                else:
                    print("❌ No tooltip appeared after hover")
                
                # Check if the span text itself changed after hover
                span_text_after_hover = await test_span.text_content()
                if span_text_after_hover != initial_text:
                    print(f"📝 Span text changed after hover ({len(span_text_after_hover)} chars): {span_text_after_hover}")
                else:
                    print("📝 Span text unchanged after hover")
                    
            except Exception as e:
                print(f"❌ Error during hover test: {e}")
            
            # METHOD 3: Check for tooltip/popover elements anywhere on page
            print(f"\n🔍 METHOD 3: Searching for tooltip/popover elements")
            tooltip_selectors = [
                "[role='tooltip']",
                ".tooltip",
                ".popover", 
                "[data-tooltip]",
                ".ant-tooltip",
                "[aria-live]"
            ]
            
            for selector in tooltip_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"📦 Found {len(elements)} elements with selector: {selector}")
                        for i, elem in enumerate(elements[:3]):  # Check first 3
                            text = await elem.text_content()
                            visible = await elem.is_visible()
                            print(f"  Element {i+1}: visible={visible}, text={len(text or '')} chars: '{(text or '')[:100]}...'")
                except Exception as e:
                    print(f"❌ Error with selector {selector}: {e}")
            
            # METHOD 4: Click on span to see if it expands
            print(f"\n🔍 METHOD 4: Clicking span to test expansion")
            try:
                await test_span.click()
                await page.wait_for_timeout(1000)
                
                # Check if text expanded
                expanded_text = await test_span.text_content()
                if len(expanded_text) > len(initial_text):
                    print(f"🎉 SUCCESS! Text expanded after click!")
                    print(f"📝 Expanded text ({len(expanded_text)} chars): {expanded_text}")
                else:
                    print("📝 No expansion after click")
                    
            except Exception as e:
                print(f"❌ Error during click test: {e}")
            
            # METHOD 5: Check Element 31 specifically (the 325-char one from previous test)
            print(f"\n🔍 METHOD 5: Looking for the 325-character element from previous test")
            all_divs = await page.query_selector_all("div.sc-dDrhAi.dnESm")
            print(f"📦 Found {len(all_divs)} prompt divs")
            
            longest_text = ""
            longest_length = 0
            
            for i, div in enumerate(all_divs):
                try:
                    div_text = await div.text_content()
                    if div_text and len(div_text) > longest_length:
                        longest_length = len(div_text)
                        longest_text = div_text
                        print(f"  Div {i+1}: {len(div_text)} chars")
                except:
                    pass
            
            if longest_length > 200:
                print(f"🎉 Found longer text ({longest_length} chars)!")
                print(f"📝 Longest text: {longest_text}")
            else:
                print(f"📝 Longest found: {longest_length} chars")
            
            print(f"\n✅ Test complete. Browser staying open for manual inspection.")
            print("Press Ctrl+C to exit...")
            
            # Keep browser open for manual inspection
            await asyncio.sleep(3600)
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            await browser.close()

def main():
    """Main entry point"""
    try:
        asyncio.run(test_tooltip_mechanisms())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted")
    except Exception as e:
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main()