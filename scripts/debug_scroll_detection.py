#!/usr/bin/env python3.11
"""
Debug Scroll Detection Script
============================
This script helps diagnose why scroll distance detection is failing
by analyzing the page structure and scroll behavior.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from playwright.async_api import async_playwright
from src.utils.boundary_scroll_manager import BoundaryScrollManager


async def debug_page_scroll(url: str):
    """Debug the scroll behavior on a specific page"""
    
    print(f"🔍 Debugging Scroll Detection on: {url}")
    print("=" * 60)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Keep visible for debugging
        args=['--disable-blink-features=AutomationControlled']
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080}
    )
    page = await context.new_page()
    
    try:
        # Navigate to the page
        print(f"🌐 Navigating to page...")
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Initialize boundary scroll manager
        manager = BoundaryScrollManager(page)
        
        # STEP 1: Analyze page structure
        print("\n📊 STEP 1: Analyzing page structure...")
        initial_state = await manager.get_scroll_position()
        
        print(f"   Window scroll Y: {initial_state['windowScrollY']}px")
        print(f"   Document scroll top: {initial_state['documentScrollTop']}px")
        print(f"   Body scroll top: {initial_state['bodyScrollTop']}px")
        print(f"   Page height: {initial_state['scrollHeight']}px")
        print(f"   Viewport height: {initial_state['clientHeight']}px")
        print(f"   Generation containers found: {initial_state['containerCount']}")
        
        # Analyze scrollable containers
        scrollable_containers = initial_state.get('scrollableContainers', [])
        print(f"\n   📦 Scrollable containers found: {len(scrollable_containers)}")
        
        for i, container in enumerate(scrollable_containers[:5]):  # Show first 5
            print(f"     {i+1}. {container['tag']}#{container['id']}")
            print(f"        Classes: {container['classes']}")
            print(f"        Scroll: {container['scrollTop']}/{container['scrollHeight']} (can scroll: {container['canScrollMore']})")
            print()
        
        # STEP 2: Test manual scroll and measure
        print("📜 STEP 2: Testing manual scroll measurement...")
        
        input("Press Enter to perform a test scroll (you can also manually scroll to compare)...")
        
        # Get state before manual test
        before_manual = await manager.get_scroll_position()
        
        # Perform a simple scroll test
        await page.evaluate("""
            // Try different scroll methods and report what happens
            console.log('=== SCROLL TEST START ===');
            
            // Method 1: Window scroll
            const initialWindowY = window.scrollY;
            window.scrollBy(0, 500);
            const windowScrolled = window.scrollY - initialWindowY;
            console.log(`Window scroll: ${initialWindowY} -> ${window.scrollY} (${windowScrolled}px)`);
            
            // Method 2: Document element scroll  
            const initialDocY = document.documentElement.scrollTop;
            document.documentElement.scrollTop += 500;
            const docScrolled = document.documentElement.scrollTop - initialDocY;
            console.log(`Document scroll: ${initialDocY} -> ${document.documentElement.scrollTop} (${docScrolled}px)`);
            
            // Method 3: Find and scroll largest container
            const containers = Array.from(document.querySelectorAll('*')).filter(el => {
                try {
                    return el.scrollHeight > el.clientHeight && el.scrollTop >= 0;
                } catch (e) {
                    return false;
                }
            });
            
            containers.sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));
            
            if (containers.length > 0) {
                const container = containers[0];
                const initialContainerY = container.scrollTop;
                container.scrollTop += 500;
                const containerScrolled = container.scrollTop - initialContainerY;
                console.log(`Container scroll (${container.tagName}#${container.id}): ${initialContainerY} -> ${container.scrollTop} (${containerScrolled}px)`);
            }
            
            console.log('=== SCROLL TEST END ===');
        """)
        
        await asyncio.sleep(1)
        
        # Get state after manual test
        after_manual = await manager.get_scroll_position()
        
        # Compare states
        window_change = after_manual['windowScrollY'] - before_manual['windowScrollY']
        doc_change = after_manual['documentScrollTop'] - before_manual['documentScrollTop']
        container_changes = []
        
        before_scrollable = before_manual.get('scrollableContainers', [])
        after_scrollable = after_manual.get('scrollableContainers', [])
        
        for i, after_container in enumerate(after_scrollable):
            if i < len(before_scrollable):
                before_container = before_scrollable[i]
                if (after_container['id'] == before_container['id'] and 
                    after_container['tag'] == before_container['tag']):
                    change = after_container['scrollTop'] - before_container['scrollTop']
                    if change != 0:
                        container_changes.append({
                            'container': f"{after_container['tag']}#{after_container['id']}",
                            'change': change
                        })
        
        print(f"   📊 Measurement Results:")
        print(f"     Window scroll change: {window_change}px")
        print(f"     Document scroll change: {doc_change}px")
        print(f"     Container changes: {len(container_changes)}")
        for change in container_changes:
            print(f"       {change['container']}: {change['change']}px")
        
        # STEP 3: Test our scroll methods
        print("\n🎯 STEP 3: Testing our verified scroll methods...")
        
        input("Press Enter to test Element.scrollIntoView() method...")
        
        result1 = await manager.scroll_method_1_element_scrollintoview(1000)
        print(f"   Primary method result:")
        print(f"     Success: {result1.success}")
        print(f"     Distance measured: {result1.scroll_distance}px")
        print(f"     Containers: {result1.containers_before} -> {result1.containers_after}")
        print(f"     Time: {result1.execution_time:.3f}s")
        
        await asyncio.sleep(2)
        
        input("Press Enter to test container.scrollTop method...")
        
        result2 = await manager.scroll_method_2_container_scrolltop(1000)
        print(f"   Fallback method result:")
        print(f"     Success: {result2.success}")
        print(f"     Distance measured: {result2.scroll_distance}px")
        print(f"     Containers: {result2.containers_before} -> {result2.containers_after}")
        print(f"     Time: {result2.execution_time:.3f}s")
        
        # STEP 4: Analysis and recommendations
        print("\n💡 STEP 4: Analysis and Recommendations")
        print("=" * 50)
        
        if max(window_change, doc_change, max([c['change'] for c in container_changes] + [0])) == 0:
            print("❌ NO SCROLL DETECTED by any method!")
            print("   This suggests the page uses:")
            print("   - Virtual scrolling")
            print("   - Custom scroll implementation") 
            print("   - JavaScript-managed scroll containers")
            print("   - CSS transforms instead of actual scrolling")
        else:
            largest_change = max(
                abs(window_change), 
                abs(doc_change), 
                max([abs(c['change']) for c in container_changes] + [0])
            )
            print(f"✅ SCROLL DETECTED: {largest_change}px")
            
            if window_change != 0:
                print(f"   ✓ Window scrolling works ({window_change}px)")
            if doc_change != 0:
                print(f"   ✓ Document scrolling works ({doc_change}px)")
            if container_changes:
                print(f"   ✓ Container scrolling works:")
                for change in container_changes:
                    print(f"     - {change['container']}: {change['change']}px")
        
        # Check if new containers appeared after our tests
        final_state = await manager.get_scroll_position()
        total_container_change = final_state['containerCount'] - initial_state['containerCount']
        
        if total_container_change > 0:
            print(f"   ✅ NEW CONTAINERS LOADED: {total_container_change} new containers")
            print("   This means scrolling DOES trigger new content loading!")
        else:
            print(f"   ❌ NO NEW CONTAINERS: Still {final_state['containerCount']} containers")
            print("   This means either:")
            print("     - Scrolling doesn't load more content on this page")
            print("     - We haven't scrolled far enough")
            print("     - There's no more content to load")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        input("\nPress Enter to close browser...")
        await browser.close()


if __name__ == "__main__":
    print("🔍 Scroll Detection Debug Tool")
    print("=" * 40)
    
    # Default to the generate page, but allow custom URL
    default_url = "https://wan.video/generate"
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input(f"Enter URL to debug (or press Enter for {default_url}): ").strip()
        if not url:
            url = default_url
    
    asyncio.run(debug_page_scroll(url))