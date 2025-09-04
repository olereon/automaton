#!/usr/bin/env python3.11
"""
Comprehensive Scroll Diagnosis with Login
=========================================
Tests scroll detection on actual generation gallery after login.
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


async def comprehensive_scroll_diagnosis():
    """Comprehensive diagnosis with login and real gallery content"""
    
    print(f"🔍 Comprehensive Scroll Diagnosis with Login")
    print("=" * 60)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Keep visible to see what's happening
        args=['--disable-blink-features=AutomationControlled']
    )
    
    context = await browser.new_context(
        viewport={'width': 2560, 'height': 1440}
    )
    page = await context.new_page()
    
    try:
        # STEP 1: Navigate and login
        print(f"🌐 STEP 1: Navigating to page and logging in...")
        await page.goto("https://wan.video/generate", wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Simple login
        try:
            await page.fill('input[placeholder="Email address"]', 'shyraoleg@outlook.com')
            await page.fill('input[type="password"]', 'Wanv!de025')
            await page.click('button:has-text("Log in")[type="submit"]')
            print("   ✓ Login attempted")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"   ⚠️  Login may have failed: {e}")
        
        # STEP 2: Wait for content to load and analyze
        print(f"\n📊 STEP 2: Analyzing page structure after login...")
        await asyncio.sleep(5)  # Wait for generation gallery to load
        
        # Initialize boundary scroll manager
        manager = BoundaryScrollManager(page)
        initial_state = await manager.get_scroll_position()
        
        print(f"   Window scroll Y: {initial_state['windowScrollY']}px")
        print(f"   Document scroll top: {initial_state['documentScrollTop']}px") 
        print(f"   Generation containers found: {initial_state['containerCount']}")
        print(f"   Page height: {initial_state['scrollHeight']}px")
        print(f"   Viewport height: {initial_state['clientHeight']}px")
        
        scrollable_containers = initial_state.get('scrollableContainers', [])
        main_scrollable = [c for c in scrollable_containers if c['canScrollMore']]
        print(f"   📦 Scrollable containers: {len(scrollable_containers)} ({len(main_scrollable)} can scroll)")
        
        # Show the most promising scrollable containers
        for i, container in enumerate(main_scrollable[:3]):
            scrollable_px = container['scrollHeight'] - container['clientHeight']
            print(f"     {i+1}. {container['tag']}#{container['id']}")
            print(f"        Classes: {container['classes'][:80]}...")
            print(f"        Can scroll: {scrollable_px}px (current: {container['scrollTop']})")
        
        # STEP 3: Look for generation containers specifically
        print(f"\n🎯 STEP 3: Searching for generation containers...")
        
        generation_containers = await page.evaluate("""
            () => {
                // Try multiple selectors for generation containers
                const selectors = [
                    '.thumsItem',           // From config
                    '.thumbnail-item',      // Common pattern
                    '[data-generation-id]', // If they exist
                    '.generation-card',     // Common pattern
                    '[class*="thumb"]',     // Any thumb class
                    '[class*="card"]',      // Any card class
                    'div[class*="thumsCou"]' // From config
                ];
                
                let allContainers = [];
                let selectorResults = {};
                
                for (const selector of selectors) {
                    try {
                        const found = document.querySelectorAll(selector);
                        selectorResults[selector] = found.length;
                        
                        // Add to all containers if not already there
                        for (const el of found) {
                            if (!allContainers.some(existing => existing === el)) {
                                allContainers.push({
                                    element: el,
                                    selector: selector,
                                    tag: el.tagName,
                                    id: el.id || 'none',
                                    classes: el.className,
                                    text: el.textContent?.slice(0, 50) || '',
                                    rect: el.getBoundingClientRect(),
                                    visible: el.getBoundingClientRect().top < window.innerHeight
                                });
                            }
                        }
                    } catch (e) {
                        selectorResults[selector] = `Error: ${e.message}`;
                    }
                }
                
                return {
                    selectorResults,
                    totalContainers: allContainers.length,
                    containers: allContainers.slice(0, 5) // First 5 for analysis
                };
            }
        """)
        
        print(f"   📈 Selector results:")
        for selector, count in generation_containers['selectorResults'].items():
            print(f"     {selector}: {count}")
        
        print(f"\n   🎯 Total generation containers found: {generation_containers['totalContainers']}")
        
        if generation_containers['totalContainers'] > 0:
            print(f"   📋 First few containers:")
            for i, container in enumerate(generation_containers['containers']):
                print(f"     {i+1}. {container['tag']}#{container['id']} - {container['selector']}")
                print(f"        Visible: {container['visible']}, Text: {container['text'][:30]}...")
        
        # STEP 4: Test scrolling methods with actual content
        print(f"\n🧪 STEP 4: Testing scroll methods on actual content...")
        
        if generation_containers['totalContainers'] == 0:
            print("   ⚠️  No generation containers found - page may not be fully loaded")
            print("   ⏰ Waiting additional 10 seconds for content...")
            await asyncio.sleep(10)
            
            # Re-check for containers
            recheck_state = await manager.get_scroll_position()
            print(f"   🔄 After waiting - containers: {recheck_state['containerCount']}")
        
        # Test with higher target distances since the page is larger
        print("   🎯 Testing Element.scrollIntoView() with 2000px target...")
        result1 = await manager.scroll_method_1_element_scrollintoview(2000)
        print(f"     Success: {result1.success}")
        print(f"     Distance: {result1.scroll_distance}px")
        print(f"     Time: {result1.execution_time:.3f}s")
        print(f"     Containers: {result1.containers_before} → {result1.containers_after}")
        
        await asyncio.sleep(3)
        
        print("   🎯 Testing container.scrollTop with 2000px target...")
        result2 = await manager.scroll_method_2_container_scrolltop(2000)
        print(f"     Success: {result2.success}")
        print(f"     Distance: {result2.scroll_distance}px")
        print(f"     Time: {result2.execution_time:.3f}s")
        print(f"     Containers: {result2.containers_before} → {result2.containers_after}")
        
        # STEP 5: Try the integrated scroll method
        print(f"\n🔗 STEP 5: Testing integrated scroll with fallback...")
        result3 = await manager.perform_scroll_with_fallback(2000)
        print(f"   Integrated scroll result:")
        print(f"     Method: {result3.method_name}")
        print(f"     Success: {result3.success}")
        print(f"     Distance: {result3.scroll_distance}px")
        print(f"     Time: {result3.execution_time:.3f}s")
        print(f"     New containers: {result3.new_containers_detected}")
        
        # STEP 6: Final analysis and recommendations
        final_state = await manager.get_scroll_position()
        
        print(f"\n💡 FINAL ANALYSIS AND RECOMMENDATIONS")
        print("=" * 60)
        
        max_distance = max([result1.scroll_distance, result2.scroll_distance, result3.scroll_distance])
        container_change = final_state['containerCount'] - initial_state['containerCount']
        
        print(f"📊 RESULTS SUMMARY:")
        print(f"   • Maximum scroll distance achieved: {max_distance}px")
        print(f"   • Initial containers: {initial_state['containerCount']}")
        print(f"   • Final containers: {final_state['containerCount']}")
        print(f"   • New containers loaded: {container_change}")
        print(f"   • Generation containers found: {generation_containers['totalContainers']}")
        
        if max_distance > 0:
            print(f"\n✅ SCROLLING IS WORKING!")
            
            # Determine which method works best
            best_method = "None"
            if result1.scroll_distance > result2.scroll_distance and result1.scroll_distance > result3.scroll_distance:
                best_method = "Element.scrollIntoView()"
            elif result2.scroll_distance > result3.scroll_distance:
                best_method = "container.scrollTop"
            else:
                best_method = "Integrated method"
            
            print(f"   🎯 Best performing method: {best_method}")
            
            if max_distance < 600:  # Current threshold
                print(f"   ⚠️  THRESHOLD ISSUE: Maximum {max_distance}px < 600px threshold")
                print(f"      SOLUTION: Lower success threshold in BoundaryScrollManager")
                print(f"      Current: {manager.min_scroll_distance * 0.3:.0f}px")
                print(f"      Suggested: {max_distance * 0.8:.0f}px")
            
        else:
            print(f"\n❌ SCROLLING NOT WORKING")
            print(f"   All scroll methods returned 0px distance")
            print(f"   This suggests the page uses virtual scrolling or custom containers")
        
        if generation_containers['totalContainers'] == 0:
            print(f"\n⚠️  NO GENERATION CONTAINERS FOUND")
            print(f"   The page may not have finished loading or login failed")
            print(f"   Check if the gallery is visible in the browser window")
        elif container_change > 0:
            print(f"\n✅ CONTENT LOADING WORKS: {container_change} new containers loaded")
        else:
            print(f"\n⚠️  NO NEW CONTENT LOADED")
            print(f"   Scrolling may need to be more aggressive or page may be at end")
        
        print(f"\n⏰ Keeping browser open for 15 seconds for manual inspection...")
        print(f"   Please check if you can see the generation gallery in the browser")
        await asyncio.sleep(15)
        
    except Exception as e:
        print(f"❌ Error during comprehensive analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(comprehensive_scroll_diagnosis())