# 🔄 Programming-Like Blocks Guide

## Overview

Programming-like blocks enable sophisticated control flow in web automation, making it possible to create truly adaptable and intelligent automation sequences. These blocks work just like programming constructs in languages like Python, JavaScript, or C++.

## Available Block Types

### 🔹 IF Blocks
Execute actions conditionally based on the result of CHECK_ELEMENT actions.

```python
.add_if_begin("check_passed")      # IF condition is true
    # Actions to execute if true
.add_elif("check_failed")          # ELIF alternative condition  
    # Actions for alternative condition
.add_else()                        # ELSE catch-all
    # Actions if no conditions met
.add_if_end()                      # END IF block
```

### 🔄 WHILE Loops
Repeat actions while a condition remains true.

```python
.add_while_begin("check_passed")   # WHILE condition is true
    # Actions to repeat
    .add_break()                   # Exit loop early if needed
    .add_continue()                # Skip to next iteration
.add_while_end()                   # END WHILE block
```

### 🎯 Loop Control
Control loop execution flow.

```python
.add_break()                       # Exit current loop
.add_continue()                    # Skip to next iteration
```

## Condition Types

All block conditions work with the results of the most recent `CHECK_ELEMENT` action:

| Condition | When Block Executes |
|-----------|-------------------|
| `check_passed` | When the last CHECK_ELEMENT returned true |
| `check_failed` | When the last CHECK_ELEMENT returned false |
| `value_equals` | When the actual value equals expected value |
| `value_not_equals` | When the actual value doesn't equal expected |

## Complete Examples

### 1. Smart Queue Management

```python
# Process queue intelligently based on current load
automation = (builder
    .add_while_begin("check_passed", "WHILE queue has items")
    
        # Check current queue count
        .add_check_element(".queue-count", "not_zero", "", "text", "Check queue")
        
        .add_if_begin("check_failed", "IF queue is empty")
            .add_break("Exit - no items to process")
        .add_if_end()
        
        # Decide processing strategy based on load
        .add_check_element(".queue-count", "greater", "7", "text", "Check if overloaded")
        
        .add_if_begin("check_passed", "IF queue is overloaded (>7)")
            .add_wait(5000, "Wait for queue to reduce")
            .add_continue("Skip processing this cycle")
            
        .add_elif("value_equals", "ELIF queue is moderate (6-7)")
            .add_click_button("button.process-one", "Process 1 item")
            
        .add_else("ELSE queue has capacity (<6)")
            .add_click_button("button.process-batch", "Process multiple items")
            
        .add_if_end()
        
        # Safety check to prevent infinite loops
        .add_check_element(".processed-count", "greater", "50", "text")
        .add_if_begin("check_passed", "IF daily limit reached")
            .add_break("Exit - daily limit reached")
        .add_if_end()
        
    .add_while_end("END queue processing")
    
    .build()
)
```

### 2. Robust Error Handling

```python
# Try multiple methods with graceful fallbacks
automation = (builder
    .add_check_element("button.primary-action", "not_zero", "", "length")
    
    .add_if_begin("check_passed", "IF primary method available")
        .add_click_button("button.primary-action", "Try primary method")
        .add_wait(2000, "Wait for response")
        
        .add_check_element(".success-indicator", "not_zero", "", "length")
        
        .add_if_begin("check_failed", "IF primary method failed")
            
            # Try backup method 1
            .add_check_element("button.backup1", "not_zero", "", "length")
            .add_if_begin("check_passed", "IF backup method 1 available")
                .add_click_button("button.backup1", "Try backup method 1")
                .add_wait(2000, "Wait for backup1")
                
                .add_check_element(".success-indicator", "not_zero", "", "length")
                .add_if_begin("check_failed", "IF backup1 also failed")
                    
                    # Try backup method 2
                    .add_click_button("button.backup2", "Try backup method 2")
                    
                .add_if_end()
            .add_if_end()
            
        .add_if_end()
        
    .add_else("ELSE no methods available")
        .add_click_button("button.report-error", "Report no methods available")
        
    .add_if_end()
    
    .build()
)
```

### 3. Adaptive Form Processing

