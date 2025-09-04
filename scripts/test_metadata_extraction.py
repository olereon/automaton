#!/usr/bin/env python3
"""
Test script to debug metadata extraction in gallery view
"""

import asyncio
from playwright.async_api import async_playwright
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

async def test_metadata_extraction():
    """Test metadata extraction from gallery thumbnails"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=DownloadShelf,DownloadBubble,DownloadBubbleV2',
            ]
        )
        
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        print("📋 Manual steps:")
        print("1. Navigate to https://wan.video/generate")
        print("2. Login if needed")
        print("3. Click on a completed generation to enter gallery")
        print("4. Press Enter when ready...")
        input()
        
        # Test clicking on a thumbnail and extracting metadata
        print("\n🔍 Testing metadata extraction...")
        
        # Click on the first thumbnail
        thumbnails = await page.query_selector_all('.thumsItem, .thumbnail-item')
        if thumbnails:
            print(f"Found {len(thumbnails)} thumbnails")
            
            # Click first thumbnail
            await thumbnails[0].click()
            print("✅ Clicked first thumbnail")
            
            # Wait for metadata to appear
            await page.wait_for_timeout(2000)
            
            # Try various selectors for Creation Time
            print("\n📅 Testing Creation Time selectors:")
            time_selectors = [
                ".sc-bYXhga.jGymgu .sc-jxKUFb.bZTHAM:last-child",
                "xpath=//span[text()='Creation Time']/following-sibling::span",
                ".sc-jxKUFb.bZTHAM:last-child",
                "span:has-text('Creation Time') + span",
                ".sc-bYXhga.jGymgu span:last-child",
                "xpath=//div[contains(@class, 'jGymgu')]//span[last()]",
                "xpath=//span[contains(@class, 'bZTHAM')][last()]"
            ]
            
            for selector in time_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=100):
                        text = await element.text_content()
                        print(f"  ✅ {selector[:50]}... = '{text}'")
                except:
                    print(f"  ❌ {selector[:50]}... - Not found")
            
            # Try various selectors for Prompt
            print("\n📝 Testing Prompt selectors:")
            prompt_selectors = [
                ".sc-dDrhAi.dnESm span:first-child",
                "xpath=//div[contains(@class, 'dnESm')]//span[1]",
                ".sc-dDrhAi.dnESm span",
                ".sc-jJRqov.cxtNJi span[aria-describedby]",
                "div.sc-dDrhAi.dnESm",
                "[class*='prompt'] span",
                "xpath=//span[@aria-describedby]"
            ]
            
            for selector in prompt_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible(timeout=100):
                        text = await element.text_content()
                        print(f"  ✅ {selector[:50]}... = '{text[:50]}...'")
                except:
                    print(f"  ❌ {selector[:50]}... - Not found")
            
            # Try to find all text containing "Creation Time"
            print("\n🔎 Looking for all elements with 'Creation Time':")
            all_elements = await page.query_selector_all("*")
            for element in all_elements:
                try:
                    text = await element.text_content()
                    if text and "Creation Time" in text:
                        tag = await element.evaluate("el => el.tagName")
                        classes = await element.get_attribute("class")
                        print(f"  Found in <{tag}> with classes: {classes}")
                        print(f"    Text: {text[:100]}")
                except:
                    pass
            
        else:
            print("❌ No thumbnails found")
        
        print("\n📋 Press Enter to close browser...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_metadata_extraction())