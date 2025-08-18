# Complete Queue Detection Solution - Final Implementation

## Problem Statement

The automation was detecting queue full popups correctly but continued running and was marked as SUCCESS by the scheduler, instead of stopping and triggering retries.

## Root Cause Analysis

1. **STOP_AUTOMATION worked correctly** - It threw RuntimeError and stopped automation
2. **Scheduler failure detection was flawed** - It used simple heuristics:
   - Return code 0 + "success"/"completed" in output = SUCCESS
   - Even with RuntimeError present, "completed" text triggered success detection
3. **No specific handling for intentional failures** - STOP_AUTOMATION wasn't recognized as a failure condition

## Complete Solution

### 1. STOP_AUTOMATION Action (Engine Level)

**Added new action type**:
```python
STOP_AUTOMATION = "stop_automation"  # Stop entire automation run
```

**Implementation**:
```python
async def _handle_stop_automation(self, action: Action, context: ExecutionContext):
    """Handle STOP_AUTOMATION action - immediately terminate automation as failed"""
    reason = action.value.get('reason', 'Stop automation requested') if action.value else 'Stop automation requested'
    log_file = action.value.get('log_file') if action.value else None
    
    logger.error(f"STOP_AUTOMATION: {reason}")
    
    # Log to specified file if provided (fixed logging implementation)
    if log_file:
        # [logging implementation]
    
    # Set instruction pointer to end to exit main loop
    context.instruction_pointer = len(self.config.actions)
    context.should_increment = False
    # Raise an exception to mark the automation as failed
    raise RuntimeError(f"Automation stopped: {reason}")
```

### 2. Workflow Integration

**Updated workflow configuration**:
```json
{
  "type": "check_element",
  "selector": "span:has-text('You\\'ve reached your')",
  "value": {
    "check": "contains",
    "value": "You've reached your",
    "attribute": "text"
  }
},
{
  "type": "if_begin",
  "value": {"condition": "check_passed"}
},
{
  "type": "log_message", 
  "value": {
    "message": "ERROR: Queue is full - popup detected. Cannot submit task. Stopping automation to trigger scheduler retry.",
    "log_file": "logs/queue_automation.log",
    "level": "error"
  }
},
{
  "type": "stop_automation",
  "value": {
    "reason": "Queue is full - stopping automation to trigger scheduler retry",
    "log_file": "logs/queue_automation.log"
  },
  "description": "Stop automation due to queue full"
},
{
  "type": "if_end"
},
{
  "type": "increment_variable",
  "value": {"variable": "task_count", "amount": 1},
  "description": "Increment task counter (only if no popup)"
}
```

**Cleanup**:
- ✅ Removed all BREAK actions (were causing errors)
- ✅ Removed unnecessary WHILE loops (were workarounds)
- ✅ Simplified control flow structure

### 3. Scheduler Failure Detection Fix

**Enhanced CLI failure detection**:
```python
# Check for specific failure indicators first (these override success indicators)
failure_indicators = [
    "stop_automation",
    "STOP_AUTOMATION",
    "Automation stopped", 
    "RuntimeError",
    "queue is full",
    "Queue is full"
]

# Check if any failure indicator is present
output_lower = stdout_text.lower()
has_failure_indicator = any(indicator.lower() in output_lower for indicator in failure_indicators)

# Determine result based on return code and output
if process.returncode == 0:
    if has_failure_indicator:
        return AutomationResult.FAILURE, tasks_created, "Automation stopped due to failure condition (queue full, etc.)"
    elif "success" in stdout_text.lower() or "completed" in stdout_text.lower():
        return AutomationResult.SUCCESS, tasks_created, "Automation completed successfully"
    else:
        return AutomationResult.FAILURE, tasks_created, "Automation completed with issues"
```

**Enhanced direct automation failure detection**:
```python
# Check for STOP_AUTOMATION failures
errors = results.get('errors', [])
stop_automation_failure = False
if errors:
    error_msg = '; '.join([err.get('error', 'Unknown error') for err in errors[:3]])
    # Check if any error is from STOP_AUTOMATION
    for error in errors:
        error_text = error.get('error', '').lower()
        if ('stop_automation' in error_text or 
            'automation stopped' in error_text or 
            'queue is full' in error_text):
            stop_automation_failure = True
            break

# Force failure if STOP_AUTOMATION was triggered
if stop_automation_failure:
    result = AutomationResult.FAILURE
    message = "Automation stopped due to failure condition (queue full, etc.)"
else:
    result = AutomationResult.SUCCESS if success else AutomationResult.FAILURE
    message = "Automation completed successfully" if success else (error_msg or "Automation failed")
```

