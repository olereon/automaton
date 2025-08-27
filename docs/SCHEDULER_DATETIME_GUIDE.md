# Automation Scheduler Date/Time Scheduling Guide

## Overview

The automation scheduler now supports scheduling automation runs to start at specific times and dates. This feature allows you to:

- Schedule automations to run at a specific time today
- Schedule automations to run on a future date
- Combine date and time for precise scheduling
- Create daily, weekly, or one-time scheduled runs

## New Parameters

### `--time HH:MM:SS`
Specifies the time when the automation should start.

- **Format**: 24-hour format (HH:MM:SS or HH:MM)
- **Default behavior**: If no date is specified, uses today's date
- **Examples**:
  - `--time 14:30:00` - Start at 2:30 PM
  - `--time 09:00` - Start at 9:00 AM (seconds default to 00)
  - `--time 23:59:59` - Start at 11:59:59 PM

### `--date YYYY-MM-DD`
Specifies the date when the automation should start.

- **Format**: ISO date format (YYYY-MM-DD)
- **Default behavior**: If no time is specified, starts at midnight (00:00:00)
- **Examples**:
  - `--date 2024-12-25` - Start on December 25, 2024
  - `--date 2024-01-01` - Start on January 1, 2024

## Usage Examples

### 1. Schedule for Today at Specific Time

```bash
# Run at 2:30 PM today
python scripts/automation_scheduler.py --config scheduler_config.json --time 14:30:00

# Run at 9 AM today
python scripts/automation_scheduler.py --configs task1.json task2.json --time 09:00:00
```

### 2. Schedule for Specific Date and Time

```bash
# Run on Christmas at 9 AM
python scripts/automation_scheduler.py --config holiday_tasks.json --date 2024-12-25 --time 09:00:00

# Run on New Year's Eve at midnight
python scripts/automation_scheduler.py --config newyear_tasks.json --date 2024-12-31 --time 00:00:00
```

### 3. Schedule for Future Date (Midnight)

```bash
# Run on specific date at midnight
python scripts/automation_scheduler.py --config weekly_tasks.json --date 2024-12-30
```

### 4. Combine with Other Parameters

```bash
# Start from 3rd config at scheduled time
python scripts/automation_scheduler.py --config scheduler_config.json --start-from 3 --time 15:00:00

# Schedule with custom wait times
python scripts/automation_scheduler.py --configs task1.json task2.json --time 10:00:00 --success-wait 600 --failure-wait 120
```

## Configuration File Support

You can also specify scheduled times in your configuration file:

```json
{
  "config_files": [
    "workflows/morning_tasks.json",
    "workflows/afternoon_tasks.json"
  ],
  "success_wait_time": 300,
  "failure_wait_time": 60,
  "max_retries": 3,
  "timeout_seconds": 1800,
  "log_file": "logs/scheduled_automation.log",
  "use_cli": true,
  "verbose": true,
  "scheduled_time": "09:00:00",
  "scheduled_date": "2024-12-25"
}
```

Command-line parameters override configuration file settings:
```bash
# Override config file's scheduled time
python scripts/automation_scheduler.py --config scheduler_config.json --time 10:00:00
```

## Scheduler Behavior

### Waiting for Scheduled Time

1. **Countdown Display**: For waits longer than 60 seconds, the scheduler displays a countdown
2. **Control Support**: You can pause/resume (Ctrl+W) or stop (Ctrl+T) while waiting
3. **Past Times**: If the scheduled time has already passed, the scheduler starts immediately with a warning

### Time Calculation

- **Today's Date**: If only `--time` is specified, the scheduler uses today's date
- **Midnight Start**: If only `--date` is specified, the scheduler starts at midnight (00:00:00)
- **Timezone**: Uses the system's local timezone

### Progress Monitoring

The scheduler provides real-time updates:
- Shows the scheduled start time
- Displays remaining wait time
- Updates countdown periodically
- Logs when scheduled time is reached

## Practical Use Cases

### 1. Daily Morning Automation

Run data collection every morning at 9 AM:
```bash
# Set up as a daily cron job
0 9 * * * python /path/to/automation_scheduler.py --config morning_tasks.json --time 09:00:00
```

### 2. Weekend Processing

