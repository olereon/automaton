# 🔄 Conditional Flow Control Guide

## Overview

Conditional flow control allows your automation to make decisions based on CHECK_ELEMENT results. This enables:

- ⏳ **Retry Logic**: Wait and retry when conditions aren't met (queue full)
- 🚫 **Skip Logic**: Skip actions when conditions are met (at limit)
- 🔁 **Loop Logic**: Repeat checks until success or timeout
- ⏰ **Scheduled Execution**: Retry at specific times or intervals

## New Action Types

### CONDITIONAL_WAIT

Waits and retries based on the result of the previous CHECK_ELEMENT action.

```python
.add_conditional_wait(
    condition="check_failed",  # When to retry
    wait_time=30000,          # Wait 30 seconds
    max_retries=5,            # Try up to 5 times
    retry_from_action=2       # Which action to retry from
)
```

**Conditions:**
- `check_failed`: Retry if previous check returned false
- `check_passed`: Retry if previous check returned true
- `value_equals`: Retry if value equals expected
- `value_not_equals`: Retry if value doesn't equal expected

### SKIP_IF

Skips the next N actions based on check results.

```python
.add_skip_if(
    condition="check_passed",  # When to skip
    skip_count=3              # Number of actions to skip
)
```

## Queue Management Example

### Scenario: Task Queue with 8-Item Limit

```python
# Check if queue has space
.add_check_element(
    selector=".queue-count",
    check_type="less",
    expected_value="8",
    attribute="text",
    description="Check queue < 8"
)

# Wait and retry if full
.add_conditional_wait(
    condition="check_failed",  # Queue >= 8
    wait_time=30000,          # Wait 30 seconds
    max_retries=5,            # Try 5 times
    retry_from_action=0       # Retry from check
)

# Add task if space available
.add_click_button("button.add-task")
```

## Complete Flow Patterns

### Pattern 1: Wait Until Space Available

```python
builder = AutomationSequenceBuilder("Queue Wait", url)

automation = (builder
    # 1. Check queue
    .add_check_element(".queue-count", "less", "8", "text")
    
    # 2. Wait if full
    .add_conditional_wait(
        condition="check_failed",
        wait_time=60000,      # 1 minute
        max_retries=10,       # Try 10 times
        retry_from_action=0   # Retry check
    )
    
    # 3. Process when space available
    .add_click_button("button.process")
    .build()
)
```

### Pattern 2: Skip If At Limit

```python
builder = AutomationSequenceBuilder("Skip If Full", url)

automation = (builder
    # 1. Check if at max
    .add_check_element(".queue-count", "equals", "8", "text")
    
    # 2. Skip task creation if full
    .add_skip_if(
        condition="check_passed",  # Queue == 8
        skip_count=3              # Skip next 3 actions
    )
    
    # 3. These get skipped if full
    .add_click_button("button.add")
    .add_input_text("input.name", "Task")
    .add_click_button("button.submit")
    
    # 4. This always runs
    .add_refresh_page()
    .build()
)
```

### Pattern 3: Different Actions Based on Count

```python
# Check different thresholds
automation = (builder
    # If < 4: Add multiple tasks
    .add_check_element(".count", "less", "4", "text")
    .add_skip_if("check_failed", skip_count=2)
    .add_click_button("button.add")  # Runs if < 4
    .add_click_button("button.add")  # Runs if < 4
    
    # If = 7: Wait for space
    .add_check_element(".count", "equals", "7", "text")
    .add_conditional_wait("check_passed", wait_time=10000)
    
    # If = 8: Skip entirely
    .add_check_element(".count", "equals", "8", "text")
    .add_skip_if("check_passed", skip_count=1)
    
    # Default: Add one task
    .add_click_button("button.add")
    .build()
)
```

## How It Works

### Execution Flow

1. **CHECK_ELEMENT** stores its result internally
2. **CONDITIONAL_WAIT** reads the last check result:
   - If condition met → Wait specified time
   - Increment retry counter
   - Jump back to retry_from_action
   - If max_retries reached → Continue forward
3. **SKIP_IF** reads the last check result:
   - If condition met → Skip next N actions
   - Otherwise → Continue normally

### Action Indexing

Actions are numbered starting from 0:
```
Action 0: add_wait(2000)
Action 1: add_check_element(...)     ← Check happens here
Action 2: add_conditional_wait(...)  ← Reads result from Action 1
Action 3: add_click_button(...)      ← Runs if check passed
```

When using `retry_from_action`, specify the index of the action to retry from.

## Advanced Examples

### Retry with Exponential Backoff

