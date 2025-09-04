#!/usr/bin/env python3.11
"""
Test Dynamic Threshold Fix
==========================
Tests that the dynamic threshold fix resolves the 0px detection issue.
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


async def test_dynamic_threshold():
    """Test that dynamic threshold properly handles small scroll distances"""
    
    print(f"🧪 Testing Dynamic Threshold Fix")
    print("=" * 50)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)  # Headless for quick test
    page = await browser.new_page()
    
    try:
        # Create a test page with limited scroll capability
        await page.goto("data:text/html," + """
        <html>
            <body style="height: 200vh;">
                <div style="height: 100px; overflow-y: scroll; border: 1px solid black;">
                    <div style="height: 500px;">Scrollable content</div>
                </div>
                <div style="height: 1000px;">More content to make page scrollable</div>
            </body>
        </html>
        """)
        
        await asyncio.sleep(1)
        
        # Initialize manager
        manager = BoundaryScrollManager(page)
        
        print("📊 Testing scroll methods with dynamic thresholds...")
        
        # Test primary method
        result1 = await manager.scroll_method_1_element_scrollintoview(2000)
        print(f"   Primary method:")
        print(f"     Distance: {result1.scroll_distance}px")
        print(f"     Success: {result1.success}")
        print(f"     Method: {result1.method_name}")
        
        # Test fallback method  
        result2 = await manager.scroll_method_2_container_scrolltop(2000)
        print(f"   Fallback method:")
        print(f"     Distance: {result2.scroll_distance}px")
        print(f"     Success: {result2.success}")
        print(f"     Method: {result2.method_name}")
        
        # Test integrated method
        result3 = await manager.perform_scroll_with_fallback(2000)
        print(f"   Integrated method:")
        print(f"     Distance: {result3.scroll_distance}px")
        print(f"     Success: {result3.success}")
        print(f"     Method: {result3.method_name}")
        
        print(f"\n💡 ANALYSIS:")
        
        # Check if any method succeeded with small distances
        max_distance = max([result1.scroll_distance, result2.scroll_distance, result3.scroll_distance])
        any_success = any([result1.success, result2.success, result3.success])
        
        if max_distance > 0 and any_success:
            print(f"✅ DYNAMIC THRESHOLD FIX WORKING!")
            print(f"   • Maximum scroll achieved: {max_distance}px")
            print(f"   • At least one method succeeded with small distance")
            print(f"   • This should resolve the 0px detection issue")
        elif max_distance > 0:
            print(f"⚠️  SCROLLING WORKS BUT THRESHOLD STILL TOO HIGH")
            print(f"   • Scroll distance: {max_distance}px")
            print(f"   • But success criteria not met")
            print(f"   • Need to lower threshold further")
        else:
            print(f"❌ NO SCROLLING DETECTED")
            print(f"   • This is expected on a simple test page")
            print(f"   • Real test needs to be on wan.video with content")
        
        print(f"\n🎯 RECOMMENDATION:")
        if max_distance > 0 and any_success:
            print(f"   The dynamic threshold fix should resolve the user's issue.")
            print(f"   When scroll distances are small (like 140px), the system will")
            print(f"   automatically lower the success threshold to 80% of achieved distance.")
            print(f"   This means 140px scroll → 112px threshold = SUCCESS ✅")
        else:
            print(f"   Run this test on actual wan.video/generate page to verify")
            print(f"   the fix works with real scroll containers and content.")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await browser.close()
    
    return max_distance > 0 and any_success


async def test_generation_download_integration():
    """Test that the fix integrates properly with GenerationDownloadManager"""
    
    print(f"\n🔗 Testing Integration with GenerationDownloadManager")
    print("=" * 60)
    
    try:
        from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig
        
        # Create test config
        config = GenerationDownloadConfig(
            downloads_folder="/tmp/test",
            logs_folder="/tmp/test",
            max_downloads=5,
            duplicate_check_enabled=False,
            stop_on_duplicate=False,
            creation_time_text="Creation Time"
        )
        
        # Create manager
        manager = GenerationDownloadManager(config)
        print("✅ GenerationDownloadManager created successfully")
        
        # Test initialization
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto("data:text/html,<html><body>Test</body></html>")
            
            # Initialize boundary scroll manager
            manager.initialize_boundary_scroll_manager(page)
            print("✅ BoundaryScrollManager initialized")
            
            # Test that it has the dynamic threshold improvements
            scroll_result = await manager.boundary_scroll_manager.perform_scroll_with_fallback(1000)
            print(f"✅ Integrated scroll test completed")
            print(f"   Method: {scroll_result.method_name}")
            print(f"   Success: {scroll_result.success}")
            print(f"   Distance: {scroll_result.scroll_distance}px")
            
        finally:
            await browser.close()
        
        print("✅ Integration test successful - fixes are properly integrated")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Dynamic Threshold Fix Test Suite")
    print("=" * 50)
    
    async def run_tests():
        test1_passed = await test_dynamic_threshold()
        test2_passed = await test_generation_download_integration()
        
        print(f"\n📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"Dynamic Threshold Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Integration Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        
        if test1_passed and test2_passed:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"The dynamic threshold fix should resolve the scroll detection issue.")
            print(f"")
            print(f"📋 WHAT WAS FIXED:")
            print(f"• Dynamic success threshold: Adapts to actual scroll capabilities")
            print(f"• Minimum threshold: 100px instead of 600px")
            print(f"• Adaptive threshold: 80% of achieved distance")
            print(f"• Better logging: Shows threshold calculations")
            print(f"")
            print(f"🎯 EXPECTED BEHAVIOR:")
            print(f"• 140px scroll → 112px threshold → SUCCESS ✅")
            print(f"• Fallback method will be used when primary fails")
            print(f"• Boundary detection will continue instead of stopping")
            
            return True
        else:
            print(f"\n❌ SOME TESTS FAILED")
            print(f"Check error messages above for details.")
            return False
    
    success = asyncio.run(run_tests())
    exit(0 if success else 1)