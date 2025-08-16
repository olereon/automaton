# While Loop Automation Guide

## Overview

The Automaton framework supports sophisticated while loop automation for creating complex, conditional workflows. This guide covers the implementation, best practices, and troubleshooting for while loop automations.

## Key Features

### ✅ Recently Fixed Issues
- **Queue Detection**: Fixed attribute handling (`text` vs `value`) for proper element content reading
- **Result Storage**: Fixed missing return statements that caused check results to be None
- **Graceful Exit**: Added bounds checking to prevent list index errors during break operations
- **Enhanced Detection**: JavaScript fallback strategies for robust queue detection

## Basic While Loop Structure

```json
{
  "type": "while_begin",
  "value": {
    "condition": "check_passed"
  },
  "description": "WHILE condition is true"
}
```

### Supported Conditions
- `check_passed`: Continue while last check_element succeeded
- `check_failed`: Continue while last check_element failed
- `value_equals`: Continue while variable equals specific value
- `value_not_equals`: Continue while variable doesn't equal specific value

## Complete Queue Management Example

```json
{
  "name": "Queue Management Automation",
  "url": "https://example.com/generate",
  "headless": false,
  "actions": [
    {
      "type": "set_variable",
      "value": {
        "variable": "max_tasks",
        "value": "8"
      },
      "description": "Set maximum queue capacity"
    },
    {
      "type": "set_variable",
      "value": {
        "variable": "task_count", 
        "value": "0"
      },
      "description": "Initialize task counter"
    },
    {
      "type": "click_button",
      "selector": "[data-test-id='sidebar-menuitem-button-Favorites']",
      "description": "Navigate to Favorites (queue view)"
    },
    {
      "type": "wait",
      "value": 2000,
      "description": "Wait for page load"
    },
    {
      "type": "check_element",
      "selector": ".queue-counter",
      "value": {
        "check": "less",
        "value": "${max_tasks}",
        "attribute": "text"
      },
      "description": "Check if queue has space"
    },
    {
      "type": "while_begin",
      "value": {
        "condition": "check_passed"
      },
      "description": "WHILE queue has space"
    },
    {
      "type": "if_begin",
      "value": {
        "condition": "check_failed"
      },
      "description": "IF queue is full"
    },
    {
      "type": "log_message",
      "value": {
        "message": "Queue is full (${max_tasks} tasks) - stopping automation",
        "log_file": "logs/queue_automation.log"
      },
      "description": "Log queue full message"
    },
    {
      "type": "break",
      "description": "Exit while loop"
    },
    {
      "type": "if_end",
      "value": {},
      "description": "END IF"
    },
    {
      "type": "log_message",
      "value": {
        "message": "Creating task #${task_count} - queue has space",
        "log_file": "logs/queue_automation.log"
      },
      "description": "Log task creation"
    },
    {
      "type": "click_button",
      "selector": ".creation-button",
      "description": "Open creation panel"
    },
    {
      "type": "upload_image",
      "selector": "input[type='file']",
      "value": "/path/to/image.jpg",
      "description": "Upload image"
    },
    {
      "type": "input_text",
      "selector": "#prompt-field",
      "value": "Create amazing automated content",
      "description": "Enter prompt"
    },
    {
      "type": "click_button",
      "selector": "#submit-button",
      "description": "Submit task"
    },
    {
      "type": "increment_variable",
      "value": {
        "variable": "task_count",
        "amount": 1
      },
      "description": "Increment task counter"
    },
    {
      "type": "wait",
      "value": 2000,
      "description": "Wait for task submission"
    },
    {
      "type": "click_button",
      "selector": "[data-test-id='sidebar-menuitem-button-Favorites']",
      "description": "Return to queue view"
    },
    {
      "type": "wait",
      "value": 2000,
      "description": "Wait for queue update"
    },
    {
      "type": "check_element",
      "selector": ".queue-counter",
      "value": {
        "check": "less",
        "value": "${max_tasks}",
        "attribute": "text"
      },
      "description": "Re-check queue status"
    },
    {
      "type": "while_end",
      "value": {},
      "description": "END WHILE loop"
    },
    {
      "type": "log_message",
      "value": {
        "message": "Automation completed. Total tasks created: ${task_count}",
        "log_file": "logs/queue_automation.log"
      },
      "description": "Log completion"
    }
  ]
}
```

## Element Detection Best Practices

### Attribute Selection
- **DIV elements**: Use `attribute: "text"` to read textContent
- **Input elements**: Use `attribute: "value"` to read input values
- **Data attributes**: Use `attribute: "data-*"` for custom attributes

### Queue Detection Strategies

The engine includes multiple fallback strategies for reliable queue detection:

```javascript
// 1. Direct selector match
const element = await page.locator(selector).first();

// 2. Text content search
const textElements = await page.locator(`text="${expectedText}"`).all();

// 3. Contains text search  
const containsElements = await page.locator(`text*="${expectedText}"`).all();

// 4. Attribute-based search
const attrElements = await page.locator(`[data-queue="${expectedText}"]`).all();

// 5. JavaScript evaluation fallback
const jsResult = await page.evaluate(() => {
    // Custom JavaScript detection logic
});
```

## Advanced Flow Control

### Nested Conditionals
```json
{
  "type": "while_begin",
  "value": { "condition": "check_passed" }
},
{
  "type": "if_begin", 
  "value": { "condition": "check_failed" }
},
{
  "type": "log_message",
  "value": { "message": "Inner condition failed" }
},
{
  "type": "break"
},
{
  "type": "if_end"
},
{
  "type": "while_end"
}
```