```python
# Process forms dynamically based on field types
automation = (builder
    .add_while_begin("check_passed", "WHILE there are unprocessed fields")
    
        .add_check_element("input:not(.processed), select:not(.processed)", 
                          "not_zero", "", "length", "Check for unprocessed fields")
        
        .add_if_begin("check_failed", "IF all fields processed")
            .add_break("All fields complete")
        .add_if_end()
        
        # Check field type and handle accordingly
        .add_check_element("input:not(.processed):first", "equals", "text", "type")
        
        .add_if_begin("check_passed", "IF field is text input")
            .add_input_text("input:not(.processed):first", "Sample text")
            
        .add_elif("value_equals", "ELIF field is email input")  
            .add_input_text("input:not(.processed):first", "test@example.com")
            
        .add_elif("value_equals", "ELIF field is number input")
            .add_input_text("input:not(.processed):first", "123")
            
        .add_else("ELSE field is other type")
            # Handle selects, checkboxes, etc.
            .add_check_element("select:not(.processed):first", "not_zero", "", "length")
            .add_if_begin("check_passed", "IF it's a select field")
                .add_click_button("select:not(.processed):first option:nth-child(2)")
            .add_if_end()
            
        .add_if_end()
        
        # Mark field as processed (would use JS injection in practice)
        .add_wait(100, "Mark field as processed")
        
    .add_while_end()
    
    .build()
)
```

## Block Nesting Rules

### ✅ Valid Nesting
- IF blocks can be nested inside other IF blocks
- WHILE loops can contain IF blocks
- IF blocks can contain WHILE loops
- Any depth of nesting is supported

### ❌ Invalid Patterns
- Missing END statements (IF_BEGIN without IF_END)
- Mismatched blocks (WHILE_BEGIN with IF_END)
- BREAK/CONTINUE outside of loops
- ELIF/ELSE outside of IF blocks

## Execution Context

The system maintains an execution context that tracks:
- **Instruction Pointer**: Current action being executed
- **Block Stack**: Active nested blocks
- **Last Check Result**: Result from most recent CHECK_ELEMENT
- **Loop State**: Break/continue flags for loop control

### Context Example
```
Action 0: add_check_element(...)           ← Sets last_check_result
Action 1: add_if_begin("check_passed")     ← Pushes IF block to stack
Action 2: add_click_button(...)            ← Executes if condition true
Action 3: add_else()                       ← Alternative branch
Action 4: add_wait(...)                    ← Executes if condition false  
Action 5: add_if_end()                     ← Pops IF block from stack
```

## Advanced Patterns

### Pattern 1: Retry with Exponential Backoff

```python
# Retry with increasing delays
retry_count = 0
automation = (builder
    .add_while_begin("check_passed", "Retry loop")
    
        .add_check_element(".retry-count", "less", "5", "text", "Check retry limit")
        .add_if_begin("check_failed", "IF max retries reached")
            .add_break("Max retries exceeded")
        .add_if_end()
        
        # Try the action
        .add_click_button("button.unreliable-action", "Try action")
        .add_wait(1000, "Wait for response")
        
        .add_check_element(".success", "not_zero", "", "length", "Check success")
        .add_if_begin("check_passed", "IF action succeeded")
            .add_break("Success - exit retry loop")
        .add_if_end()
        
        # Exponential backoff wait
        .add_check_element(".retry-count", "equals", "1", "text")
        .add_if_begin("check_passed", "IF first retry")
            .add_wait(2000, "Wait 2 seconds")
        .add_elif("value_equals", "ELIF second retry")
            .add_wait(4000, "Wait 4 seconds")  
        .add_else("ELSE later retries")
            .add_wait(8000, "Wait 8 seconds")
        .add_if_end()
        
        # Increment retry count (would use JS in practice)
        .add_wait(100, "Increment retry counter")
        
    .add_while_end()
    
    .build()
)
```

### Pattern 2: State Machine Implementation

