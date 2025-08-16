# Automation Scheduler Guide

## Overview

The Automation Scheduler is a powerful Python script that manages sequential execution of multiple automation configurations with intelligent retry logic, timing controls, and comprehensive reporting.

## Features

### ✅ Core Capabilities
- **Sequential Execution**: Process multiple automation configurations in order
- **Retry Logic**: Configurable retry attempts for failed automations
- **Smart Timing**: Different wait times for success and failure scenarios
- **Comprehensive Logging**: Detailed execution tracking and reporting
- **Multiple Interfaces**: Support for both CLI and direct engine execution
- **Task Counting**: Automatic detection and reporting of created tasks
- **JSON Configuration**: Flexible configuration through JSON files
- **Real-time Progress**: Live countdown timers and status updates

### 🎯 Use Cases
- **Batch Processing**: Run multiple automation workflows automatically
- **Scheduled Operations**: Execute automations with precise timing
- **Queue Management**: Create multiple tasks across different time periods
- **Testing & Validation**: Automated testing of multiple configurations
- **Production Workflows**: Reliable execution with error handling and retries

## Installation and Setup

### Prerequisites
```bash
# Ensure automation framework is installed
cd /path/to/automaton
pip install -r requirements.txt
playwright install chromium
```

### Script Location
The scheduler script is located at:
```
scripts/automation_scheduler.py
```

## Usage

### Command Line Interface

#### Basic Usage with Configuration File
```bash
python scripts/automation_scheduler.py --config configs/scheduler_config.json
```

#### Direct Configuration via Command Line
```bash
python scripts/automation_scheduler.py \
  --configs workflow1.json workflow2.json workflow3.json \
  --success-wait 300 \
  --failure-wait 60 \
  --max-retries 3 \
  --timeout 1800
```

#### Create Example Configuration
```bash
python scripts/automation_scheduler.py --create-example
```

### Configuration File Format

#### scheduler_config.json
```json
{
  "config_files": [
    "workflows/user_while-loop-1.json",
    "workflows/user_while-loop-2.json", 
    "examples/queue_management_example.json"
  ],
  "success_wait_time": 300,
  "failure_wait_time": 60,
  "max_retries": 3,
  "timeout_seconds": 1800,
  "log_file": "logs/automation_scheduler.log",
  "use_cli": true,
  "verbose": true
}
```

#### Configuration Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|--------|
| `config_files` | List of automation configuration files | `[]` | Array of file paths |
| `success_wait_time` | Wait time after successful automation (seconds) | `300` | 0-86400 |
| `failure_wait_time` | Wait time before retry after failure (seconds) | `60` | 0-3600 |
| `max_retries` | Maximum retry attempts per configuration | `3` | 1-10 |
| `timeout_seconds` | Timeout per automation run (seconds) | `1800` | 60-7200 |
| `log_file` | Path to log file | `logs/automation_scheduler.log` | String |
| `use_cli` | Use CLI interface (recommended) | `true` | Boolean |
| `verbose` | Enable detailed logging | `true` | Boolean |

## Execution Flow

### 🔄 Main Process Loop

1. **Initialize**: Load configuration and setup logging
2. **Validate**: Check all configuration files exist
3. **Process Each Configuration**:
   - Attempt automation execution
   - On success: Wait `success_wait_time` → Continue to next config
   - On failure: Wait `failure_wait_time` → Retry (up to `max_retries`)
   - On timeout/error: Log and proceed based on retry logic
4. **Generate Report**: Comprehensive summary with statistics

### 📊 Retry Logic

```
For each configuration file:
├── Attempt 1
│   ├── Success → Wait T1 → Next config
│   └── Failure → Wait T2 → Attempt 2
├── Attempt 2  
│   ├── Success → Wait T1 → Next config
│   └── Failure → Wait T2 → Attempt 3
└── Attempt N (max_retries)
    ├── Success → Wait T1 → Next config
    └── Failure → Log failure → Next config
```

### ⏱️ Timing Controls

- **T1 (success_wait_time)**: Wait after successful automation before starting next configuration
- **T2 (failure_wait_time)**: Wait before retrying failed automation
- **Timeout**: Maximum time allowed per automation run

## Output and Reporting

### 📋 Real-time Console Output

