#!/usr/bin/env python3
"""
Test Check Element Action
Demonstrates how to check element values, attributes, and queue counts.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import AutomationSequenceBuilder, WebAutomationEngine

async def test_check_element():
    """Test checking element values and attributes"""
    
    print("🔍 CHECK ELEMENT TEST")
    print("=" * 50)
    print("This test demonstrates checking:")
    print("  1. Element text content")
    print("  2. Element attributes (data-*, aria-*, etc.)")
    print("  3. Numeric comparisons (greater/less than)")
    print("  4. Non-zero checks")
    print("=" * 50)
    
    # Create test automation
    builder = AutomationSequenceBuilder(
        name="Check Element Test",
        url="https://example.com"  # Replace with your target URL
    )
    
    automation = (builder
        .set_headless(False)  # Visible for testing
        .set_viewport(1280, 720)
        
        # Wait for page load
        .add_wait(2000, description="Wait for page to load")
        
        # Example 1: Check if an element's text equals a specific value
        .add_check_element(
            selector="h1",  # Example: Check the main heading
            check_type="equals",
            expected_value="Example Domain",
            attribute="text",
            description="Check if heading is 'Example Domain'"
        )
        
        # Example 2: Check if a queue count is not zero
        .add_check_element(
            selector=".queue-count",  # Replace with your queue count selector
            check_type="not_zero",
            expected_value="",  # Not needed for not_zero check
            attribute="text",
            description="Check if queue has items"
        )
        
        # Example 3: Check if tasks are less than 8
        .add_check_element(
            selector=".task-count",  # Replace with your task count selector
            check_type="less",
            expected_value="8",
            attribute="text",
            description="Check if task count < 8"
        )
        
        # Example 4: Check a data attribute
        .add_check_element(
            selector="button.process",  # Replace with your button selector
            check_type="not_equals",
            expected_value="0",
            attribute="data-remaining",  # Check data-remaining attribute
            description="Check if data-remaining is not 0"
        )
        
        # Example 5: Check if element contains specific text
        .add_check_element(
            selector=".status-message",  # Replace with your status selector
            check_type="contains",
            expected_value="Complete",
            attribute="text",
            description="Check if status contains 'Complete'"
        )
        
        .build()
    )
    
    # Run automation
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    # Display results
    print("\n" + "=" * 50)
    print("📊 CHECK RESULTS:")
    print(f"Success: {results['success']}")
    print(f"Actions completed: {results['actions_completed']}/{results['total_actions']}")
    
    # Show check results
    if results['outputs']:
        print("\n🔍 CHECK DETAILS:")
        for key, value in results['outputs'].items():
            if isinstance(value, dict) and 'success' in value:
                action_num = key.replace('action_', '')
                print(f"\nAction {action_num}:")
                print(f"  Check passed: {'✅' if value['success'] else '❌'}")
                print(f"  Actual value: '{value.get('actual_value', 'N/A')}'")
                print(f"  Expected: {value.get('check_type', '')} '{value.get('expected_value', '')}'")
                print(f"  Attribute checked: {value.get('attribute', 'text')}")
    
    if results['errors']:
        print("\n❌ ERRORS:")
        for error in results['errors']:
            print(f"  - {error['action_description']}: {error['error']}")
    
    return results['success']

async def test_dynamic_monitoring():
    """Monitor element values that change over time"""
    
    print("\n📈 DYNAMIC MONITORING TEST")
    print("=" * 50)
    print("Monitoring element values every 5 seconds...")
    
    url = input("Enter URL to monitor: ").strip()
    selector = input("Enter selector to monitor: ").strip()
    attribute = input("Enter attribute to check (text/value/etc): ").strip() or "text"
    
    builder = AutomationSequenceBuilder(
        name="Dynamic Monitor",
        url=url
    )
    
    # Monitor loop - check value 5 times with delays
    for i in range(5):
        automation = (builder
            .add_wait(5000, description=f"Wait 5 seconds (check {i+1}/5)")
            .add_check_element(
                selector=selector,
                check_type="not_equals",
                expected_value="",  # Just get the value
                attribute=attribute,
                description=f"Check #{i+1}: Get {attribute} value"
            )
        )
    
    automation = builder.build()
    
    engine = WebAutomationEngine(automation)
    engine.config.headless = False
    
    results = await engine.run_automation()
    
    # Display monitoring results
    print("\n📊 MONITORING RESULTS:")
    if results['outputs']:
        for key, value in results['outputs'].items():
            if isinstance(value, dict) and 'actual_value' in value:
                action_num = key.replace('action_', '')
                print(f"Check {int(action_num)//2 + 1}: {value['actual_value']}")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Test element checks on example.com")
    print("2. Monitor dynamic element values")
    print("3. Custom URL with checks")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        asyncio.run(test_check_element())
    elif choice == "2":
        asyncio.run(test_dynamic_monitoring())
    elif choice == "3":
        # Custom test
        url = input("Enter URL: ").strip()
        selector = input("Enter selector: ").strip()
        check_type = input("Check type (equals/not_equals/greater/less/contains/not_zero): ").strip()
        expected = input("Expected value (leave empty for not_zero): ").strip()
        attribute = input("Attribute (text/value/data-*/etc, default=text): ").strip() or "text"
        
        builder = AutomationSequenceBuilder("Custom Check", url)
        automation = (builder
            .set_headless(False)
            .add_wait(2000)
            .add_check_element(selector, check_type, expected, attribute, "Custom check")
            .build()
        )
        
        engine = WebAutomationEngine(automation)
        results = asyncio.run(engine.run_automation())
        
        if results['outputs'].get('action_1'):
            result = results['outputs']['action_1']
            print(f"\n{'✅ PASSED' if result['success'] else '❌ FAILED'}")
            print(f"Actual: {result['actual_value']}")
            print(f"Expected: {result['check_type']} {result['expected_value']}")
    else:
        print("Invalid choice")