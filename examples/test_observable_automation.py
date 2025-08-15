#!/usr/bin/env python3
"""
Observable Test Automation - Watch Browser Actions in Real-Time
This script demonstrates how to create an automation that you can watch.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import AutomationSequenceBuilder, WebAutomationEngine

async def create_observable_test():
    """Create a test automation that's easy to observe"""
    
    print("🎬 Creating Observable Test Automation...")
    print("=" * 50)
    
    # Build an observable automation sequence
    builder = AutomationSequenceBuilder(
        name="Observable Test - GitHub Search", 
        url="https://github.com"
    )
    
    # Configure for VISIBLE mode (headless=False)
    automation = (builder
        .set_headless(False)  # 👁️ VISIBLE MODE - Browser window will appear
        .set_viewport(1280, 720)  # Nice window size
        
        # Action 1: Wait for page to load
        .add_wait_for_element("body", timeout=10000, 
                             description="Wait for GitHub homepage to load")
        
        # Action 2: Wait a moment so you can see the page
        .add_wait(3000, description="Pause to observe the homepage")
        
        # Action 3: Find and click the search box
        .add_click_button("input[placeholder*='Search']", 
                         description="Click on the search box")
        
        # Action 4: Type in a search term
        .add_input_text("input[placeholder*='Search']", "playwright automation",
                       description="Type search term: 'playwright automation'")
        
        # Action 5: Wait to see the typing
        .add_wait(2000, description="Pause to see the typed text")
        
        # Action 6: Press Enter (submit search)
        .add_click_button("input[placeholder*='Search']", 
                         description="Submit search by clicking search field")
        
        # Action 7: Wait for search results
        .add_wait_for_element("[data-testid='results-list']", timeout=10000,
                             description="Wait for search results to appear")
        
        # Action 8: Final pause to observe results
        .add_wait(5000, description="Pause to observe search results")
        
        .build()
    )
    
    print(f"✅ Created automation with {len(automation.actions)} observable actions:")
    for i, action in enumerate(automation.actions, 1):
        print(f"   {i}. {action.type.value} - {action.description}")
    
    return automation

async def run_observable_test():
    """Run the test automation and watch it work"""
    
    print("\n🚀 Starting Observable Automation...")
    print("👀 WATCH: Browser window will appear shortly!")
    print("=" * 50)
    
    # Create the test automation
    config = await create_observable_test()
    
    # Run the automation
    engine = WebAutomationEngine(config)
    
    print("\n📺 Browser launching... Get ready to watch!")
    print("🎬 You should see:")
    print("   • Browser window opens")
    print("   • GitHub homepage loads")
    print("   • Search box gets clicked")
    print("   • Text gets typed")
    print("   • Search executes")
    print("   • Results appear")
    
    try:
        results = await engine.run_automation()
        
        print("\n" + "=" * 50)
        print("🎉 AUTOMATION COMPLETED!")
        print(f"✅ Success: {results['success']}")
        print(f"📊 Actions completed: {results['actions_completed']}/{results['total_actions']}")
        
        if results['errors']:
            print(f"❌ Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"   • {error}")
        else:
            print("🎯 No errors - all actions executed successfully!")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
    
    return results['success']

if __name__ == "__main__":
    print("🧪 OBSERVABLE AUTOMATION TEST")
    print("This will open a browser window so you can watch the automation!")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()  # Wait for user confirmation
        success = asyncio.run(run_observable_test())
        
        if success:
            print("\n🎊 Test completed successfully!")
            print("💡 Next steps:")
            print("   • Try creating your own automation in the GUI")
            print("   • Remember to uncheck 'Run headless' to watch it")
            print("   • Add wait actions to slow down for better observation")
        else:
            print("\n⚠️ Test had issues - check the browser window for details")
            
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")