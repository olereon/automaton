# Minimal Fix Instructions for Queue Detection

## The ONLY Change Needed

In your workflow `run-08-18-1-updated.json`, you only need to change TWO things:

### 1. Change Action Type from `check_queue` to `check_element`

**Find all occurrences of:**
```json
{
  "type": "check_queue",
  "selector": ".sc-fGqoZs.fWNdKz",
  "value": {
    "check": "less",
    "value": "8",
    "attribute": "text"
  },
  "timeout": 1000,
  "description": "Check current queue number using new div selector"
}
```

**Replace with:**
```json
{
  "type": "check_element",  // ← THIS IS THE ONLY CHANGE
  "selector": ".sc-fGqoZs.fWNdKz",
  "value": {
    "check": "less",
    "value": "8",
    "attribute": "text"
  },
  "timeout": 1000,
  "description": "Check current queue number using new div selector"
}
```

### 2. Location of Changes

Based on your workflow, you need to change `check_queue` to `check_element` at:
- **Line 357** (action index 43)
- **Line 414** (if you have another queue check)

## Why This Fixes the Error

The error `'in <string>' requires string as left operand, not dict` occurs because:

- `check_queue` expects a simple string value (e.g., `"value": "Completed"`)
- `check_element` expects a dictionary with conditional logic (what you have)

## DO NOT Change

- ❌ DO NOT change the order of actions
- ❌ DO NOT move the Generate landmark actions
- ❌ DO NOT reorganize the workflow structure
- ❌ DO NOT remove or add actions

Just change the action type from `check_queue` to `check_element` wherever it appears with a dictionary value.

## Testing

After making this single change:
```bash
python3.11 automaton-cli.py run -c workflows/run-08-18-1-updated.json --show-browser
```

The workflow should run without the TypeError.