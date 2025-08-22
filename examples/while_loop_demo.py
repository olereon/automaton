#!/usr/bin/env python3
"""
While Loop Queue Management Demo
Demonstrates the new while loop functionality with variables and logging.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.engine import AutomationSequenceBuilder, WebAutomationEngine

async def while_loop_demo():
    """
    Demo: While loop with variables and logging
    This automation will:
    1. Initialize variables (task_count = 0, max_tasks = 8)
    2. While queue < max_tasks:
       - Check queue count
       - Create task if space available
       - Increment counter
       - Log progress
    3. Stop when queue is full
    """
    
    print("🔄 WHILE LOOP QUEUE MANAGEMENT DEMO")
    print("=" * 50)
    
    builder = AutomationSequenceBuilder(
        name="While Loop Demo",
        url="https://wan.video/generate"
    )
    
    automation = (builder
        .set_headless(False)
        .set_viewport(1280, 720)
        
        # Initialize variables
        .add_set_variable("task_count", "0", "Initialize task counter")
        .add_set_variable("max_tasks", "8", "Set maximum queue capacity")
        
        # Log start
        .add_log_message(
            "Starting automation - Target: ${max_tasks} tasks",
            "logs/while_loop_demo.log",
            "Log automation start"
        )
        
        # Initial queue check
        .add_click_button(".sc-bfjeOH.kgbaCl", "Initial queue check")
        .add_wait(300, "Wait after initial click")
        
        # WHILE LOOP: Continue while queue has space
        .add_while_begin("check_passed", "WHILE queue has space")
        
            # Check if queue < max_tasks
            .add_check_element(
                selector=".sc-dMmcxd.cZTIpi",
                check_type="less",
                expected_value="${max_tasks}",
                attribute="value",
                description="Check if queue has space"
            )
            
            # IF queue is full, break out
            .add_if_begin("check_failed", "IF queue is full")
                .add_log_message(
                    "Queue is full (${max_tasks}) - stopping. Created: ${task_count} tasks",
                    "logs/while_loop_demo.log",
                    "Log queue full"
                )
                .add_break("Exit loop - queue full")
            .add_if_end("END IF")
            
            # Log task creation
            .add_log_message(
                "Creating task #${task_count} - queue has space",
                "logs/while_loop_demo.log",
                "Log task creation"
            )
            
            # Task creation sequence
            .add_click_button(".sc-dMmcxd.cZTIpi", "Click queue")
            .add_click_button(".sc-cmdOMZ.jZnOHe", "Open creation field")
            .add_wait(500, "Wait before settings")
            
            # Configure settings
            .add_click_button("[data-test-id=\"creation-form-button-setting\"]", "Open settings")
            .add_wait(1500, "Wait for settings")
            .add_toggle_setting("[data-test-id=\"creation-form-checkbox-generateWidthCredits\"]", False, "Disable credits")
            .add_wait(500, "Wait after toggle")
            .add_click_button("[data-test-id=\"creation-form-button-setting\"]", "Close settings")
            
            # Add content
            .add_click_button(".sc-fXpfQj.ibGzNb", "Click Add Image")
            .add_wait(1000, "Wait before upload")
            .add_upload_image(
                "text=\"Upload from device\"",
                "/home/olereon/workspace/github.com/olereon/!_temp/-up-3_01114_.png",
                "Upload image"
            )
            .add_wait(4000, "Wait for upload")
            
            # Input prompt with task number substitution
            .add_input_text(
                "[data-test-id=\"creation-form-textarea\"]",
                "Task ${task_count}: Automated task creation with while loop functionality",
                "Input prompt with task number"
            )
            .add_wait(2000, "Wait before submit")
            
            # Submit and track progress
            .add_click_button("[data-test-id=\"creation-form-button-submit\"]", "Submit task")
            .add_increment_variable("task_count", 1, "Increment task counter")
            
            # Log completion
            .add_log_message(
                "Successfully created task #${task_count}",
                "logs/while_loop_demo.log",
                "Log task completion"
            )
            
            # Refresh queue view
            .add_wait(2000, "Wait between tasks")
            .add_click_button(".sc-bfjeOH.kgbaCl", "Refresh queue view")
            .add_wait(500, "Wait for refresh")
            
        .add_while_end("END WHILE loop")
        
        # Final log
        .add_log_message(
            "Automation completed. Total tasks created: ${task_count}",
            "logs/while_loop_demo.log",
            "Log final completion"
        )
        
        .build()
    )
    
    # Create logs directory
    import os
    os.makedirs("logs", exist_ok=True)
    
    print(f"📋 Automation configured with {len(automation.actions)} actions")
    print("🚀 Starting execution...")
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print("\n📊 RESULTS:")
    print(f"Success: {results['success']}")
    print(f"Total actions executed: {len(results.get('action_results', []))}")
    
    # Show variable states
    if hasattr(engine, 'variables'):
        print("\n🔢 FINAL VARIABLE VALUES:")
        for var, value in engine.variables.items():
            print(f"  {var}: {value}")
    
    print("\n📋 Check logs/while_loop_demo.log for detailed execution log")

if __name__ == "__main__":
    print("WHILE LOOP AUTOMATION DEMO")
    print("=" * 50)
    print("This demo shows queue management using while loops with:")
    print("✅ Variable tracking (task_count, max_tasks)")
    print("✅ Conditional execution (while queue < 8)")
    print("✅ External logging with timestamps")
    print("✅ Variable substitution in actions")
    print("✅ Loop control (break when queue full)")
    print("\nPress Enter to start demo...")
    input()
    
    asyncio.run(while_loop_demo())