#!/usr/bin/env python3
"""
Demonstration of the new date and time scheduling features for automation_scheduler.

This script shows how to use the new --time and --date parameters to schedule
automations to run at specific times and dates.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.automation_scheduler import AutomationScheduler, SchedulerConfig


def create_demo_configs():
    """Create demo configuration files for scheduled runs"""
    configs_dir = Path("examples/scheduled_configs")
    configs_dir.mkdir(exist_ok=True)
    
    # Create morning automation config
    morning_config = {
        "name": "Morning Automation",
        "url": "https://example.com/morning",
        "headless": True,
        "viewport": {"width": 1280, "height": 720},
        "actions": [
            {
                "type": "wait_for_element",
                "selector": "body",
                "timeout": 10000,
                "description": "Wait for page load"
            },
            {
                "type": "log_message",
                "value": {
                    "message": f"Morning automation executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "log_file": "logs/morning_automation.log"
                },
                "description": "Log morning execution"
            }
        ]
    }
    
    # Create afternoon automation config
    afternoon_config = {
        "name": "Afternoon Automation",
        "url": "https://example.com/afternoon",
        "headless": True,
        "viewport": {"width": 1280, "height": 720},
        "actions": [
            {
                "type": "wait_for_element",
                "selector": "body",
                "timeout": 10000,
                "description": "Wait for page load"
            },
            {
                "type": "log_message",
                "value": {
                    "message": f"Afternoon automation executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "log_file": "logs/afternoon_automation.log"
                },
                "description": "Log afternoon execution"
            }
        ]
    }
    
    # Write configs
    morning_file = configs_dir / "morning_automation.json"
    afternoon_file = configs_dir / "afternoon_automation.json"
    
    with open(morning_file, "w") as f:
        json.dump(morning_config, f, indent=2)
    
    with open(afternoon_file, "w") as f:
        json.dump(afternoon_config, f, indent=2)
    
    return str(morning_file), str(afternoon_file)


async def demo_schedule_time_today():
    """Demo: Schedule automation for a specific time today"""
    print("\n" + "="*60)
    print("DEMO 1: Schedule for Specific Time Today")
    print("="*60)
    
    morning_config, afternoon_config = create_demo_configs()
    
    # Schedule for 10 seconds from now (for demo purposes)
    now = datetime.now()
    scheduled = now + timedelta(seconds=10)
    scheduled_time = scheduled.strftime("%H:%M:%S")
    
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scheduling automation for: {scheduled_time} (in 10 seconds)")
    print("\nThis demonstrates scheduling an automation to run at a specific time today.")
    print("In production, you might schedule for 09:00:00 for morning tasks.")
    
    config = SchedulerConfig(
        config_files=[morning_config],
        success_wait_time=5,
        failure_wait_time=5,
        max_retries=1,
        timeout_seconds=60,
        log_file="logs/demo_scheduled_time.log",
        use_cli=True,
        verbose=True,
        scheduled_time=scheduled_time,
        scheduled_date=None  # None means today
    )
    
    scheduler = AutomationScheduler(config)
    
    print("\n⏰ Scheduler will wait until the scheduled time...")
    print("Press Ctrl+C to cancel\n")
    
    try:
        # Run for demonstration
        task = asyncio.create_task(scheduler.run_scheduler())
        await asyncio.sleep(15)  # Wait for execution
        scheduler.stop_scheduler()
        await task
    except KeyboardInterrupt:
        print("\n⚠️ Demo cancelled by user")
    except:
        pass
    
    print("\n✅ Demo completed!")


async def demo_schedule_specific_date():
    """Demo: Schedule automation for a specific date and time"""
    print("\n" + "="*60)
    print("DEMO 2: Schedule for Specific Date and Time")
    print("="*60)
    
    morning_config, afternoon_config = create_demo_configs()
    
    # Schedule for tomorrow at 9 AM
    tomorrow = datetime.now() + timedelta(days=1)
    scheduled_date = tomorrow.strftime("%Y-%m-%d")
    scheduled_time = "09:00:00"
    
    print(f"Current datetime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scheduling for: {scheduled_date} at {scheduled_time}")
    print("\nThis demonstrates scheduling an automation for a future date.")
    print("Perfect for scheduling weekend or holiday automations.")
    
    config = SchedulerConfig(
        config_files=[morning_config, afternoon_config],
        success_wait_time=300,  # 5 minutes between configs
        failure_wait_time=60,
        max_retries=2,
        timeout_seconds=600,
        log_file="logs/demo_scheduled_date.log",
        use_cli=True,
        verbose=True,
        scheduled_time=scheduled_time,
        scheduled_date=scheduled_date
    )
    
    scheduler = AutomationScheduler(config)
    
    print("\n📅 Scheduler configured for future date and time")
    print("In production, this would wait until the scheduled datetime.")
    print("For demo purposes, we'll just show the configuration.\n")
    
    # Just start and immediately stop for demo
    task = asyncio.create_task(scheduler.run_scheduler())
    await asyncio.sleep(2)
    scheduler.stop_scheduler()
    
    try:
        await task
    except:
        pass
    
    print("✅ Demo completed!")


async def demo_multiple_schedules():
    """Demo: Show how to create multiple scheduled runs"""
    print("\n" + "="*60)
    print("DEMO 3: Multiple Scheduled Runs (Configuration)")
    print("="*60)
    
    print("Example scheduler configuration for multiple daily runs:\n")
    
    # Create example configuration for multiple scheduled runs
    scheduler_config = {
        "morning_run": {
            "config_files": [
                "workflows/morning_tasks.json",
                "workflows/data_collection.json"
            ],
            "scheduled_time": "09:00:00",
            "scheduled_date": None,  # Run daily
            "success_wait_time": 300,
            "failure_wait_time": 60,
            "max_retries": 3
        },
        "afternoon_run": {
            "config_files": [
                "workflows/afternoon_tasks.json",
                "workflows/report_generation.json"
            ],
            "scheduled_time": "14:30:00",
            "scheduled_date": None,  # Run daily
            "success_wait_time": 300,
            "failure_wait_time": 60,
            "max_retries": 3
        },
        "evening_run": {
            "config_files": [
                "workflows/evening_cleanup.json",
                "workflows/backup_tasks.json"
            ],
            "scheduled_time": "18:00:00",
            "scheduled_date": None,  # Run daily
            "success_wait_time": 300,
            "failure_wait_time": 60,
            "max_retries": 3
        }
    }
    
    print("📋 Daily Schedule Configuration:")
    for name, config in scheduler_config.items():
        time = config["scheduled_time"]
        files = len(config["config_files"])
        print(f"  • {name}: {time} - {files} automation configs")
    
    print("\n💡 Tips for using scheduled automations:")
    print("  1. Use cron or Windows Task Scheduler for recurring daily runs")
    print("  2. Schedule during off-peak hours for better performance")
    print("  3. Add sufficient wait times between configs to avoid rate limiting")
    print("  4. Monitor logs regularly for any failed automations")
    print("  5. Use --date parameter for one-time future runs")
    
    # Save example configuration
    config_file = Path("examples/scheduled_configs/daily_schedule.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, "w") as f:
        json.dump(scheduler_config, f, indent=2)
    
    print(f"\n📄 Example configuration saved to: {config_file}")
    print("✅ Demo completed!")


async def demo_command_line_examples():
    """Show command-line usage examples"""
    print("\n" + "="*60)
    print("DEMO 4: Command-Line Usage Examples")
    print("="*60)
    
    examples = [
        {
            "description": "Schedule for 2:30 PM today",
            "command": "python automation_scheduler.py --config scheduler_config.json --time 14:30:00"
        },
        {
            "description": "Schedule for 9 AM tomorrow",
            "command": "python automation_scheduler.py --config scheduler_config.json --date 2024-12-26 --time 09:00:00"
        },
        {
            "description": "Schedule for specific date at midnight",
            "command": "python automation_scheduler.py --config scheduler_config.json --date 2024-12-31 --time 00:00:00"
        },
        {
            "description": "Schedule with custom configs and time",
            "command": "python automation_scheduler.py --configs task1.json task2.json --time 10:00:00 --success-wait 600"
        },
        {
            "description": "Schedule for next Monday at 8 AM",
            "command": "python automation_scheduler.py --config weekly_tasks.json --date 2024-12-30 --time 08:00:00"
        },
        {
            "description": "Start from 3rd config at scheduled time",
            "command": "python automation_scheduler.py --config scheduler_config.json --start-from 3 --time 15:00:00"
        }
    ]
    
    print("📝 Command-Line Examples:\n")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}:")
        print(f"   $ {example['command']}\n")
    
    print("💡 Pro Tips:")
    print("  • Time format: HH:MM:SS (24-hour format)")
    print("  • Date format: YYYY-MM-DD")
    print("  • If only --time is specified, uses today's date")
    print("  • If only --date is specified, starts at midnight")
    print("  • Past times will start immediately with a warning")
    print("  • Scheduler shows countdown for long waits")
    
    print("\n✅ Demo completed!")


async def main():
    """Main demo menu"""
    print("🚀 Automation Scheduler Date/Time Features Demo")
    print("="*80)
    print("\nThis demo showcases the new scheduling features that allow you to:")
    print("  • Schedule automations for specific times (--time HH:MM:SS)")
    print("  • Schedule automations for specific dates (--date YYYY-MM-DD)")
    print("  • Combine date and time for precise scheduling")
    
    while True:
        print("\n" + "="*60)
        print("Available Demos:")
        print("1. Schedule for specific time today")
        print("2. Schedule for specific date and time")
        print("3. Multiple scheduled runs configuration")
        print("4. Command-line usage examples")
        print("5. Exit")
        
        try:
            choice = input("\nSelect demo (1-5): ").strip()
            
            if choice == "1":
                await demo_schedule_time_today()
            elif choice == "2":
                await demo_schedule_specific_date()
            elif choice == "3":
                await demo_multiple_schedules()
            elif choice == "4":
                await demo_command_line_examples()
            elif choice == "5":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n💥 Demo error: {e}")


if __name__ == "__main__":
    asyncio.run(main())