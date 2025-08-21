#!/usr/bin/env python3
"""
Demo script to show queue full detection and scheduler retry behavior

This demonstrates:
1. How the automation detects the queue full popup
2. How it marks the run as failed
3. How the scheduler initiates a retry
"""

import json
import sys
from pathlib import Path

def explain_queue_full_handling():
    """Explain how the queue full detection and retry works"""
    
    print("=" * 70)
    print("QUEUE FULL DETECTION AND RETRY MECHANISM")
    print("=" * 70)
    
    print("\n📋 WORKFLOW OVERVIEW:")
    print("-" * 40)
    print("1. Automation clicks Submit button to create a task")
    print("2. Waits 1 second for submission response")
    print("3. Checks for popup with text 'You've reached your'")
    print("4. If popup detected:")
    print("   - Logs ERROR message")
    print("   - Attempts to click non-existent element (causes failure)")
    print("   - Automation stops with error")
    print("5. If no popup:")
    print("   - Increments task counter")
    print("   - Continues normally")
    
    print("\n🔄 SCHEDULER RETRY BEHAVIOR:")
    print("-" * 40)
    print("• When automation fails due to queue full:")
    print("  - Scheduler detects the failure")
    print("  - Waits 'failure_wait_time' seconds (default: 60s)")
    print("  - Retries the configuration")
    print("  - Maximum retries: 3 (configurable)")
    
    print("\n⚙️ CONFIGURATION:")
    print("-" * 40)
    
    # Load and show relevant config
    config_file = Path(__file__).parent.parent / "workflows" / "run-08-16-1.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Find the popup check action
        actions = config.get('actions', [])
        for i, action in enumerate(actions):
            if action.get('type') == 'check_element' and 'reached your' in str(action.get('selector', '')):
                print(f"✓ Popup detection configured at action #{i}")
                print(f"  Selector: {action.get('selector')}")
                print(f"  Timeout: {action.get('timeout')}ms")
                break
    
    print("\n📊 EXPECTED BEHAVIOR:")
    print("-" * 40)
    print("• Queue not full → Task created successfully")
    print("• Queue full → Automation fails → Scheduler retries")
    print("• After retries → If still full, moves to next config")
    
    print("\n🚀 TO TEST THIS:")
    print("-" * 40)
    print("1. Run the scheduler with the configuration:")
    print("   python scripts/automation_scheduler.py --configs workflows/run-08-16-1.json")
    print("\n2. The automation will:")
    print("   - Succeed if queue has space")
    print("   - Fail and retry if queue is full")
    
    print("\n💡 BENEFITS:")
    print("-" * 40)
    print("• Prevents wasted attempts when queue is full")
    print("• Automatic retry with configurable delays")
    print("• Clear error logging for debugging")
    print("• Scheduler tracks success/failure statistics")

def create_test_scheduler_config():
    """Create a test scheduler configuration for queue full scenarios"""
    
    config = {
        "config_files": [
            "workflows/run-08-16-1.json"
        ],
        "success_wait_time": 300,  # 5 minutes after success
        "failure_wait_time": 60,   # 1 minute before retry
        "max_retries": 3,          # Try up to 3 times
        "timeout_seconds": 600,    # 10 minutes per attempt
        "log_file": "logs/queue_full_test.log",
        "use_cli": True,
        "verbose": True
    }
    
    config_path = Path(__file__).parent.parent / "configs" / "queue_full_test_scheduler.json"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Test scheduler config created: {config_path}")
    print("\nRun with:")
    print(f"  python scripts/automation_scheduler.py --config {config_path}")
    
    return config_path

def main():
    """Main demo function"""
    explain_queue_full_handling()
    
    # Optionally create test config
    response = input("\n❓ Create test scheduler configuration? (y/n): ")
    if response.lower() == 'y':
        create_test_scheduler_config()
    
    print("\n" + "=" * 70)
    print("Queue full detection and retry mechanism is ready!")
    print("=" * 70)

if __name__ == "__main__":
    main()