```python
# Implement a simple state machine
automation = (builder
    .add_while_begin("check_passed", "State machine loop")
    
        # Check current state
        .add_check_element(".state", "equals", "INIT", "data-state")
        
        .add_if_begin("check_passed", "IF state is INIT")
            .add_click_button("button.start", "Initialize system")
            # State would change to PROCESSING
            
        .add_elif("value_equals", "ELIF state is PROCESSING")
            .add_check_element(".progress", "equals", "100", "aria-valuenow")
            .add_if_begin("check_passed", "IF processing complete")
                .add_click_button("button.finalize", "Finalize")
                # State changes to COMPLETE
            .add_else("ELSE still processing")
                .add_wait(5000, "Wait for processing")
            .add_if_end()
            
        .add_elif("value_equals", "ELIF state is COMPLETE")
            .add_break("State machine complete")
            
        .add_else("ELSE unknown state")
            .add_break("Error - unknown state")
            
        .add_if_end()
        
        # Safety check
        .add_check_element(".loop-count", "greater", "20", "text")
        .add_if_begin("check_passed", "IF too many iterations")
            .add_break("Safety exit")
        .add_if_end()
        
    .add_while_end()
    
    .build()
)
```

## JSON Configuration

```json
{
  "name": "Programming Blocks Example",
  "url": "https://example.com",
  "actions": [
    {
      "type": "check_element",
      "selector": ".queue-count",
      "value": {"check": "not_zero", "value": "", "attribute": "text"},
      "description": "Check queue has items"
    },
    {
      "type": "if_begin", 
      "value": {"condition": "check_passed"},
      "description": "IF queue has items"
    },
    {
      "type": "while_begin",
      "value": {"condition": "check_passed"}, 
      "description": "WHILE processing items"
    },
    {
      "type": "click_button",
      "selector": "button.process",
      "description": "Process item"
    },
    {
      "type": "check_element",
      "selector": ".queue-count",
      "value": {"check": "equals", "value": "0", "attribute": "text"},
      "description": "Check if queue empty"
    },
    {
      "type": "if_begin",
      "value": {"condition": "check_passed"},
      "description": "IF queue is now empty"
    },
    {
      "type": "break",
      "value": {},
      "description": "Exit processing loop"
    },
    {
      "type": "if_end",
      "value": {},
      "description": "END empty queue check"
    },
    {
      "type": "while_end",
      "value": {},
      "description": "END processing loop"  
    },
    {
      "type": "if_end",
      "value": {},
      "description": "END main condition"
    }
  ]
}
```

## Tips and Best Practices

### 🎯 Design Tips
1. **Plan Your Logic**: Draw flowcharts before coding complex blocks
2. **Keep Blocks Simple**: Avoid too many nested levels (max 3-4 deep)
3. **Use Descriptive Names**: Make block purposes clear in descriptions
4. **Add Safety Exits**: Always include loop counters or timeouts

### 🔧 Implementation Tips
1. **Check First**: Always CHECK_ELEMENT before conditional blocks
2. **Handle Edge Cases**: Account for elements not found, timeouts, etc.
3. **Test Incrementally**: Test simple blocks before adding complexity
4. **Use Break Points**: Add waits and checks for debugging

### 🛡️ Error Prevention
1. **Balance Blocks**: Every BEGIN needs an END
2. **Scope Awareness**: BREAK/CONTINUE only work inside loops
3. **Condition Dependencies**: Ensure CHECK_ELEMENT runs before IF blocks
4. **Infinite Loop Prevention**: Add maximum iteration counters

## Troubleshooting

### Block Mismatch Errors
```
Error: IF_BEGIN without matching IF_END
Solution: Check that every add_if_begin() has add_if_end()
```

### Condition Not Found
```
Error: No previous check result for IF block
Solution: Add add_check_element() before conditional blocks
```

### Infinite Loops  
```
Error: WHILE loop running indefinitely
Solution: Add break conditions and safety counters
```

### Invalid BREAK/CONTINUE
```
Error: BREAK outside of loop
Solution: Only use BREAK/CONTINUE inside WHILE blocks
```

## Performance Considerations

- **Block Overhead**: Each block adds ~10ms processing time
- **Memory Usage**: Deep nesting uses more memory for context stack  
- **Loop Efficiency**: Add reasonable delays in WHILE loops
- **Condition Caching**: CHECK_ELEMENT results are cached for performance

---

This system transforms web automation from simple linear sequences into powerful, adaptive programs that can handle complex real-world scenarios with intelligence and resilience!