#!/usr/bin/env python3
"""
Automation Scheduler Demo Script

This script demonstrates how to use the automation scheduler with example configurations.
It shows different scheduling scenarios and configuration options.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.automation_scheduler import AutomationScheduler, SchedulerConfig


async def demo_basic_scheduling():
    """Demonstrate basic automation scheduling"""
    print("🎬 Demo: Basic Automation Scheduling")
    print("=" * 50)
    
    # Create demo configuration
    config = SchedulerConfig(
        config_files=[
            "examples/automaton-example-config.json",
            "configs/example_automation.json"
        ],
        success_wait_time=10,  # Short wait for demo
        failure_wait_time=5,   # Short retry wait for demo
        max_retries=2,
        timeout_seconds=300,   # 5 minutes timeout
        log_file="logs/demo_scheduler.log",
        use_cli=True,
        verbose=True
    )
    
    scheduler = AutomationScheduler(config)
    
    try:
        await scheduler.run_scheduler()
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")


async def demo_queue_management():
    """Demonstrate queue management scheduling"""
    print("🎬 Demo: Queue Management Automation")
    print("=" * 50)
    
    # Check if queue management configs exist
    queue_configs = [
        "workflows/user_while-loop-1.json",
        "workflows/user_while-loop-2.json"
    ]
    
    existing_configs = [config for config in queue_configs if Path(config).exists()]
    
    if not existing_configs:
        print("⚠️  Queue management configurations not found. Using example configs instead.")
        existing_configs = [
            "examples/automaton-example-config.json",
            "configs/example_automation.json"
        ]
    
    config = SchedulerConfig(
        config_files=existing_configs,
        success_wait_time=30,   # 30 seconds between successful runs
        failure_wait_time=15,   # 15 seconds before retry
        max_retries=3,
        timeout_seconds=600,    # 10 minutes timeout
        log_file="logs/queue_demo_scheduler.log",
        use_cli=True,
        verbose=True
    )
    
    scheduler = AutomationScheduler(config)
    
    try:
        await scheduler.run_scheduler()
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")


def create_demo_configs():
    """Create demo configuration files"""
    print("📁 Creating demo configuration files...")
    
    # Create simple demo automation config
    demo_config = {
        "name": "Demo Automation",
        "url": "https://example.com",
        "headless": True,
        "viewport": {
            "width": 1280,
            "height": 720
        },
        "actions": [
            {
                "type": "wait_for_element",
                "selector": "body",
                "timeout": 10000,
                "description": "Wait for page load"
            },
            {
                "type": "wait",
                "value": 2000,
                "description": "Demo wait"
            },
            {
                "type": "log_message",
                "value": {
                    "message": "Demo automation completed successfully",
                    "log_file": "logs/demo_automation.log"
                },
                "description": "Log completion"
            }
        ]
    }
    
    # Ensure configs directory exists
    Path("configs").mkdir(exist_ok=True)
    
    # Write demo config
    with open("configs/demo_automation.json", "w") as f:
        json.dump(demo_config, f, indent=2)
    
    # Create scheduler config for demo
    scheduler_config = {
        "config_files": [
            "configs/demo_automation.json",
            "examples/automaton-example-config.json"
        ],
        "success_wait_time": 15,
        "failure_wait_time": 10,
        "max_retries": 2,
        "timeout_seconds": 300,
        "log_file": "logs/demo_scheduler.log",
        "use_cli": True,
        "verbose": True
    }
    
    with open("configs/demo_scheduler_config.json", "w") as f:
        json.dump(scheduler_config, f, indent=2)
    
    print("✅ Demo configuration files created:")
    print("   - configs/demo_automation.json")
    print("   - configs/demo_scheduler_config.json")


async def main():
    """Main demo function"""
    print("🚀 Automation Scheduler Demo")
    print("=" * 60)
    
    # Show menu
    print("\nAvailable demos:")
    print("1. Basic scheduling demo")
    print("2. Queue management demo")
    print("3. Create demo configuration files")
    print("4. Exit")
    
    try:
        choice = input("\nSelect demo (1-4): ").strip()
        
        if choice == "1":
            await demo_basic_scheduling()
        elif choice == "2":
            await demo_queue_management()
        elif choice == "3":
            create_demo_configs()
        elif choice == "4":
            print("👋 Goodbye!")
            return
        else:
            print("❌ Invalid choice. Please select 1-4.")
    
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"💥 Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())