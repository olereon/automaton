#!/usr/bin/env python3
"""
Debug Automation Script - Enhanced Error Reporting
This script provides detailed debugging information for automation failures.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.engine import AutomationSequenceBuilder, WebAutomationEngine

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/automation_debug.log')
    ]
)
logger = logging.getLogger(__name__)

async def debug_simple_automation():
    """Create a very simple automation with enhanced debugging"""
    
    print("🔍 DEBUG MODE: Creating Simple Test Automation")
    print("=" * 60)
    
    # Create a minimal automation to test basic functionality
    builder = AutomationSequenceBuilder(
        name="Debug Test - DuckDuckGo", 
        url="https://duckduckgo.com"
    )
    
    # Build with just a few basic actions
    automation = (builder
        .set_headless(False)  # Visible mode for debugging
        .set_viewport(1280, 720)
        
        # Test 1: Just wait for page load
        .add_wait(3000, description="Wait 3 seconds for page to fully load")
        
        # Test 2: Wait for a basic element that should exist
        .add_wait_for_element("body", timeout=10000, 
                             description="Wait for page body element")
        
        # Test 3: Try to find the search input with a simple selector
        .add_wait_for_element("input[name='q']", timeout=10000, 
                             description="Wait for DuckDuckGo search box")
        
        # Test 4: Click on the search box
        .add_click_button("input[name='q']", 
                         description="Click on search box")
        
        # Test 5: Type some text
        .add_input_text("input[name='q']", "test search",
                       description="Type 'test search' in search box")
        
        .build()
    )
    
    logger.info(f"Created automation with {len(automation.actions)} debug actions")
    return automation

async def run_debug_automation():
    """Run automation with detailed error analysis"""
    
    print("\n🚀 Starting DEBUG Automation...")
    print("👀 Browser window will open - watch for errors")
    print("=" * 60)
    
    # Create debug automation
    config = await debug_simple_automation()
    
    # Run with enhanced error reporting
    engine = WebAutomationEngine(config)
    
    try:
        print("\n📺 Launching browser and starting automation...")
        results = await engine.run_automation()
        
        print("\n" + "=" * 60)
        print("🎯 AUTOMATION RESULTS:")
        print(f"✅ Success: {results['success']}")
        print(f"📊 Actions completed: {results['actions_completed']}/{results['total_actions']}")
        
        if results['errors']:
            print(f"\n❌ ERRORS FOUND ({len(results['errors'])}):")
            print("-" * 40)
            
            for i, error in enumerate(results['errors'], 1):
                print(f"\n🔥 ERROR {i}:")
                print(f"   Action #{error['action_index']}: {error['action_type']}")
                print(f"   Description: {error['action_description']}")
                print(f"   Selector: {error['selector']}")
                print(f"   Error Type: {error['error_type']}")
                print(f"   Error Message: {error['error']}")
                print(f"   Page URL: {error.get('page_url', 'Unknown')}")
                print(f"   Page Title: {error.get('page_title', 'Unknown')}")
                
                # Provide specific debugging tips
                if error['action_type'] == 'wait_for_element':
                    print("\n   💡 DEBUGGING TIPS:")
                    print("      - Check if the selector is correct")
                    print("      - Try right-clicking the element and 'Inspect'")
                    print("      - Copy the selector from browser dev tools")
                    print("      - The element might load after the timeout")
                    
                elif error['action_type'] == 'click_button':
                    print("\n   💡 DEBUGGING TIPS:")
                    print("      - Element might not be clickable yet")
                    print("      - Try adding a wait_for_element before clicking")
                    print("      - Check if element is hidden behind another element")
                    
                elif error['action_type'] == 'input_text':
                    print("\n   💡 DEBUGGING TIPS:")
                    print("      - Input field might not be ready for text")
                    print("      - Try clicking the field first")
                    print("      - Check if field requires focus")
        else:
            print("🎉 No errors - all actions executed successfully!")
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        print("This indicates a fundamental issue with the automation setup.")
        return False
    
    # Additional debugging information
    print(f"\n📋 DEBUG LOG saved to: /tmp/automation_debug.log")
    print("📖 Check the log file for detailed technical information")
    
    return results['success']

async def quick_page_test():
    """Quick test to just open page and inspect elements"""
    
    print("\n🔬 QUICK PAGE INSPECTION TEST")
    print("=" * 40)
    
    try:
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        print("🌐 Opening DuckDuckGo...")
        await page.goto("https://duckduckgo.com", wait_until="networkidle")
        
        print(f"📄 Page Title: {await page.title()}")
        print(f"🔗 Current URL: {page.url}")
        
        # Check for search box
        search_inputs = await page.query_selector_all("input[name='q']")
        print(f"🔍 Search boxes found: {len(search_inputs)}")
        
        all_inputs = await page.query_selector_all("input")
        print(f"📝 Total input elements: {len(all_inputs)}")
        
        # Print details of first few inputs
        for i, inp in enumerate(all_inputs[:3]):
            attrs = await inp.evaluate("el => ({name: el.name, id: el.id, type: el.type, placeholder: el.placeholder})")
            print(f"   Input {i+1}: {attrs}")
        
        print("\n⏳ Keeping browser open for 10 seconds for manual inspection...")
        await asyncio.sleep(10)
        
        await browser.close()
        print("✅ Quick test completed")
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")

if __name__ == "__main__":
    print("🐛 AUTOMATION DEBUGGING TOOL")
    print("This tool provides detailed error analysis for failed automations")
    print("\nChoose an option:")
    print("1. Run debug automation (recommended)")
    print("2. Quick page inspection test")
    print("3. Both tests")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice in ["2", "3"]:
            print("\n" + "="*60)
            asyncio.run(quick_page_test())
        
        if choice in ["1", "3"]:
            print("\n" + "="*60)
            success = asyncio.run(run_debug_automation())
            
            if success:
                print("\n🎊 Debug automation completed successfully!")
                print("💡 Your automation setup is working correctly.")
                print("🔧 The issue might be with specific selectors in your config.")
            else:
                print("\n⚠️ Debug automation failed - check detailed errors above")
                print("🛠️ Use the debugging tips to fix selector issues")
                
    except KeyboardInterrupt:
        print("\n🛑 Debug session cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error in debug tool: {e}")