#!/usr/bin/env python3.11
"""
Automated Scroll Detection Script
================================
Non-interactive version to diagnose scroll behavior on wan.video/generate
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from playwright.async_api import async_playwright
from src.utils.boundary_scroll_manager import BoundaryScrollManager


async def automated_scroll_diagnosis(url: str = "https://wan.video/generate"):
    """Automated diagnosis of scroll behavior"""
    
    print(f"🔍 Automated Scroll Analysis: {url}")
    print("=" * 60)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Keep visible to see what's happening
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
        await asyncio.sleep(5)  # Wait for full page load
        
        # Initialize boundary scroll manager
        manager = BoundaryScrollManager(page)
        
        # ANALYSIS 1: Initial page structure
        print("\n📊 ANALYSIS 1: Initial page structure")
        initial_state = await manager.get_scroll_position()
        
        print(f"   Window scroll Y: {initial_state['windowScrollY']}px")
        print(f"   Document scroll top: {initial_state['documentScrollTop']}px") 
        print(f"   Generation containers found: {initial_state['containerCount']}")
        print(f"   Page height: {initial_state['scrollHeight']}px")
        
        scrollable_containers = initial_state.get('scrollableContainers', [])
        print(f"\n   📦 Scrollable containers: {len(scrollable_containers)}")
        
        # Focus on containers that can actually scroll
        main_scrollable = [c for c in scrollable_containers if c['canScrollMore']]
        print(f"   🎯 Can scroll more: {len(main_scrollable)}")
        
        for i, container in enumerate(main_scrollable[:3]):
            print(f"     {i+1}. {container['tag']}#{container['id']}")
            print(f"        Classes: {container['classes'][:50]}...")  # Truncate long class names
            print(f"        Scroll: {container['scrollTop']}/{container['scrollHeight']} (scrollable: {container['scrollHeight']-container['clientHeight']}px)")
        
        # ANALYSIS 2: Test automated scroll methods
        print(f"\n🧪 ANALYSIS 2: Testing scroll methods automatically")
        
        # Test primary method
        print("   Testing Element.scrollIntoView()...")
        result1 = await manager.scroll_method_1_element_scrollintoview(1000)
        print(f"     Success: {result1.success}")
        print(f"     Distance: {result1.scroll_distance}px")
        print(f"     Time: {result1.execution_time:.3f}s")
        print(f"     Containers: {result1.containers_before} → {result1.containers_after}")
        
        await asyncio.sleep(2)
        
        # Test fallback method
        print("   Testing container.scrollTop...")
        result2 = await manager.scroll_method_2_container_scrolltop(1000)
        print(f"     Success: {result2.success}")
        print(f"     Distance: {result2.scroll_distance}px")
        print(f"     Time: {result2.execution_time:.3f}s")
        print(f"     Containers: {result2.containers_before} → {result2.containers_after}")
        
        # ANALYSIS 3: Manual JavaScript scroll test
        print(f"\n🔬 ANALYSIS 3: Direct JavaScript scroll measurement")
        
        # Perform multiple scroll approaches and measure each
        scroll_measurements = await page.evaluate("""
            async () => {
                const measurements = [];
                
                // Method 1: Window scroll
                const initialWindow = window.scrollY;
                window.scrollBy(0, 1000);
                await new Promise(resolve => setTimeout(resolve, 500));
                const windowDistance = window.scrollY - initialWindow;
                measurements.push({
                    method: 'window.scrollBy',
                    distance: windowDistance,
                    final_position: window.scrollY
                });
                
                // Method 2: Document scroll
                const initialDoc = document.documentElement.scrollTop;
                document.documentElement.scrollTop += 1000;
                await new Promise(resolve => setTimeout(resolve, 500));
                const docDistance = document.documentElement.scrollTop - initialDoc;
                measurements.push({
                    method: 'document.documentElement.scrollTop',
                    distance: docDistance,
                    final_position: document.documentElement.scrollTop
                });
                
                // Method 3: Find largest scrollable container and scroll it
                const containers = Array.from(document.querySelectorAll('*')).filter(el => {
                    try {
                        return el.scrollHeight > el.clientHeight && el.scrollTop >= 0;
                    } catch (e) {
                        return false;
                    }
                });
                
                containers.sort((a, b) => 
                    (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight)
                );
                
                if (containers.length > 0) {
                    const container = containers[0];
                    const initialScroll = container.scrollTop;
                    container.scrollTop += 1000;
                    await new Promise(resolve => setTimeout(resolve, 500));
                    const containerDistance = container.scrollTop - initialScroll;
                    
                    measurements.push({
                        method: `container.scrollTop (${container.tagName}#${container.id})`,
                        distance: containerDistance,
                        final_position: container.scrollTop,
                        container_info: {
                            tag: container.tagName,
                            id: container.id || 'none',
                            classes: container.className,
                            scrollHeight: container.scrollHeight,
                            clientHeight: container.clientHeight
                        }
                    });
                }
                
                return measurements;
            }
        """)
        
        print("   JavaScript measurement results:")
        for measurement in scroll_measurements:
            print(f"     📏 {measurement['method']}: {measurement['distance']}px")
            if 'container_info' in measurement:
                info = measurement['container_info']
                print(f"        Container: {info['tag']}#{info['id']}")
                print(f"        Scrollable area: {info['scrollHeight'] - info['clientHeight']}px")
        
        # ANALYSIS 4: Check for generation containers after scrolling
        final_state = await manager.get_scroll_position()
        container_change = final_state['containerCount'] - initial_state['containerCount']
        
        print(f"\n📈 ANALYSIS 4: Content loading analysis")
        print(f"   Initial containers: {initial_state['containerCount']}")
        print(f"   Final containers: {final_state['containerCount']}")
        print(f"   New containers loaded: {container_change}")
        
        # DIAGNOSIS AND RECOMMENDATIONS
        print(f"\n💡 DIAGNOSIS AND RECOMMENDATIONS")
        print("=" * 50)
        
        max_distance = max([m['distance'] for m in scroll_measurements] + [result1.scroll_distance, result2.scroll_distance])
        
        if max_distance == 0:
            print("❌ NO SCROLLING DETECTED")
            print("   ISSUE: Page likely uses:")
            print("     • Virtual scrolling (CSS transforms)")
            print("     • Custom JavaScript scroll handlers")
            print("     • React/Vue virtual list components")
            print("     • Intersection Observer-based loading")
            print("")
            print("   SOLUTION: Need to:")
            print("     • Check for virtual scroll containers")
            print("     • Use element.scrollIntoView() on specific elements")
            print("     • Monitor DOM changes instead of scroll positions")
            print("     • Trigger custom scroll events")
        else:
            print(f"✅ SCROLLING WORKS: {max_distance}px maximum detected")
            
            # Find the best working method
            working_methods = []
            if result1.scroll_distance > 0:
                working_methods.append(f"Element.scrollIntoView: {result1.scroll_distance}px")
            if result2.scroll_distance > 0:
                working_methods.append(f"container.scrollTop: {result2.scroll_distance}px")
            for m in scroll_measurements:
                if m['distance'] > 0:
                    working_methods.append(f"{m['method']}: {m['distance']}px")
            
            print("   ✓ WORKING METHODS:")
            for method in working_methods:
                print(f"     - {method}")
        
        if container_change > 0:
            print(f"   ✅ Content loading works: {container_change} new containers")
        else:
            print(f"   ⚠️  No new content loaded - may need more aggressive scrolling")
        
        print(f"\n⏰ Keeping browser open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(automated_scroll_diagnosis())