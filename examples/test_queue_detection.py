#!/usr/bin/env python3
"""
Test Enhanced Queue Detection
Tests the improved queue detection functionality without navigation.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import AutomationSequenceBuilder, WebAutomationEngine

async def test_queue_detection():
    """
    Test the enhanced queue detection method
    """
    
    print("🔍 TESTING ENHANCED QUEUE DETECTION")
    print("=" * 50)
    
    builder = AutomationSequenceBuilder(
        name="Queue Detection Test",
        url="https://wan.video/generate"
    )
    
    automation = (builder
        .set_headless(False)
        .set_viewport(1280, 720)
        
        # Wait for login (assuming already logged in)
        .add_wait_for_element("input[placeholder=\"Email address\"]", timeout=8000, description="Wait for login form")
        .add_input_text("input[placeholder=\"Email address\"]", "shyraoleg@outlook.com", "Enter email")
        .add_input_text("input[type=\"password\"]", "Wanv!de025", "Enter password") 
        .add_wait(800, "Brief pause")
        .add_click_button("button:has-text(\"Log in\")[type=\"submit\"]", "Click login")
        .add_wait(2000, "Wait for login")
        
        # Navigate to generate page if needed
        .add_click_button("a[href='/generate'], button:has-text('Generate'), [data-test-id*='generate']", "Navigate to generate")
        .add_wait(2000, "Wait for generate page")
        
        # Test enhanced queue detection
        .add_set_variable("max_tasks", "8", "Set max tasks for comparison")
        .add_log_message("Testing enhanced queue detection...", "logs/queue_test.log", "Log test start")
        
        # Test 1: Direct queue detection
        .add_check_element(
            selector=".sc-dMmcxd.cZTIpi",
            check_type="less",
            expected_value="${max_tasks}",
            attribute="value",
            description="Test direct queue detection"
        )
        
        # Test 2: Log the result
        .add_log_message("Queue detection test completed", "logs/queue_test.log", "Log test completion")
        
        .build()
    )
    
    # Create logs directory
    import os
    os.makedirs("logs", exist_ok=True)
    
    print(f"📋 Automation configured with {len(automation.actions)} actions")
    print("🚀 Starting queue detection test...")
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print("\n📊 RESULTS:")
    print(f"Success: {results['success']}")
    print(f"Total actions executed: {len(results.get('action_results', []))}") 
    
    # Show check results
    for key, value in results.get('outputs', {}).items():
        if 'check' in key.lower():
            print(f"🔍 {key}: {value}")
    
    # Show variable states
    if hasattr(engine, 'variables'):
        print("\n🔢 VARIABLE VALUES:")
        for var, value in engine.variables.items():
            print(f"  {var}: {value}")
    
    print("\n📋 Check logs/queue_test.log for detailed results")

if __name__ == "__main__":
    print("ENHANCED QUEUE DETECTION TEST")
    print("=" * 50)
    print("This test will:")
    print("✅ Login to the website")
    print("✅ Navigate to generate page")
    print("✅ Test enhanced queue detection without navigation")
    print("✅ Log results for analysis")
    print("\nPress Enter to start test...")
    input()
    
    asyncio.run(test_queue_detection())