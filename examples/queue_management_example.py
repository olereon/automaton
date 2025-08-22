#!/usr/bin/env python3
"""
Queue Management Example with Conditional Flow
Demonstrates checking queue limits and waiting/retrying when at capacity.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.engine import AutomationSequenceBuilder, WebAutomationEngine

async def queue_with_retry_example():
    """
    Example: Check queue count and retry if at limit
    This automation will:
    1. Check if queue count < 8
    2. If at limit (8), wait 30 seconds and retry (up to 5 times)
    3. If space available, add task to queue
    """
    
    print("📊 QUEUE MANAGEMENT WITH RETRY")
    print("=" * 50)
    
    builder = AutomationSequenceBuilder(
        name="Queue Management",
        url="https://yoursite.com/queue"  # Replace with your URL
    )
    
    automation = (builder
        .set_headless(False)
        .set_viewport(1280, 720)
        
        # Wait for page load
        .add_wait(2000, description="Wait for page to load")
        
        # Step 1: Check current queue count
        .add_check_element(
            selector=".queue-count",  # Your queue count selector
            check_type="less",
            expected_value="8",  # Check if less than 8
            attribute="text",
            description="Check if queue has space (< 8 tasks)"
        )
        
        # Step 2: Conditional wait and retry if queue is full
        .add_conditional_wait(
            condition="check_failed",  # Retry if check failed (queue >= 8)
            wait_time=10000,  # Wait 10 seconds
            max_retries=5,  # Try up to 5 times
            retry_from_action=2,  # Retry from the check (action index 2)
            description="Wait 10s and retry if queue is full"
        )
        
        # Step 3: If we get here, queue has space - add new task
        .add_click_button(
            selector="button.add-task",
            description="Click Add Task button"
        )
        
        .add_input_text(
            selector="input.task-name",
            value="New automated task",
            description="Enter task name"
        )
        
        .add_click_button(
            selector="button.submit-task",
            description="Submit new task"
        )
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print("\n📊 RESULTS:")
    print(f"Success: {results['success']}")
    
    if results['outputs']:
        for key, value in results['outputs'].items():
            if 'actual_value' in value:
                print(f"Queue count was: {value['actual_value']}")
                if value['success']:
                    print("✅ Queue had space, task added")
                else:
                    print("⏳ Queue was full, waited and retried")

async def skip_if_at_limit_example():
    """
    Example: Skip task creation if queue is at limit
    This automation will:
    1. Check if queue count == 8
    2. If at limit, skip the next 3 actions (task creation)
    3. Otherwise, create the task
    """
    
    print("🚫 SKIP IF AT LIMIT EXAMPLE")
    print("=" * 50)
    
    builder = AutomationSequenceBuilder(
        name="Skip If Full",
        url="https://yoursite.com/queue"
    )
    
    automation = (builder
        .set_headless(False)
        .set_viewport(1280, 720)
        
        .add_wait(2000, description="Wait for page load")
        
        # Check if queue is at maximum
        .add_check_element(
            selector=".queue-count",
            check_type="equals",
            expected_value="8",
            attribute="text",
            description="Check if queue is at max (8)"
        )
        
        # Skip task creation if at limit
        .add_skip_if(
            condition="check_passed",  # Skip if check passed (queue == 8)
            skip_count=3,  # Skip next 3 actions
            description="Skip task creation if queue is full"
        )
        
        # These 3 actions will be skipped if queue is full
        .add_click_button("button.add-task", description="[Skippable] Add task")
        .add_input_text("input.task-name", "New task", description="[Skippable] Enter name")
        .add_click_button("button.submit", description="[Skippable] Submit")
        
        # This will always run
        .add_click_button("button.refresh", description="Refresh queue display")
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print(f"\nResult: {results['success']}")
    if results['outputs']:
        check_result = list(results['outputs'].values())[0]
        if check_result.get('success'):
            print("⚠️ Queue was full, task creation skipped")
        else:
            print("✅ Queue had space, task was created")

async def complex_conditional_flow():
    """
    Example: Complex flow with multiple conditions
    - Check queue count
    - If < 4: Add 2 tasks
    - If 4-6: Add 1 task
    - If 7: Wait and retry
    - If 8: Skip all task creation
    """
    
    print("🔄 COMPLEX CONDITIONAL FLOW")
    print("=" * 50)
    
    builder = AutomationSequenceBuilder(
        name="Complex Flow",
        url="https://yoursite.com/queue"
    )
    
    automation = (builder
        .set_headless(False)
        .add_wait(2000)
        
        # Check 1: Is queue < 4?
        .add_check_element(".queue-count", "less", "4", "text", "Check if < 4")
        .add_skip_if("check_failed", skip_count=2, description="Skip 2-task add if >= 4")
        
        # Add 2 tasks if < 4
        .add_click_button("button.add-task", description="[If <4] Add first task")
        .add_click_button("button.add-task", description="[If <4] Add second task")
        
        # Check 2: Is queue exactly 7?
        .add_check_element(".queue-count", "equals", "7", "text", "Check if = 7")
        .add_conditional_wait("check_passed", wait_time=10000, max_retries=3,
                            retry_from_action=4, description="Wait if queue is 7")
        
        # Check 3: Is queue full (8)?
        .add_check_element(".queue-count", "equals", "8", "text", "Check if full")
        .add_skip_if("check_passed", skip_count=1, description="Skip if full")
        
        # Add single task if room
        .add_click_button("button.add-task", description="Add single task")
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print(f"\nSuccess: {results['success']}")
    print("Check the outputs to see which path was taken")

async def scheduled_retry_example():
    """
    Example: Retry at specific times
    This shows how to implement scheduled retries using wait times
    """
    
    print("⏰ SCHEDULED RETRY EXAMPLE")
    print("=" * 50)
    
    # Calculate wait time until next suitable time
    # For example, wait until next 5-minute mark
    now = datetime.now()
    next_run = now.replace(second=0, microsecond=0)
    if now.minute % 5 != 0:
        minutes_to_add = 5 - (now.minute % 5)
        next_run += timedelta(minutes=minutes_to_add)
    else:
        next_run += timedelta(minutes=5)
    
    wait_ms = int((next_run - now).total_seconds() * 1000)
    
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    print(f"Next run at: {next_run.strftime('%H:%M:%S')}")
    print(f"Waiting: {wait_ms/1000:.1f} seconds")
    
    builder = AutomationSequenceBuilder(
        name="Scheduled Retry",
        url="https://yoursite.com/queue"
    )
    
    automation = (builder
        .set_headless(False)
        
        # Wait until scheduled time
        .add_wait(wait_ms, description=f"Wait until {next_run.strftime('%H:%M')}")
        
        # Check queue
        .add_check_element(".queue-count", "less", "8", "text", "Check queue space")
        
        # If full, schedule next retry
        .add_conditional_wait(
            condition="check_failed",
            wait_time=100000,  # Wait 100 seconds (reduced from 5 min)
            max_retries=12,  # Retry for 1 hour
            retry_from_action=1,
            description="Retry every 100 seconds"
        )
        
        # Process if space available
        .add_click_button("button.process", description="Process task")
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print(f"\nCompleted: {results['success']}")

if __name__ == "__main__":
    print("QUEUE MANAGEMENT AUTOMATION EXAMPLES")
    print("=" * 50)
    print("Choose an example:")
    print("1. Queue with retry (wait if full)")
    print("2. Skip if at limit")
    print("3. Complex conditional flow")
    print("4. Scheduled retry")
    print("5. Run all examples")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        asyncio.run(queue_with_retry_example())
    elif choice == "2":
        asyncio.run(skip_if_at_limit_example())
    elif choice == "3":
        asyncio.run(complex_conditional_flow())
    elif choice == "4":
        asyncio.run(scheduled_retry_example())
    elif choice == "5":
        asyncio.run(queue_with_retry_example())
        print("\n" + "="*50 + "\n")
        asyncio.run(skip_if_at_limit_example())
        print("\n" + "="*50 + "\n")
        asyncio.run(complex_conditional_flow())
    else:
        print("Invalid choice")