Schedule heavy processing for Saturday morning:
```bash
python scripts/automation_scheduler.py --config weekend_processing.json --date 2024-12-28 --time 02:00:00
```

### 3. Business Hours Automation

Run during lunch break to minimize disruption:
```bash
python scripts/automation_scheduler.py --config business_tasks.json --time 12:30:00
```

### 4. Multiple Daily Runs

Create a script for multiple scheduled runs:
```bash
#!/bin/bash
# morning_run.sh
python scripts/automation_scheduler.py --config morning.json --time 09:00:00

# afternoon_run.sh  
python scripts/automation_scheduler.py --config afternoon.json --time 14:00:00

# evening_run.sh
python scripts/automation_scheduler.py --config evening.json --time 18:00:00
```

## Integration with System Schedulers

### Linux/Mac (cron)

Add to crontab for daily execution:
```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/automaton && python scripts/automation_scheduler.py --config daily_tasks.json --time 09:00:00

# Run every Monday at 8 AM
0 8 * * 1 cd /path/to/automaton && python scripts/automation_scheduler.py --config weekly_tasks.json --time 08:00:00
```

### Windows (Task Scheduler)

Create a scheduled task:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Set action to run Python script with parameters:
   ```
   Program: python.exe
   Arguments: C:\path\to\automation_scheduler.py --config tasks.json --time 09:00:00
   ```

## Best Practices

1. **Buffer Time**: Add buffer time between scheduled runs to avoid conflicts
2. **Logging**: Always specify a log file for scheduled runs
3. **Error Handling**: Set appropriate retry counts and wait times
4. **Time Zones**: Be aware of time zone differences if running on remote servers
5. **Testing**: Test scheduled times with short waits first before production use

## Validation and Error Handling

### Time Format Validation

Valid formats:
- `HH:MM:SS` - Full format with seconds
- `HH:MM` - Hours and minutes (seconds default to 00)

Invalid formats will produce an error:
- `25:00:00` - Hour must be 0-23
- `14:60:00` - Minute must be 0-59
- `14:30:60` - Second must be 0-59

### Date Format Validation

Valid format:
- `YYYY-MM-DD` - ISO date format

Invalid formats will produce an error:
- `12/25/2024` - Must use YYYY-MM-DD
- `2024-13-01` - Invalid month
- `2024-02-30` - Invalid day for month

## Troubleshooting

### Common Issues

1. **"Scheduled time has already passed"**
   - The specified time is in the past for today
   - Solution: Either specify a future time or add `--date` for tomorrow

2. **"Invalid time format"**
   - Time is not in HH:MM:SS or HH:MM format
   - Solution: Use 24-hour format with colons

3. **"Invalid date format"**
   - Date is not in YYYY-MM-DD format
   - Solution: Use ISO date format

### Debug Tips

1. **Test with Short Waits**: Use a time just a few seconds in the future for testing
2. **Check Logs**: Review the scheduler log file for detailed information
3. **Verbose Mode**: Use `--verbose` flag for detailed output
4. **Manual Testing**: Test time/date parameters before adding to cron/scheduler

## Examples and Demos

### Test the Feature

Run the test script:
```bash
python tests/test_scheduler_datetime.py
```

### Interactive Demo

Run the demo script to see examples:
```bash
python examples/scheduler_datetime_demo.py
```

## API Reference

### SchedulerConfig Class

New attributes:
```python
@dataclass
class SchedulerConfig:
    # ... existing attributes ...
    scheduled_time: Optional[str] = None  # Time in HH:MM:SS format
    scheduled_date: Optional[str] = None  # Date in YYYY-MM-DD format
```

### Command-Line Arguments

```python
parser.add_argument('--time', type=str, metavar='HH:MM:SS', 
                   help='Schedule start time (e.g., 14:30:00 for 2:30 PM)')
parser.add_argument('--date', type=str, metavar='YYYY-MM-DD',
                   help='Schedule start date (e.g., 2024-12-25)')
```

## Summary

The new date and time scheduling features provide flexible automation scheduling options:

- ✅ Schedule for specific times today
- ✅ Schedule for future dates
- ✅ Combine with existing scheduler features
- ✅ Full control support (pause/resume/stop)
- ✅ Integration with system schedulers
- ✅ Comprehensive validation and error handling

This enhancement makes the automation scheduler suitable for production environments where precise timing is crucial for automated workflows.