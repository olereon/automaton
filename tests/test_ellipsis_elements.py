#!/usr/bin/env python3
"""
Test script to find the shortest elements containing ellipsis "..." on the generation gallery page.
This helps identify where the full prompt text might be truncated or hidden.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from playwright.async_api import async_playwright

async def find_ellipsis_elements():
    """Find all elements containing ellipsis and identify the shortest ones"""
    
    print("🔍 Ellipsis Element Finder")
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
            # Navigate to the generation page
            print("🌐 Navigating to wan.video/generate...")
            await page.goto("https://wan.video/generate", timeout=30000)
            
            # Login (using the same credentials as the demo)
            print("🔑 Logging in...")
            await page.fill('input[placeholder="Email address"]', 'shyraoleg@outlook.com')
            await page.fill('input[type="password"]', 'Wanv!de025')
            await page.click('button:has-text("Log in")[type="submit"]')
            
            # Wait for page to load after login
            await page.wait_for_timeout(5000)
            
            # Navigate to completed tasks (same as generation download automation)
            print("📱 Navigating to completed tasks page (9th item)...")
            try:
                # Use the same selector as the automation: "div[id$='__9']"
                completed_task_selector = "div[id$='__9']"
                print(f"🎯 Clicking selector: {completed_task_selector}")
                
                await page.click(completed_task_selector, timeout=15000)
                await page.wait_for_timeout(3000)  # Wait for page to load
                print("✅ Successfully navigated to completed tasks page")
                
                # Wait for thumbnails to load (same as automation)
                thumbnail_selector = ".thumsItem, .thumbnail-item"
                await page.wait_for_selector(thumbnail_selector, timeout=15000)
                
                # Check how many thumbnails we found
                thumbnails = await page.query_selector_all(thumbnail_selector)
                print(f"📸 Found {len(thumbnails)} thumbnail elements after navigation")
                
            except Exception as e:
                print(f"❌ Error navigating to completed tasks: {e}")
                print("🔄 Continuing with current page...")
            
            print("🔍 Searching for elements containing ellipsis '...'")
            
            # Find all elements containing ellipsis using XPath
            # This finds elements that contain "..." as text content
            ellipsis_elements = await page.query_selector_all("//*[contains(text(), '...')]")
            
            print(f"📦 Found {len(ellipsis_elements)} elements containing ellipsis")
            print()
            
            # Analyze each element to find the shortest ones (no nested elements)
            shortest_elements = []
            
            for i, element in enumerate(ellipsis_elements):
                try:
                    # Get element details
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    text_content = await element.text_content()
                    inner_html = await element.inner_html()
                    
                    # Check if this is a leaf element (no nested HTML tags)
                    has_nested_tags = '<' in inner_html and '>' in inner_html
                    
                    # Get element class and other attributes
                    class_name = await element.get_attribute('class') or 'no-class'
                    element_id = await element.get_attribute('id') or 'no-id'
                    
                    # Check visibility
                    is_visible = await element.is_visible()
                    
                    element_info = {
                        'index': i,
                        'tag': tag_name,
                        'text': text_content.strip() if text_content else '',
                        'text_length': len(text_content.strip()) if text_content else 0,
                        'html_length': len(inner_html),
                        'has_nested_tags': has_nested_tags,
                        'class': class_name,
                        'id': element_id,
                        'visible': is_visible,
                        'inner_html': inner_html[:200] + ('...' if len(inner_html) > 200 else '')
                    }
                    
                    # Only consider leaf elements (no nested tags) that are visible
                    if not has_nested_tags and is_visible and text_content:
                        shortest_elements.append(element_info)
                    
                    # Show all elements for debugging
                    print(f"Element {i+1}:")
                    print(f"  Tag: {tag_name}")
                    print(f"  Class: {class_name}")
                    print(f"  Visible: {is_visible}")
                    print(f"  Has nested tags: {has_nested_tags}")
                    print(f"  Text length: {len(text_content.strip()) if text_content else 0}")
                    print(f"  Text: '{(text_content.strip() if text_content else '')[:100]}{'...' if text_content and len(text_content.strip()) > 100 else ''}'")
                    print(f"  HTML: {inner_html[:150]}{'...' if len(inner_html) > 150 else ''}")
                    print()
                    
                except Exception as e:
                    print(f"  Error processing element {i}: {e}")
                    continue
            
            # Sort shortest elements by text length
            shortest_elements.sort(key=lambda x: x['text_length'])
            
            print("\n🎯 SHORTEST LEAF ELEMENTS (no nested tags, visible only):")
            print("=" * 80)
            
            if shortest_elements:
                for elem in shortest_elements[:10]:  # Show top 10 shortest
                    print(f"#{elem['index']+1} - {elem['tag']}.{elem['class']}")
                    print(f"  Text ({elem['text_length']} chars): '{elem['text'][:200]}{'...' if len(elem['text']) > 200 else ''}'")
                    print(f"  HTML: {elem['inner_html']}")
                    print()
            else:
                print("❌ No leaf elements with ellipsis found!")
            
            print(f"\n📊 SUMMARY:")
            print(f"  Total ellipsis elements: {len(ellipsis_elements)}")
            print(f"  Leaf elements (no nested tags): {len(shortest_elements)}")
            
            # Also search specifically for spans with aria-describedby
            print("\n🔍 CHECKING SPANS WITH aria-describedby:")
            aria_spans = await page.query_selector_all("span[aria-describedby]")
            print(f"Found {len(aria_spans)} span elements with aria-describedby")
            
            for i, span in enumerate(aria_spans):
                try:
                    text = await span.text_content()
                    aria_value = await span.get_attribute('aria-describedby')
                    class_name = await span.get_attribute('class') or 'no-class'
                    is_visible = await span.is_visible()
                    
                    print(f"  Span {i+1}: class='{class_name}' aria-describedby='{aria_value}' visible={is_visible}")
                    print(f"    Text ({len(text) if text else 0} chars): '{(text or '')[:150]}{'...' if text and len(text) > 150 else ''}'")
                    
                    # If this span contains ellipsis, highlight it
                    if text and '...' in text:
                        print(f"    🎯 CONTAINS ELLIPSIS!")
                    
                    print()
                except Exception as e:
                    print(f"    Error: {e}")
            
            print("\n✅ Analysis complete. Browser will stay open for manual inspection.")
            print("Press Ctrl+C to exit...")
            
            # Keep browser open for manual inspection
            await asyncio.sleep(3600)  # Wait 1 hour or until interrupted
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            await browser.close()

def main():
    """Main entry point"""
    try:
        asyncio.run(find_ellipsis_elements())
    except KeyboardInterrupt:
        print("\n🛑 Script interrupted")
    except Exception as e:
        print(f"\n💥 Error: {e}")

if __name__ == "__main__":
    main()