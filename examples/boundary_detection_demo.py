#!/usr/bin/env python3.11
"""
Boundary Detection Demo
=======================
Demonstrates how to use the verified scrolling methods for boundary detection
in generation galleries.

This example shows how to:
1. Initialize the boundary scroll manager
2. Define boundary criteria 
3. Perform scrolling with verified methods
4. Detect new generation containers
5. Scan for boundary generations
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from playwright.async_api import async_playwright
from utils.boundary_scroll_manager import BoundaryScrollManager
from utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig


async def boundary_detection_demo():
    """Demo of boundary detection functionality"""
    
    print("🎯 Boundary Detection Demo")
    print("=" * 50)
    print("This demo shows how to use verified scrolling methods to find")
    print("boundary generations in a gallery. The methods used are:")
    print("  1. Element.scrollIntoView() - Primary (Rank #1)")
    print("  2. container.scrollTop - Fallback (Rank #2)")
    print("  Both ensure >2000px scroll distance per action.")
    print("")
    
    # Get URL from user
    url = input("Enter the /generate page URL: ").strip()
    if not url:
        print("❌ URL required")
        return
    
    # Initialize Playwright
    print("🚀 Launching browser...")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,  # Visible for demo
        args=['--disable-blink-features=AutomationControlled']
    )
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080}
    )
    page = await context.new_page()
    
    try:
        # Navigate to the page
        print(f"🌐 Navigating to: {url}")
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Initialize boundary scroll manager
        print("🎯 Initializing boundary scroll manager...")
        manager = BoundaryScrollManager(page)
        
        # Demo 1: Get initial scroll position
        print("\n📊 Demo 1: Getting initial scroll position")
        initial_state = await manager.get_scroll_position()
        print(f"   Current scroll position: {initial_state['windowScrollY']}px")
        print(f"   Generation containers found: {initial_state['containerCount']}")
        print(f"   Page scroll height: {initial_state['scrollHeight']}px")
        print(f"   Visible containers: {len([c for c in initial_state['containers'] if c['visible']])}")
        
        # Demo 2: Test primary scroll method
        print("\n🎯 Demo 2: Testing primary scroll method (Element.scrollIntoView)")
        print("   Target distance: 2500px")
        result1 = await manager.scroll_method_1_element_scrollintoview(2500)
        print(f"   ✓ Method: {result1.method_name}")
        print(f"   ✓ Success: {result1.success}")
        print(f"   ✓ Distance scrolled: {result1.scroll_distance}px")
        print(f"   ✓ Execution time: {result1.execution_time:.3f}s")
        print(f"   ✓ New containers detected: {result1.new_containers_detected}")
        
        input("\nPress Enter to continue to Demo 3...")
        
        # Demo 3: Test fallback scroll method
        print("\n🎯 Demo 3: Testing fallback scroll method (container.scrollTop)")
        print("   Target distance: 2200px")
        result2 = await manager.scroll_method_2_container_scrolltop(2200)
        print(f"   ✓ Method: {result2.method_name}")
        print(f"   ✓ Success: {result2.success}")
        print(f"   ✓ Distance scrolled: {result2.scroll_distance}px")
        print(f"   ✓ Execution time: {result2.execution_time:.3f}s")
        print(f"   ✓ New containers detected: {result2.new_containers_detected}")
        
        input("\nPress Enter to continue to Demo 4...")
        
        # Demo 4: Define boundary criteria
        print("\n🎯 Demo 4: Defining boundary criteria")
        print("   You can customize these criteria based on your specific needs:")
        
        # Example boundary criteria
        boundary_criteria = {
            'generation_id_pattern': '#000001',  # Look for generation IDs containing this
            'text_contains': 'older generation',  # Look for this text in containers
            'attribute_matches': {
                'data-status': 'completed'  # Look for completed generations
            },
            'dataset_matches': {
                'generationType': 'video'  # Look for video generations
            }
        }
        
        print("   Example criteria defined:")
        for key, value in boundary_criteria.items():
            print(f"     {key}: {value}")
        
        # Allow user to customize criteria
        print("\n   Would you like to customize the boundary criteria?")
        customize = input("   (y/n): ").strip().lower()
        
        if customize in ['y', 'yes']:
            print("\n   Enter custom boundary criteria:")
            pattern = input("   Generation ID pattern to search for (or press Enter to skip): ").strip()
            if pattern:
                boundary_criteria['generation_id_pattern'] = pattern
            
            text = input("   Text content to search for (or press Enter to skip): ").strip()
            if text:
                boundary_criteria['text_contains'] = text
        
        input("\nPress Enter to start boundary search...")
        
        # Demo 5: Full boundary search
        print("\n🎯 Demo 5: Full boundary search with verified methods")
        print("   This will scroll through the gallery until a boundary is found")
        print("   or the end is reached. Each scroll will be >2000px.")
        print(f"   Boundary criteria: {boundary_criteria}")
        print("")
        
        boundary_found = await manager.scroll_until_boundary_found(boundary_criteria)
        
        # Display results
        stats = manager.get_scroll_statistics()
        
        print("\n📊 RESULTS:")
        print("=" * 30)
        print(f"Boundary found: {'✓ YES' if boundary_found else '✗ NO'}")
        print(f"Total scrolls performed: {stats['scroll_attempts']}")
        print(f"Total distance scrolled: {stats['total_scrolled_distance']:,}px")
        print(f"Average scroll distance: {stats['average_scroll_distance']:.0f}px")
        print(f"Minimum scroll distance: {stats['min_scroll_distance']}px")
        
        if boundary_found:
            print(f"\n🎯 BOUNDARY DETAILS:")
            print(f"   ID: {boundary_found.get('id', 'N/A')}")
            print(f"   Text: {boundary_found.get('text', 'N/A')[:100]}...")
            print(f"   Class: {boundary_found.get('className', 'N/A')}")
            print(f"   Attributes: {len(boundary_found.get('attributes', {}))}")
        
        # Demo 6: Integration with GenerationDownloadManager
        print("\n🎯 Demo 6: Integration with GenerationDownloadManager")
        print("   This shows how the boundary scroll manager integrates")
        print("   with the existing generation download automation.")
        
        # Create a minimal config for demo
        config = GenerationDownloadConfig(
            downloads_folder="./demo_downloads",
            max_downloads=5,
            duplicate_check_enabled=False,
            creation_time_text="Aug 27, 2024"
        )
        
        # Initialize download manager
        download_manager = GenerationDownloadManager(config)
        
        # Show how to use the integrated method
        print("\n   Using integrated boundary search method:")
        boundary_via_integration = await download_manager.scroll_to_find_boundary_generations(
            page, boundary_criteria
        )
        
        print(f"   Result: {'✓ Found' if boundary_via_integration else '✗ Not found'}")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n🏁 Demo completed!")
        print("   The browser will remain open for inspection.")
        input("   Press Enter to close...")
        await browser.close()


async def simple_boundary_test():
    """Simplified test for quick verification"""
    print("🎯 Simple Boundary Test")
    print("=" * 30)
    
    url = "https://example.com/generate"  # Replace with actual URL
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    
    try:
        await page.goto(url)
        await asyncio.sleep(2)
        
        manager = BoundaryScrollManager(page)
        
        # Simple scroll test
        result = await manager.perform_scroll_with_fallback(2000)
        print(f"Scroll test: {result.success}, {result.scroll_distance}px")
        
    finally:
        await browser.close()


if __name__ == "__main__":
    print("Boundary Detection Demo Options:")
    print("1. Full Interactive Demo")
    print("2. Simple Test")
    
    choice = input("Select option (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(boundary_detection_demo())
    elif choice == "2":
        asyncio.run(simple_boundary_test())
    else:
        print("Invalid choice. Running full demo...")
        asyncio.run(boundary_detection_demo())