```python
# First attempt - wait 5 seconds
.add_check_element(".status", "equals", "ready", "text")
.add_conditional_wait("check_failed", wait_time=5000, max_retries=1)

# Second attempt - wait 10 seconds  
.add_check_element(".status", "equals", "ready", "text")
.add_conditional_wait("check_failed", wait_time=10000, max_retries=1)

# Third attempt - wait 20 seconds
.add_check_element(".status", "equals", "ready", "text")
.add_conditional_wait("check_failed", wait_time=20000, max_retries=1)
```

### Multiple Condition Checks

```python
# Check condition A
.add_check_element(".conditionA", "equals", "true", "text")
.add_skip_if("check_failed", skip_count=5)  # Skip if A is false

# Check condition B (only if A was true)
.add_check_element(".conditionB", "equals", "true", "text")
.add_skip_if("check_failed", skip_count=3)  # Skip if B is false

# Actions that run only if both A and B are true
.add_click_button("button.action1")
.add_click_button("button.action2")
.add_click_button("button.action3")
```

### Scheduled Execution

```python
from datetime import datetime, timedelta

# Calculate wait until next hour
now = datetime.now()
next_hour = now.replace(minute=0, second=0) + timedelta(hours=1)
wait_ms = int((next_hour - now).total_seconds() * 1000)

automation = (builder
    .add_wait(wait_ms, f"Wait until {next_hour.strftime('%H:%M')}")
    .add_check_element(".queue", "less", "8", "text")
    .add_conditional_wait(
        condition="check_failed",
        wait_time=3600000,  # 1 hour
        max_retries=24      # Retry for 24 hours
    )
    .add_click_button("button.process")
    .build()
)
```

## JSON Configuration

```json
{
  "actions": [
    {
      "type": "check_element",
      "selector": ".queue-count",
      "value": {
        "check": "less",
        "value": "8",
        "attribute": "text"
      },
      "description": "Check queue space"
    },
    {
      "type": "conditional_wait",
      "value": {
        "condition": "check_failed",
        "wait_time": 30000,
        "max_retries": 5,
        "retry_from_action": 0
      },
      "description": "Wait if queue full"
    },
    {
      "type": "skip_if",
      "value": {
        "condition": "value_equals",
        "expected_value": "8",
        "skip_count": 2
      },
      "description": "Skip if at max"
    }
  ]
}
```

## Tips and Best Practices

1. **Always Check First**: Place CHECK_ELEMENT before conditional actions
2. **Set Reasonable Timeouts**: Don't retry forever - set max_retries
3. **Use Descriptive Names**: Make descriptions clear for debugging
4. **Test Edge Cases**: Test when queue is empty, full, and in-between
5. **Consider Network Delays**: Add small waits after clicks for page updates
6. **Log Results**: Check results are stored in outputs for debugging

## Troubleshooting

### "No previous check result"
- Ensure CHECK_ELEMENT comes before CONDITIONAL_WAIT/SKIP_IF
- Check that the CHECK_ELEMENT didn't throw an error

### Infinite Loops
- Set reasonable max_retries (usually 3-10)
- Add increasing wait times for each retry
- Consider adding a SKIP_IF as a circuit breaker

### Wrong Actions Skipped
- Remember action indices start at 0
- Count all actions including waits
- Use descriptions to track which actions are skippable

## Complete Working Example

```python
async def smart_queue_management():
    """Production-ready queue management"""
    
    builder = AutomationSequenceBuilder(
        name="Smart Queue Manager",
        url="https://yourapp.com"
    )
    
    automation = (builder
        .set_headless(False)
        .add_wait(2000, "Initial page load")
        
        # Step 1: Login if needed
        .add_check_element(".login-status", "equals", "logged-in", 
                          "data-status", "Check login status")
        .add_skip_if("check_passed", skip_count=1, 
                    description="Skip login if already logged in")
        .add_click_button(".login-btn", "Perform login")
        
        # Step 2: Check queue capacity
        .add_wait(1000, "Wait for queue to load")
        .add_check_element(".queue-count", "less", "8", "text",
                          "Check queue has space")
        
        # Step 3: Handle full queue
        .add_conditional_wait(
            condition="check_failed",
            wait_time=30000,  # 30 seconds
            max_retries=10,   # Try for 5 minutes
            retry_from_action=4,  # Retry from queue check
            description="Wait for queue space"
        )
        
        # Step 4: Add task (only if space available)
        .add_click_button("#add-task-btn", "Open task dialog")
        .add_input_text("#task-name", "Automated Task", "Enter task name")
        .add_click_button("#submit-btn", "Submit task")
        
        # Step 5: Verify success
        .add_wait(2000, "Wait for confirmation")
        .add_check_element(".success-message", "contains", "added",
                          "text", "Verify task added")
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    return await engine.run_automation()
```

This gives you complete control over automation flow based on dynamic page conditions!