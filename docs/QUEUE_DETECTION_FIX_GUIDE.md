# Queue Detection Fix Guide

## 🔴 Problem Identified

The test encountered errors because of incorrect action type usage and value format:

```
ERROR: 'in <string>' requires string as left operand, not dict
```

---

## 🎯 Root Cause Analysis

### Issue 1: Wrong Action Type
**Problem:** The workflow used `check_queue` with a dictionary value containing conditional logic.

```json
// ❌ INCORRECT
{
  "type": "check_queue",
  "selector": ".sc-fGqoZs.fWNdKz",
  "value": {
    "check": "less",
    "value": "8",
    "attribute": "text"
  }
}
```

**Why it failed:** The `CHECK_QUEUE` action type expects a simple string value to search for in queue items, not a conditional check dictionary.

### Issue 2: Action Type Confusion

There are two different action types that were confused:

1. **`CHECK_QUEUE`** - For checking if specific text exists in queue items
   - Expects: Simple string value
   - Returns: List of matching queue items
   
2. **`CHECK_ELEMENT`** - For conditional checking of element attributes
   - Expects: Dictionary with check conditions
   - Returns: Pass/fail for conditional logic

---

## ✅ Solution

### Use `check_element` for Conditional Queue Checks

```json
// ✅ CORRECT
{
  "type": "check_element",
  "selector": ".sc-fGqoZs.fWNdKz",
  "value": {
    "check": "less",
    "value": "8",
    "attribute": "text"
  },
  "timeout": 5000,
  "description": "Check if queue number is less than 8"
}
```

---

## 📋 Complete Working Examples

### Example 1: Check if Queue Has Space
```json
{
  "type": "check_element",
  "selector": ".sc-fGqoZs.fWNdKz",
  "value": {
    "check": "less",
    "value": "8",
    "attribute": "text"
  },
  "timeout": 5000,
  "description": "Check if queue has space (< 8)"
}
```

### Example 2: Check if Queue is Full
```json
{
  "type": "check_element",
  "selector": ".sc-fGqoZs.fWNdKz",
  "value": {
    "check": "equals",
    "value": "8",
    "attribute": "text"
  },
  "timeout": 5000,
  "description": "Check if queue is full (= 8)"
}
```

### Example 3: Alternative Using Text Matching
```json
{
  "type": "check_element",
  "selector": "div:has-text('^[0-7]$')",
  "value": {
    "check": "exists",
    "value": null,
    "attribute": null
  },
  "timeout": 5000,
  "description": "Check if queue number is 0-7"
}
```

---

## 🔧 Workflow Structure Fix

### Before (Incorrect)
```json
{
  "actions": [
    // ...
    {
      "type": "check_queue",  // ❌ Wrong action type
      "selector": ".sc-fGqoZs.fWNdKz",
      "value": {
        "check": "less",
        "value": "8",
        "attribute": "text"
      }
    },
    {
      "type": "if_begin",
      "value": {
        "condition": "check_failed"
      }
    }
    // ...
  ]
}
```

### After (Correct)
```json
{
  "actions": [
    // ...
    {
      "type": "check_element",  // ✅ Correct action type
      "selector": ".sc-fGqoZs.fWNdKz",
      "value": {
        "check": "less",
        "value": "8",
        "attribute": "text"
      }
    },
    {
      "type": "if_begin",
      "value": {
        "condition": "check_failed"
      }
    }
    // ...
  ]
}
```

---

## 📊 Action Type Reference

| Action Type | Purpose | Value Format | Use Case |
|------------|---------|--------------|----------|
| `check_element` | Conditional checking | Dictionary with `check`, `value`, `attribute` | Queue space detection |
| `check_queue` | Find text in queue items | Simple string | Finding specific tasks |
| `wait_for_element` | Wait for element presence | null or timeout | Page load confirmation |
| `click_button` | Click an element | null | Navigation and submission |

---

## 🎯 Testing the Fix

### Test Command
```bash
# Test the fixed workflow
python3.11 automaton-cli.py run -c workflows/run-08-18-1-fixed.json --show-browser

# Or use GUI
python3.11 automaton-gui.py
# Load: workflows/run-08-18-1-fixed.json
```

### Expected Behavior
1. ✅ Successfully navigate to Generate page using text landmark
2. ✅ Correctly detect queue number (0-8)
3. ✅ Properly evaluate if queue has space (< 8)
4. ✅ Execute conditional logic based on queue status
5. ✅ No type errors or action execution failures

---

## 🔍 Debugging Tips

### If Queue Detection Still Fails

1. **Verify Selector is Correct**
   ```javascript
   // In browser console:
   document.querySelector('.sc-fGqoZs.fWNdKz').textContent
   ```

2. **Try Alternative Selectors**
   ```json
   // Option 1: Parent + child approach
   "selector": ".sc-fstJre.eFrNiR .sc-fGqoZs.fWNdKz"
   
   // Option 2: XPath
   "selector": "xpath=//div[contains(@class, 'fWNdKz')]"
   
   // Option 3: Text pattern
   "selector": "div:has-text('^[0-8]$')"
   ```

3. **Add Debug Logging**
   ```json
   {
     "type": "log_message",
     "value": {
       "message": "Checking queue selector: .sc-fGqoZs.fWNdKz",
       "log_file": "logs/debug.log"
     }
   }
   ```

---

## 📋 Summary

**Key Fixes Applied:**
1. Changed `check_queue` to `check_element` for conditional checks
2. Ensured value format matches action type requirements
3. Added proper navigation using Generate text landmark
4. Improved error handling and logging

**Files Created:**
- `workflows/run-08-18-1-fixed.json` - Corrected workflow with proper action types
- `docs/QUEUE_DETECTION_FIX_GUIDE.md` - This comprehensive guide

The workflow should now execute without type errors and properly detect queue status for conditional automation flow.

---

*Updated: August 25, 2025*  
*Compatible with: Automaton Framework v2.0+*