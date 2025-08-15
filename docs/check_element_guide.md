# 🔍 Check Element Action Guide

## Overview

The `CHECK_ELEMENT` action allows you to verify element values, attributes, and numeric conditions during automation. This is useful for:

- ✅ Verifying queue counts are non-zero before processing
- ✅ Checking task counts are within limits (e.g., < 8)
- ✅ Validating element text or attribute values
- ✅ Monitoring dynamic content changes
- ✅ Conditional automation based on element states

## Action Configuration

### Basic Structure

```json
{
  "type": "check_element",
  "selector": "CSS_SELECTOR",
  "value": {
    "check": "CHECK_TYPE",
    "value": "EXPECTED_VALUE",
    "attribute": "ATTRIBUTE_NAME"
  },
  "timeout": 30000,
  "description": "Check description"
}
```

### Check Types

| Check Type | Description | Example |
|------------|-------------|---------|
| `equals` | Value must equal expected | Check if count = "5" |
| `not_equals` | Value must not equal expected | Check if status != "0" |
| `greater` | Numeric value > expected | Check if queue > 0 |
| `less` | Numeric value < expected | Check if tasks < 8 |
| `contains` | Value contains expected text | Check if message contains "Complete" |
| `not_zero` | Value is not "0" or empty | Check if queue is not empty |

### Attributes to Check

| Attribute | Description | Example |
|-----------|-------------|---------|
| `text` | Element's text content | "5 items" |
| `value` | Input field value | Form input values |
| `data-*` | Data attributes | `data-count`, `data-status` |
| `aria-*` | Accessibility attributes | `aria-label`, `aria-valuenow` |
| Any HTML attribute | Any valid attribute | `href`, `title`, `alt` |

## Examples

### 1. Check Queue Count is Not Zero

```python
.add_check_element(
    selector=".queue-count",
    check_type="not_zero",
    expected_value="",
    attribute="text",
    description="Verify queue has items"
)
```

### 2. Check Task Count is Less Than 8

```python
.add_check_element(
    selector="span.task-counter",
    check_type="less",
    expected_value="8",
    attribute="text",
    description="Ensure task count < 8"
)
```

### 3. Check Data Attribute Value

```python
.add_check_element(
    selector="button.process",
    check_type="not_equals",
    expected_value="0",
    attribute="data-remaining",
    description="Check remaining items"
)
```

### 4. Check Element Contains Text

```python
.add_check_element(
    selector=".status-message",
    check_type="contains",
    expected_value="Success",
    attribute="text",
    description="Verify success message"
)
```

### 5. Check Aria Attribute for Progress

```python
.add_check_element(
    selector="div.progress-bar",
    check_type="equals",
    expected_value="100",
    attribute="aria-valuenow",
    description="Check if progress is 100%"
)
```

## GUI Usage

1. **Open Add Action Dialog**
   - Click "Add Action" in the automation GUI

2. **Select CHECK_ELEMENT**
   - Choose "check_element" from the Action Type dropdown

3. **Configure Check**
   - **Selector**: CSS selector for the element
   - **Check Type**: Select comparison type (equals, not_equals, etc.)
   - **Expected Value**: The value to compare against
   - **Attribute**: What to check (text, value, or attribute name)

4. **Add Description**
   - Provide a clear description of what you're checking

## JSON Configuration Example

```json
{
  "name": "Process Automation with Checks",
  "url": "https://yoursite.com",
  "actions": [
    {
      "type": "wait_for_element",
      "selector": ".queue-display",
      "timeout": 10000,
      "description": "Wait for queue display"
    },
    {
      "type": "check_element",
      "selector": ".queue-count",
      "value": {
        "check": "not_zero",
        "value": "",
        "attribute": "text"
      },
      "timeout": 5000,
      "description": "Verify queue is not empty"
    },
    {
      "type": "check_element",
      "selector": ".task-limit",
      "value": {
        "check": "less",
        "value": "8",
        "attribute": "text"
      },
      "timeout": 5000,
      "description": "Check task count < 8"
    },
    {
      "type": "click_button",
      "selector": "button.process",
      "description": "Start processing"
    }
  ]
}
```

## Return Values

The CHECK_ELEMENT action returns a dictionary with:

```python
{
    "success": True/False,  # Whether check passed
    "actual_value": "5",    # The actual value found
    "expected_value": "8",  # The expected value
    "check_type": "less",   # The check performed
    "attribute": "text"     # The attribute checked
}
```

## Testing Script

Use the provided test script to experiment with checks:

```bash
python3 examples/test_check_element.py
```

Options:
1. Test on example.com
2. Monitor dynamic values
3. Custom URL with specific checks

## Common Use Cases

### 1. Queue Management
```python
# Only process if queue has items
.add_check_element(selector=".queue", check_type="not_zero", 
                   expected_value="", attribute="text")
```

### 2. Rate Limiting
```python
# Ensure not exceeding limits
.add_check_element(selector=".active-tasks", check_type="less",
                   expected_value="10", attribute="text")
```

### 3. Status Verification
```python
# Check if ready to proceed
.add_check_element(selector=".status", check_type="equals",
                   expected_value="ready", attribute="data-state")
```

### 4. Progress Monitoring
```python
# Wait for completion
.add_check_element(selector=".progress", check_type="equals",
                   expected_value="100", attribute="aria-valuenow")
```

## Tips

1. **Use Selector Finder**: Use the selector finder tool to locate elements with numeric values
2. **Check Attributes**: Inspect elements to find data-* attributes that contain counts
3. **Combine with Waits**: Add wait actions before checks to ensure elements are updated
4. **Log Results**: Check results are stored in automation outputs for debugging
5. **Chain Checks**: Use multiple checks to validate complex conditions

## Troubleshooting

### Check Always Fails
- Verify the selector is correct
- Check if the attribute name is spelled correctly
- Ensure the element is loaded before checking
- Inspect actual vs expected values in logs

### Numeric Comparisons Not Working
- Ensure values are numeric (no text like "items: 5")
- Remove spaces and non-numeric characters
- Use "text" attribute for visible content
- Use "value" for input fields

### Attribute Not Found
- Use browser inspector to verify attribute exists
- Check for typos in attribute name
- Some attributes may be dynamically added
- Try "text" or "innerText" for content