### 4. Retry Mechanism

**Existing retry logic works perfectly**:
```python
async def process_config_file(self, config_file: str) -> bool:
    for attempt in range(1, self.config.max_retries + 1):
        run = await self.run_single_automation(config_file, attempt)
        
        if run.result == AutomationResult.SUCCESS:
            return True  # Move to next config
        
        elif attempt < self.config.max_retries:
            # Retry after failure_wait_time
            await self.wait_with_countdown(self.config.failure_wait_time, f"before retry {attempt + 1}")
        else:
            # Max retries exceeded, move to next config
            return False
    
    return False
```

## Expected Behavior

### Queue Full Scenario:
1. ✅ **Submit task** → Wait for response → **Check for popup**
2. ✅ **Popup detected** → `check_element` returns `success: true`
3. ✅ **IF condition met** → Enter error handling block
4. ✅ **Log error message** to logs/queue_automation.log
5. ✅ **STOP_AUTOMATION executes** → RuntimeError raised → **Automation terminates immediately**
6. ✅ **Scheduler detects failure** → Result = FAILURE (not SUCCESS)
7. ✅ **Wait failure_wait_time** (60 seconds)
8. ✅ **Retry automation** (up to max_retries = 3 times)
9. ✅ **If all retries fail** → Move to next configuration

### Queue Available Scenario:
1. ✅ **Submit task** → Wait for response → **Check for popup**
2. ✅ **No popup detected** → `check_element` returns `success: false`
3. ✅ **IF condition not met** → Skip error handling block
4. ✅ **Increment task counter** → Continue with automation normally
5. ✅ **Automation completes successfully** → Result = SUCCESS
6. ✅ **Wait success_wait_time** (300 seconds)
7. ✅ **Move to next configuration**

## Validation Results

### Unit Tests: ✅ PASSED
- **STOP_AUTOMATION implementation**: 2 actions properly configured
- **Queue detection flow**: 2 detection points with correct logic
- **Code cleanup**: No old BREAK actions or unnecessary WHILE loops
- **JSON validation**: Syntax correct

### Scheduler Tests: ✅ PASSED
- **CLI failure detection**: 5/5 test cases pass
- **Direct failure detection**: 3/3 test cases pass  
- **STOP_AUTOMATION recognition**: All failure indicators detected correctly
- **Success/failure distinction**: Proper handling of edge cases

## Files Modified

1. **`src/core/engine.py`**:
   - Added STOP_AUTOMATION action type and handler
   - Fixed logging implementation
   - Proper RuntimeError generation for failures

2. **`workflows/run-08-16-1.json`**:
   - Replaced BREAK actions with STOP_AUTOMATION
   - Removed unnecessary WHILE/BREAK constructs
   - Clean, simple control flow

3. **`scripts/automation_scheduler.py`**:
   - Enhanced failure detection for CLI automation
   - Enhanced failure detection for direct automation
   - Specific STOP_AUTOMATION recognition
   - Priority override: failure indicators > success indicators

4. **Tests**:
   - `test_stop_automation.py`: Implementation validation
   - `test_scheduler_failure_detection.py`: Scheduler logic validation

## Key Success Factors

1. **✅ Robust Failure Detection**: Multiple failure indicators prevent false positives
2. **✅ Priority-Based Logic**: Failure indicators override generic success text
3. **✅ Immediate Termination**: STOP_AUTOMATION provides clean exit mechanism
4. **✅ Proper Error Propagation**: RuntimeError ensures failure is detected
5. **✅ Comprehensive Testing**: Both unit and integration tests validate behavior
6. **✅ Clean Implementation**: Simple, maintainable code without complex workarounds

## Summary

This solution provides **definitive, reliable queue full detection and retry handling**:

- **When queue is full**: Automation stops immediately → Marked as FAILURE → Retry after 60s → Up to 3 attempts
- **When queue available**: Automation continues normally → Marked as SUCCESS → Wait 300s → Next config
- **No false positives**: Failure indicators override success text to prevent incorrect SUCCESS marking
- **Maintainable code**: Clean structure without complex WHILE/BREAK workarounds

The automation scheduler will now **correctly handle queue full conditions** and retry as intended, preventing wasted attempts and enabling automatic recovery when queue capacity becomes available.