### Retry Logic with Limits
```json
{
  "type": "set_variable",
  "value": { "variable": "retry_count", "value": "0" }
},
{
  "type": "set_variable", 
  "value": { "variable": "max_retries", "value": "5" }
},
{
  "type": "while_begin",
  "value": { "condition": "check_passed" }
},
{
  "type": "increment_variable",
  "value": { "variable": "retry_count", "amount": 1 }
},
{
  "type": "check_element",
  "selector": "body",
  "value": {
    "check": "greater",
    "value": "${max_retries}",
    "attribute": "data-retry-count"
  }
},
{
  "type": "if_begin",
  "value": { "condition": "check_passed" }
},
{
  "type": "log_message",
  "value": { "message": "Max retries reached - exiting" }
},
{
  "type": "break"
},
{
  "type": "if_end"
},
{
  "type": "while_end"
}
```

## Variable Management

### Supported Variable Operations
- `set_variable`: Set initial values
- `increment_variable`: Increase numeric values
- `decrement_variable`: Decrease numeric values (if implemented)

### Variable Substitution
Use `${variable_name}` syntax in:
- Element values for comparison
- Log messages
- Text input values
- Any string-based configuration

### Example Variable Usage
```json
{
  "type": "set_variable",
  "value": {
    "variable": "base_url",
    "value": "https://api.example.com"
  }
},
{
  "type": "input_text",
  "selector": "#api-endpoint",
  "value": "${base_url}/v1/tasks"
},
{
  "type": "log_message", 
  "value": {
    "message": "Processing task #${task_number} at ${base_url}",
    "log_file": "logs/api_calls.log"
  }
}
```

## Debugging and Monitoring

### Comprehensive Logging
```json
{
  "type": "log_message",
  "value": {
    "message": "Queue check: current=${current_queue}, max=${max_queue}, result=${check_result}",
    "log_file": "logs/detailed_automation.log"
  }
}
```

### Debug Information
The engine logs detailed execution information:
- Action execution status
- Check result details (success, actual_value, expected_value)
- Variable states
- Block stack information
- Error details with context

### Example Debug Output
```
INFO:core.engine:EVAL_CONDITION: condition='check_passed', last_check_result={'success': True, 'actual_value': '3', 'expected_value': '8', 'check_type': 'less', 'attribute': 'text'}
INFO:core.engine:EVAL_CONDITION: check_passed = True
INFO:core.engine:Logged message to logs/queue_automation.log: Creating task #1 - queue has space
```

## Common Issues and Solutions

### Issue: Check Results Return None
**Problem**: `context.last_check_result` is None despite successful element detection
**Solution**: Fixed in recent update - execute_action now properly returns results

### Issue: "List Index Out of Range" on Break
**Problem**: Break statement tries to access actions beyond array bounds
**Solution**: Added bounds checking before accessing action array

### Issue: Wrong Attribute Reading
**Problem**: Using `attribute: "value"` on DIV elements returns empty string
**Solution**: Use `attribute: "text"` for DIV textContent, `attribute: "value"` for INPUT elements

### Issue: Queue Detection Timeout
**Problem**: Element not found after task submission
**Solution**: 
- Add wait time after task submission
- Use navigation to refresh queue view
- Implement JavaScript fallback detection

## Performance Considerations

### Optimization Tips
1. **Minimal Wait Times**: Use element-based waits instead of fixed delays
2. **Efficient Selectors**: Use specific, fast selectors
3. **Batch Operations**: Group related actions together
4. **Early Exit Conditions**: Implement proper break conditions to avoid infinite loops

### Resource Management
- **Memory Usage**: Variables are stored in context throughout execution
- **Browser Resources**: Long-running loops may impact browser performance
- **Log File Size**: Monitor log file growth in long-running automations

## Testing and Validation

### Test Your While Loop Automations
1. **Start Small**: Test loop logic with minimal actions first
2. **Add Logging**: Include comprehensive logging for all decision points
3. **Test Edge Cases**: Verify behavior when conditions are at boundaries
4. **Monitor Execution**: Watch browser during development to understand flow
5. **Validate Exit Conditions**: Ensure loops can exit gracefully

### Validation Checklist
- [ ] Loop condition is correctly formatted
- [ ] Break conditions are implemented
- [ ] Variables are properly initialized
- [ ] Element selectors are tested and reliable
- [ ] Attribute types match element types (text/value)
- [ ] Logging provides adequate debugging information
- [ ] Maximum iteration limits are considered

## Best Practices Summary

1. **Always provide exit conditions** to prevent infinite loops
2. **Use proper attributes** (`text` for DIVs, `value` for inputs)
3. **Add comprehensive logging** for debugging and monitoring
4. **Test element selectors** in browser DevTools before use
5. **Handle timing issues** with appropriate waits and retries
6. **Initialize variables** before use in conditions
7. **Use specific selectors** that won't change between runs
8. **Monitor resource usage** for long-running automations
9. **Implement graceful error handling** with IF blocks
10. **Document complex logic** with clear action descriptions

## Conclusion

While loop automation in Automaton provides powerful capabilities for creating sophisticated, adaptive workflows. With proper implementation of conditions, variables, and error handling, you can build robust automations that handle complex scenarios like queue management, retry logic, and multi-step processes.

The recent fixes ensure reliable operation with proper result storage, graceful exit handling, and enhanced element detection strategies. Follow the best practices and patterns outlined in this guide to create maintainable and reliable automated workflows.