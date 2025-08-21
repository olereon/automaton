#!/usr/bin/env python3
"""
Quick demonstration of the new scheduling features.
This script will schedule an automation to run 10 seconds in the future.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.automation_scheduler import AutomationScheduler, SchedulerConfig


async def main():
    """Quick demo that schedules an automation 10 seconds in the future"""
    print("🚀 Quick Scheduling Demo")
    print("="*60)
    
    # Create a simple test config
    test_config = {
        "name": "Quick Schedule Test",
        "url": "https://example.com",
        "headless": True,
        "viewport": {"width": 1280, "height": 720},
        "actions": [
            {
                "type": "wait",
                "value": 1000,
                "description": "Quick wait"
            },
            {
                "type": "log_message",
                "value": {
                    "message": f"✅ Automation executed at scheduled time: {datetime.now().strftime('%H:%M:%S')}",
                    "log_file": "logs/quick_demo.log"
                },
                "description": "Log execution"
            }
        ]
    }
    
    # Save config
    config_dir = Path("examples/temp_configs")
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "quick_test.json"
    
    with open(config_file, "w") as f:
        json.dump(test_config, f, indent=2)
    
    # Schedule for 10 seconds from now
    now = datetime.now()
    scheduled = now + timedelta(seconds=10)
    scheduled_time = scheduled.strftime("%H:%M:%S")
    
    print(f"Current time:    {now.strftime('%H:%M:%S')}")
    print(f"Scheduled for:   {scheduled_time} (in 10 seconds)")
    print("\n⏰ Watch the countdown...")
    print("Press Ctrl+C to cancel\n")
    
    # Create scheduler config
    config = SchedulerConfig(
        config_files=[str(config_file)],
        success_wait_time=5,
        failure_wait_time=5,
        max_retries=1,
        timeout_seconds=30,
        log_file="logs/quick_demo_scheduler.log",
        use_cli=True,
        verbose=True,
        scheduled_time=scheduled_time,
        scheduled_date=None  # Today
    )
    
    # Run scheduler
    scheduler = AutomationScheduler(config)
    
    try:
        # Run and wait for completion
        await scheduler.run_scheduler()
        print("\n✅ Demo completed successfully!")
        print("The automation ran at the scheduled time.")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    # Cleanup
    try:
        config_file.unlink()
    except:
        pass


if __name__ == "__main__":
    print("This demo will schedule an automation to run in 10 seconds.")
    print("You'll see a countdown timer before the automation starts.\n")
    asyncio.run(main())