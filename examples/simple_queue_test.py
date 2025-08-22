#!/usr/bin/env python3
"""
Simple Queue Detection Test
Minimal test to verify enhanced queue detection on generate page.
Assumes user is already logged in and on generate page.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.engine import AutomationSequenceBuilder, WebAutomationEngine

async def simple_queue_test():
    """
    Simple test assuming already on generate page
    """
    
    print("🔍 SIMPLE QUEUE DETECTION TEST")
    print("=" * 50)
    
    builder = AutomationSequenceBuilder(
        name="Simple Queue Test",
        url="https://wan.video/generate"
    )
    
    automation = (builder
        .set_headless(False)
        .set_viewport(1280, 720)
        
        # Initialize test variables
        .add_set_variable("max_tasks", "8", "Set max tasks for comparison")
        .add_log_message("Starting simple queue detection test...", "logs/simple_queue_test.log", "Log test start")
        
        # Wait for page to be ready
        .add_wait(3000, "Wait for page to be ready")
        
        # Test enhanced queue detection
        .add_check_element(
            selector=".sc-dMmcxd.cZTIpi",
            check_type="less",
            expected_value="${max_tasks}",
            attribute="value",
            description="Test enhanced queue detection"
        )
        
        # Log the result
        .add_log_message("Queue detection test completed successfully", "logs/simple_queue_test.log", "Log test completion")
        
        .build()
    )
    
    # Create logs directory
    import os
    os.makedirs("logs", exist_ok=True)
    
    print(f"📋 Automation configured with {len(automation.actions)} actions")
    print("🚀 Starting simple queue detection test...")
    print("📝 Make sure you're already logged in and on the generate page!")
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print("\n📊 RESULTS:")
    print(f"Success: {results['success']}")
    print(f"Total actions executed: {len(results.get('action_results', []))}") 
    
    # Show check results
    outputs = results.get('outputs', {})
    if outputs:
        print("\n🔍 CHECK RESULTS:")
        for key, value in outputs.items():
            print(f"  {key}: {value}")
    
    # Show errors if any
    errors = results.get('errors', [])
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"  {error.get('action_type', 'Unknown')}: {error.get('error', 'Unknown error')}")
    
    # Show variable states
    if hasattr(engine, 'variables'):
        print("\n🔢 VARIABLE VALUES:")
        for var, value in engine.variables.items():
            print(f"  {var}: {value}")
    
    print("\n📋 Check logs/simple_queue_test.log for detailed results")

if __name__ == "__main__":
    print("SIMPLE QUEUE DETECTION TEST")
    print("=" * 50)
    print("Prerequisites:")
    print("🔑 You must be logged in to wan.video")
    print("📄 You must be on the /generate page")
    print("🎯 The queue element should be visible")
    print("\nThis test will:")
    print("✅ Test enhanced JavaScript-based queue detection")
    print("✅ Log detailed results for analysis")
    print("✅ Show queue value and comparison results")
    print("\nPress Enter to start test...")
    input()
    
    asyncio.run(simple_queue_test())