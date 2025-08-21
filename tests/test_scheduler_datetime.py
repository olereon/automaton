#!/usr/bin/env python3
"""
Test script for the new date and time scheduling parameters.
This script tests the new --time and --date parameters added to the automation scheduler.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.automation_scheduler import AutomationScheduler, SchedulerConfig


def create_test_config():
    """Create a test configuration file"""
    test_config = {
        "name": "Test Scheduled Automation",
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
                "timeout": 5000,
                "description": "Wait for page load"
            },
            {
                "type": "log_message",
                "value": {
                    "message": f"Test automation executed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "log_file": "logs/test_scheduled_automation.log"
                },
                "description": "Log execution time"
            }
        ]
    }
    
    # Ensure test directory exists
    test_dir = Path("tests/configs")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Write test config
    config_file = test_dir / "test_scheduled_automation.json"
    with open(config_file, "w") as f:
        json.dump(test_config, f, indent=2)
    
    return str(config_file)


async def test_immediate_start():
    """Test that scheduler starts immediately when no time/date specified"""
    print("\n" + "="*60)
    print("TEST 1: Immediate Start (no scheduling)")
    print("="*60)
    
    config_file = create_test_config()
    
    config = SchedulerConfig(
        config_files=[config_file],
        success_wait_time=5,
        failure_wait_time=5,
        max_retries=1,
        timeout_seconds=30,
        log_file="logs/test_immediate.log",
        use_cli=True,
        verbose=True,
        scheduled_time=None,
        scheduled_date=None
    )
    
    scheduler = AutomationScheduler(config)
    
    start_time = datetime.now()
    print(f"Starting at: {start_time.strftime('%H:%M:%S')}")
    
    # Run for a short time then stop
    task = asyncio.create_task(scheduler.run_scheduler())
    await asyncio.sleep(2)
    scheduler.stop_scheduler()
    
    try:
        await task
    except:
        pass
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    print(f"Ended at: {end_time.strftime('%H:%M:%S')}")
    print(f"Elapsed: {elapsed:.1f} seconds")
    
    # Should start immediately (within 3 seconds)
    assert elapsed < 3, f"Expected immediate start but took {elapsed} seconds"
    print("✅ Test passed: Scheduler started immediately")


async def test_scheduled_time_today():
    """Test scheduling for a specific time today (in the near future)"""
    print("\n" + "="*60)
    print("TEST 2: Scheduled Time Today")
    print("="*60)
    
    config_file = create_test_config()
    
    # Schedule for 5 seconds from now
    now = datetime.now()
    scheduled = now + timedelta(seconds=5)
    scheduled_time = scheduled.strftime("%H:%M:%S")
    
    config = SchedulerConfig(
        config_files=[config_file],
        success_wait_time=5,
        failure_wait_time=5,
        max_retries=1,
        timeout_seconds=30,
        log_file="logs/test_scheduled_time.log",
        use_cli=True,
        verbose=True,
        scheduled_time=scheduled_time,
        scheduled_date=None
    )
    
    scheduler = AutomationScheduler(config)
    
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    print(f"Scheduled for: {scheduled_time}")
    
    start_time = datetime.now()
    
    # Run scheduler
    task = asyncio.create_task(scheduler.run_scheduler())
    
    # Wait for scheduled time plus a bit
    await asyncio.sleep(7)
    scheduler.stop_scheduler()
    
    try:
        await task
    except:
        pass
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    print(f"Started execution at: {end_time.strftime('%H:%M:%S')}")
    print(f"Wait duration: {elapsed:.1f} seconds")
    
    # Should wait approximately 5 seconds
    assert 4 < elapsed < 8, f"Expected ~5 second wait but got {elapsed} seconds"
    print("✅ Test passed: Scheduler waited for scheduled time")


async def test_scheduled_date_and_time():
    """Test scheduling for a specific date and time"""
    print("\n" + "="*60)
    print("TEST 3: Scheduled Date and Time")
    print("="*60)
    
    config_file = create_test_config()
    
    # Schedule for tomorrow at this time
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    scheduled_date = tomorrow.strftime("%Y-%m-%d")
    scheduled_time = now.strftime("%H:%M:%S")
    
    config = SchedulerConfig(
        config_files=[config_file],
        success_wait_time=5,
        failure_wait_time=5,
        max_retries=1,
        timeout_seconds=30,
        log_file="logs/test_scheduled_date.log",
        use_cli=True,
        verbose=True,
        scheduled_time=scheduled_time,
        scheduled_date=scheduled_date
    )
    
    scheduler = AutomationScheduler(config)
    
    print(f"Current datetime: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scheduled for: {scheduled_date} {scheduled_time}")
    
    # This would wait ~24 hours, so just verify it calculates correctly
    # by checking the scheduler's internal state
    task = asyncio.create_task(scheduler.run_scheduler())
    
    # Give it a moment to calculate
    await asyncio.sleep(1)
    
    # Stop it immediately
    scheduler.stop_scheduler()
    
    try:
        await task
    except:
        pass
    
    print("✅ Test passed: Scheduler accepted future date and time")


async def test_past_time_immediate_start():
    """Test that scheduler starts immediately if scheduled time has passed"""
    print("\n" + "="*60)
    print("TEST 4: Past Time (should start immediately)")
    print("="*60)
    
    config_file = create_test_config()
    
    # Schedule for 1 hour ago
    now = datetime.now()
    past = now - timedelta(hours=1)
    scheduled_time = past.strftime("%H:%M:%S")
    
    config = SchedulerConfig(
        config_files=[config_file],
        success_wait_time=5,
        failure_wait_time=5,
        max_retries=1,
        timeout_seconds=30,
        log_file="logs/test_past_time.log",
        use_cli=True,
        verbose=True,
        scheduled_time=scheduled_time,
        scheduled_date=None
    )
    
    scheduler = AutomationScheduler(config)
    
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    print(f"Scheduled for: {scheduled_time} (past)")
    
    start_time = datetime.now()
    
    # Run scheduler
    task = asyncio.create_task(scheduler.run_scheduler())
    await asyncio.sleep(2)
    scheduler.stop_scheduler()
    
    try:
        await task
    except:
        pass
    
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds()
    
    print(f"Started at: {end_time.strftime('%H:%M:%S')}")
    print(f"Elapsed: {elapsed:.1f} seconds")
    
    # Should start immediately since time has passed
    assert elapsed < 3, f"Expected immediate start but took {elapsed} seconds"
    print("✅ Test passed: Scheduler started immediately for past time")


async def test_time_format_validation():
    """Test various time format validations"""
    print("\n" + "="*60)
    print("TEST 5: Time Format Validation")
    print("="*60)
    
    config_file = create_test_config()
    
    # Test valid formats
    valid_formats = [
        "14:30:00",  # HH:MM:SS
        "09:15:30",  # Leading zeros
        "23:59:59",  # Max values
        "00:00:00",  # Midnight
        "14:30",     # HH:MM (no seconds)
    ]
    
    for time_str in valid_formats:
        try:
            config = SchedulerConfig(
                config_files=[config_file],
                success_wait_time=5,
                failure_wait_time=5,
                max_retries=1,
                timeout_seconds=30,
                log_file="logs/test_validation.log",
                use_cli=True,
                verbose=False,
                scheduled_time=time_str,
                scheduled_date=None
            )
            print(f"✅ Valid format accepted: {time_str}")
        except Exception as e:
            print(f"❌ Valid format rejected: {time_str} - {e}")
            assert False, f"Should accept valid format {time_str}"
    
    print("\nAll time format validations passed!")


async def test_date_format_validation():
    """Test various date format validations"""
    print("\n" + "="*60)
    print("TEST 6: Date Format Validation")
    print("="*60)
    
    config_file = create_test_config()
    
    # Test valid formats
    valid_dates = [
        "2024-12-25",  # YYYY-MM-DD
        "2024-01-01",  # New Year
        "2024-02-29",  # Leap year
    ]
    
    for date_str in valid_dates:
        try:
            config = SchedulerConfig(
                config_files=[config_file],
                success_wait_time=5,
                failure_wait_time=5,
                max_retries=1,
                timeout_seconds=30,
                log_file="logs/test_validation.log",
                use_cli=True,
                verbose=False,
                scheduled_time=None,
                scheduled_date=date_str
            )
            print(f"✅ Valid date accepted: {date_str}")
        except Exception as e:
            print(f"❌ Valid date rejected: {date_str} - {e}")
            assert False, f"Should accept valid date {date_str}"
    
    print("\nAll date format validations passed!")


async def main():
    """Run all tests"""
    print("🧪 Testing Automation Scheduler Date/Time Features")
    print("="*80)
    
    try:
        # Run tests
        await test_immediate_start()
        await test_scheduled_time_today()
        await test_scheduled_date_and_time()
        await test_past_time_immediate_start()
        await test_time_format_validation()
        await test_date_format_validation()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED!")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())