```
🎬 Starting Automation Scheduler
📋 Configurations to process: 3
⏱️  Success wait time: 300s
🔄 Failure wait time: 60s
🎯 Max retries per config: 3

============================================================
📄 Processing 1/3: workflows/user_while-loop-1.json
============================================================

🚀 Starting automation: workflows/user_while-loop-1.json (attempt 1)
✅ SUCCESS: workflows/user_while-loop-1.json - 3 tasks created
🎉 Configuration completed successfully: workflows/user_while-loop-1.json

⏳ Waiting 300 seconds (before next configuration)...
⏳ 5m 0s remaining...
⏳ 4m 0s remaining...
...
```

### 📊 Final Summary Report

```
🎉 ALL jobs are done. The job summary:
================================================================================

📊 AUTOMATION SCHEDULER SUMMARY
================================================================================
⏱️  Total execution time: 1h 15m 30s
📁 Total configurations: 3

✅ workflows/user_while-loop-1.json
   └─ Tasks created: 3
   └─ Duration: 2m 45s
   └─ Attempts: 1
   └─ Completed: 2025-08-16 14:30:15

✅ workflows/user_while-loop-2.json
   └─ Tasks created: 5
   └─ Duration: 4m 12s
   └─ Attempts: 2
   └─ Completed: 2025-08-16 14:45:30

❌ examples/queue_management_example.json
   └─ Result: FAILED after 3 attempts
   └─ Last error: Element not found: .queue-counter
   └─ Last attempt: 2025-08-16 15:10:45

📈 OVERALL STATISTICS
========================================
✅ Successful configurations: 2/3
🎯 Total tasks created: 8
🔄 Total automation runs: 6
⏱️  Average run duration: 3m 28s
📊 Success rate: 66.7%

📄 Detailed report exported to: logs/automation_report.json
```

### 📄 JSON Report Export

Detailed execution data is automatically exported to `logs/automation_report.json`:

```json
{
  "scheduler_config": {
    "config_files": ["workflow1.json", "workflow2.json"],
    "success_wait_time": 300,
    "failure_wait_time": 60,
    "max_retries": 3
  },
  "execution_summary": {
    "total_configs": 2,
    "successful_configs": 2,
    "total_runs": 3,
    "total_tasks_created": 8,
    "start_time": "2025-08-16T14:00:00",
    "end_time": "2025-08-16T15:15:30"
  },
  "runs": [
    {
      "config_file": "workflow1.json",
      "attempt_number": 1,
      "start_time": "2025-08-16T14:00:00",
      "end_time": "2025-08-16T14:02:45",
      "result": "success",
      "tasks_created": 3,
      "duration_seconds": 165.0,
      "error_message": null
    }
  ]
}
```

## Command Line Options

### All Available Options

```bash
python scripts/automation_scheduler.py [OPTIONS]

OPTIONS:
  --config FILE           Scheduler configuration file
  --configs FILE [FILE...]  List of automation config files
  --success-wait SECONDS  Wait time after success (default: 300)
  --failure-wait SECONDS  Wait time before retry (default: 60)
  --max-retries NUMBER    Maximum retry attempts (default: 3)
  --timeout SECONDS       Timeout per automation (default: 1800)
  --log-file FILE         Log file path (default: logs/automation_scheduler.log)
  --use-direct           Use direct engine instead of CLI
  --quiet                Quiet mode (less logging)
  --create-example       Create example configuration
  --help                 Show help message
```

### Usage Examples

#### Production Queue Management
```bash
# Run queue management every 5 minutes with 3 retries
python scripts/automation_scheduler.py \
  --configs workflows/queue_batch_1.json workflows/queue_batch_2.json \
  --success-wait 300 \
  --failure-wait 120 \
  --max-retries 3 \
  --timeout 1200
```

#### Testing and Development
```bash
# Quick testing with shorter waits
python scripts/automation_scheduler.py \
  --configs test_config.json \
  --success-wait 30 \
  --failure-wait 10 \
  --max-retries 1 \
  --timeout 300
```

#### Batch Processing with Custom Logging
```bash
# Custom logging location
python scripts/automation_scheduler.py \
  --config production_scheduler.json \
  --log-file /var/log/automation/scheduler.log
```

## Task Count Detection

The scheduler automatically detects and reports the number of tasks created by each automation:

### Detection Methods

1. **CLI Output Parsing**: Extracts task counts from automation output
   - Patterns: "Total tasks created: N", "task #N", "Successfully created task #N"
   - Uses regex matching to find highest task number

2. **Direct Results Analysis**: For direct engine execution
   - Analyzes `increment_variable` results for task counters
   - Counts successful task submission actions
   - Examines automation outputs for task-related data

3. **Log File Analysis**: Fallback method
   - Parses log files for task creation messages
   - Correlates log entries with execution timeline

## Error Handling and Recovery

### 🔧 Automatic Recovery

- **Timeout Handling**: Graceful process termination and cleanup
- **File Validation**: Pre-execution checks for configuration file existence
- **Dependency Checks**: Validates automation framework availability
- **Resource Cleanup**: Proper browser and process cleanup on failures

### 🚨 Error Categories

1. **Configuration Errors**: Invalid JSON, missing files, parameter validation
2. **Execution Errors**: Automation failures, element not found, network issues
3. **Timeout Errors**: Automations exceeding configured time limits
4. **System Errors**: Resource exhaustion, permission issues, dependency problems

### 🛠️ Recovery Strategies

- **Retry Logic**: Configurable retry attempts with exponential backoff
- **Graceful Degradation**: Continue with remaining configurations on individual failures
- **State Preservation**: Maintain execution state across retries
- **Comprehensive Logging**: Detailed error context for troubleshooting

## Best Practices

### 🎯 Configuration Design

1. **Realistic Timeouts**: Set timeouts based on expected automation duration + buffer
2. **Appropriate Wait Times**: Balance efficiency with system resource considerations
3. **Retry Limits**: Avoid excessive retries that may indicate systematic issues
4. **File Organization**: Use clear, descriptive configuration file names

### 📊 Production Deployment

1. **Resource Monitoring**: Monitor system resources during batch processing
2. **Log Rotation**: Implement log rotation for long-running schedulers
3. **Error Alerting**: Set up monitoring for failed automation batches
4. **Backup Configurations**: Maintain backup copies of working configurations

### 🔍 Debugging and Troubleshooting

1. **Verbose Logging**: Enable verbose mode during development and testing
2. **Individual Testing**: Test configurations individually before batch processing
3. **Browser Debugging**: Use `--show-browser` for visual debugging of automation issues
4. **Log Analysis**: Regularly review logs for patterns in failures or performance issues

## Integration Examples

### 🔄 Cron Job Integration

```bash
# Daily automation batch at 2 AM
0 2 * * * cd /path/to/automaton && python scripts/automation_scheduler.py --config configs/daily_batch.json

# Hourly queue management
0 * * * * cd /path/to/automaton && python scripts/automation_scheduler.py --configs workflows/hourly_queue.json --success-wait 3600
```

### 🐳 Docker Integration

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN playwright install chromium

CMD ["python", "scripts/automation_scheduler.py", "--config", "configs/production_scheduler.json"]
```

### 🔧 CI/CD Pipeline Integration

```yaml
# GitHub Actions example
- name: Run Automation Tests
  run: |
    python scripts/automation_scheduler.py \
      --configs tests/test_*.json \
      --success-wait 30 \
      --failure-wait 10 \
      --max-retries 1 \
      --timeout 300
```

## Troubleshooting

### Common Issues

1. **Configuration File Not Found**
   - Verify file paths are correct and files exist
   - Use absolute paths or ensure working directory is correct

2. **Automation Timeouts**
   - Increase timeout values for complex automations
   - Check network connectivity and site responsiveness

3. **High Failure Rates**
   - Review individual automation configurations
   - Test element selectors and timing assumptions
   - Check for website changes that break automation

4. **Resource Exhaustion**
   - Monitor system resources during execution
   - Reduce concurrent operations or increase wait times
   - Implement resource cleanup in automation configurations

5. **Permission Issues**
   - Ensure write permissions for log directory
   - Check file system permissions for temporary files
   - Validate browser installation and permissions

### Debug Mode

```bash
# Enable maximum debugging
python scripts/automation_scheduler.py \
  --config debug_config.json \
  --verbose \
  --timeout 300
```

## Conclusion

The Automation Scheduler provides a robust, production-ready solution for managing complex automation workflows with intelligent retry logic, comprehensive reporting, and flexible configuration options. It's designed to handle both development testing and production batch processing scenarios with equal reliability.

For additional support and advanced configuration options, refer to the main automation framework documentation and example configurations provided in the repository.