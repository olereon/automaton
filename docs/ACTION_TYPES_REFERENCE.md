# Action Types Reference Guide

Complete reference for all supported action types in the Automaton framework.

## Table of Contents

1. [Basic Actions](#basic-actions)
2. [Advanced Actions](#advanced-actions)
3. [Flow Control](#flow-control)
4. [Generation Downloads](#generation-downloads)
5. [Variable Management](#variable-management)
6. [Logging & Debugging](#logging--debugging)

---

## Basic Actions

### INPUT_TEXT
Fill text input fields with specified content.

**Parameters:**
- `selector` (string): CSS selector for the input field
- `value` (string): Text to enter (supports variables)
- `timeout` (int, optional): Wait timeout in milliseconds

**Example:**
```json
{
  "type": "input_text",
  "selector": "#username",
  "value": "john.doe@example.com",
  "timeout": 5000,
  "description": "Enter username"
}
```

### CLICK_BUTTON
Click any clickable element (button, link, div, etc.).

**Parameters:**
- `selector` (string): CSS selector for the element
- `timeout` (int, optional): Wait timeout before clicking

**Example:**
```json
{
  "type": "click_button",
  "selector": "#submit-btn",
  "timeout": 3000,
  "description": "Click submit button"
}
```

### UPLOAD_IMAGE
Upload a file to a file input element.

**Parameters:**
- `selector` (string): CSS selector for file input
- `file_path` (string): Path to the file to upload

**Example:**
```json
{
  "type": "upload_image",
  "selector": "#file-upload",
  "value": "/path/to/image.jpg",
  "description": "Upload profile picture"
}
```

### TOGGLE_SETTING
Check or uncheck checkboxes, radio buttons, or toggle switches.

**Parameters:**
- `selector` (string): CSS selector for the element
- `value` (boolean): true to check, false to uncheck

**Example:**
```json
{
  "type": "toggle_setting",
  "selector": "#accept-terms",
  "value": true,
  "description": "Accept terms and conditions"
}
```

### WAIT
Pause execution for a specified duration.

**Parameters:**
- `value` (int): Duration in milliseconds

**Example:**
```json
{
  "type": "wait",
  "value": 2000,
  "description": "Wait 2 seconds"
}
```

### WAIT_FOR_ELEMENT
Wait for an element to appear on the page.

**Parameters:**
- `selector` (string): CSS selector for the element
- `timeout` (int, optional): Maximum wait time in milliseconds

**Example:**
```json
{
  "type": "wait_for_element",
  "selector": ".success-message",
  "timeout": 10000,
  "description": "Wait for success message"
}
```

### REFRESH_PAGE
Reload the current page.

**Parameters:** None

**Example:**
```json
{
  "type": "refresh_page",
  "description": "Refresh the page"
}
```

### EXPAND_DIALOG
Expand a collapsible dialog or accordion element.

**Parameters:**
- `selector` (string): CSS selector for the expandable element

**Example:**
```json
{
  "type": "expand_dialog",
  "selector": ".accordion-header",
  "description": "Expand settings panel"
}
```

### SWITCH_PANEL
Switch between tabs or panels in a multi-panel interface.

**Parameters:**
- `selector` (string): CSS selector for the panel/tab to switch to

**Example:**
```json
{
  "type": "switch_panel",
  "selector": "#tab-settings",
  "description": "Switch to settings tab"
}
```

---

## Advanced Actions

### CHECK_ELEMENT
Validate element content against expected values.

**Parameters:**
- `selector` (string): CSS selector for the element
- `check_type` (string): "equals", "less", "greater", "contains", "not_contains"
- `expected_value` (string): Value to check against (supports variables)
- `attribute` (string, optional): Attribute to check (default: "text")

**Example:**
```json
{
  "type": "check_element",
  "selector": ".queue-count",
  "check_type": "less",
  "expected_value": "8",
  "attribute": "text",
  "description": "Check if queue has space"
}
```

**Check Types:**
- `equals`: Exact match
- `less`: Numeric less than
- `greater`: Numeric greater than
- `contains`: Text contains substring
- `not_contains`: Text does not contain substring

### CHECK_QUEUE
Specialized queue monitoring with multiple detection strategies.

**Parameters:**
- `selector` (string): CSS selector for queue element
- `check_type` (string): Comparison type
- `expected_value` (string/int): Expected queue value
- `attribute` (string, optional): Attribute to check

**Example:**
```json
{
  "type": "check_queue",
  "selector": ".queue-status",
  "check_type": "less",
  "expected_value": "8",
  "description": "Check queue capacity"
}
```

### LOGIN
Automated login action with credential management.

**Parameters:**
- `username` (string): Username or email
- `password` (string): Password
- `username_selector` (string): Selector for username field
- `password_selector` (string): Selector for password field
- `submit_selector` (string): Selector for submit button

**Example:**
```json
{
  "type": "login",
  "value": {
    "username": "user@example.com",
    "password": "secure_password",
    "username_selector": "#email",
    "password_selector": "#password",
    "submit_selector": "#login-btn"
  },
  "description": "Login to platform"
}
```

### DOWNLOAD_FILE
Download a file from a link or button.

**Parameters:**
- `selector` (string): CSS selector for download link/button
- `wait_for_download` (boolean, optional): Wait for download completion

**Example:**
```json
{
  "type": "download_file",
  "selector": ".download-link",
  "description": "Download report"
}
```

### CONDITIONAL_WAIT
Retry an action with exponential backoff until successful.

**Parameters:**
- `action` (object): Action to retry
- `max_attempts` (int): Maximum retry attempts
- `initial_wait` (int): Initial wait time in milliseconds
- `max_wait` (int): Maximum wait time between retries
- `multiplier` (float): Backoff multiplier

**Example:**
```json
{
  "type": "conditional_wait",
  "value": {
    "action": {
      "type": "click_button",
      "selector": "#dynamic-button"
    },
    "max_attempts": 5,
    "initial_wait": 1000,
    "max_wait": 10000,
    "multiplier": 2.0
  },
  "description": "Retry clicking button with backoff"
}
```

### SKIP_IF
Skip the next action based on a condition.

**Parameters:**
- `condition` (string): JavaScript expression to evaluate
- `skip_count` (int, optional): Number of actions to skip (default: 1)

**Example:**
```json
{
  "type": "skip_if",
  "value": {
    "condition": "check_result == false",
    "skip_count": 2
  },
  "description": "Skip next 2 actions if check failed"
}
```

---

## Flow Control

### IF_BEGIN / IF_END
Conditional execution block.

**Parameters:**
- `condition` (string): JavaScript expression to evaluate

**Example:**
```json
[
  {
    "type": "if_begin",
    "value": {
      "condition": "check_result == true"
    },
    "description": "If queue has space"
  },
  {
    "type": "click_button",
    "selector": "#create-task",
    "description": "Create new task"
  },
  {
    "type": "if_end",
    "description": "End if block"
  }
]
```

### ELIF
Else-if branch in conditional block.

**Parameters:**
- `condition` (string): JavaScript expression to evaluate

**Example:**
```json
{
  "type": "elif",
  "value": {
    "condition": "queue_count == 5"
  },
  "description": "Else if queue is half full"
}
```

### ELSE
Else branch in conditional block.

**Parameters:** None

**Example:**
```json
{
  "type": "else",
  "description": "Otherwise"
}
```

### WHILE_BEGIN / WHILE_END
Loop execution block.

**Parameters:**
- `condition` (string): JavaScript expression to evaluate

**Example:**
```json
[
  {
    "type": "while_begin",
    "value": {
      "condition": "task_count < max_tasks"
    },
    "description": "While tasks remain"
  },
  {
    "type": "click_button",
    "selector": "#process-task",
    "description": "Process task"
  },
  {
    "type": "increment_variable",
    "value": {
      "name": "task_count",
      "increment": 1
    }
  },
  {
    "type": "while_end",
    "description": "End while loop"
  }
]
```

### BREAK
Exit the current loop immediately.

**Parameters:** None

**Example:**
```json
{
  "type": "break",
  "description": "Exit loop"
}
```

### CONTINUE
Skip to the next iteration of the current loop.

**Parameters:** None

**Example:**
```json
{
  "type": "continue",
  "description": "Skip to next iteration"
}
```

### STOP_AUTOMATION
Terminate the entire automation immediately.

**Parameters:**
- `reason` (string, optional): Reason for stopping
- `log_file` (string, optional): Path to log file for recording stop

**Example:**
```json
{
  "type": "stop_automation",
  "value": {
    "reason": "Critical error encountered",
    "log_file": "/logs/automation.log"
  },
  "description": "Emergency stop"
}
```

---

## Generation Downloads

### START_GENERATION_DOWNLOADS
Begin automated download process for generated content.

**Parameters:**
- `max_downloads` (int): Maximum files to download
- `downloads_folder` (string): Target download directory
- `logs_folder` (string, optional): Directory for log files
- `download_timeout` (int, optional): Timeout per download
- `verification_timeout` (int, optional): File verification timeout
- `retry_attempts` (int, optional): Retry attempts for failed downloads
- Various selectors for platform-specific elements

**Example:**
```json
{
  "type": "start_generation_downloads",
  "value": {
    "max_downloads": 50,
    "downloads_folder": "/downloads/vids",
    "logs_folder": "/logs",
    "download_timeout": 120000,
    "verification_timeout": 30000,
    "retry_attempts": 3,
    "completed_task_selector": "div[id$='__8']",
    "thumbnail_selector": ".thumbnail-item",
    "download_button_selector": "[data-download]",
    "generation_date_selector": ".date-field",
    "prompt_selector": ".prompt-text"
  },
  "timeout": 300000,
  "description": "Start downloading generations"
}
```

### STOP_GENERATION_DOWNLOADS
Stop the currently running generation download process.

**Parameters:** None

**Example:**
```json
{
  "type": "stop_generation_downloads",
  "description": "Stop downloads"
}
```

### CHECK_GENERATION_STATUS
Get the current status of generation downloads.

**Parameters:** None

**Returns:**
- `downloads_completed`: Number of completed downloads
- `current_thumbnail_index`: Current position in thumbnail list
- `should_stop`: Whether stop was requested
- `max_downloads`: Configured maximum
- `log_file_path`: Path to log file
- `downloads_folder`: Download directory

**Example:**
```json
{
  "type": "check_generation_status",
  "description": "Check download progress"
}
```

---

## Variable Management

### SET_VARIABLE
Store a value in a variable for later use.

**Parameters:**
- `name` (string): Variable name
- `value` (any): Value to store (can be string, number, boolean)

**Example:**
```json
{
  "type": "set_variable",
  "value": {
    "name": "user_id",
    "value": "12345"
  },
  "description": "Store user ID"
}
```

### INCREMENT_VARIABLE
Increment a numeric variable.

**Parameters:**
- `name` (string): Variable name
- `increment` (int, optional): Amount to increment (default: 1)

**Example:**
```json
{
  "type": "increment_variable",
  "value": {
    "name": "counter",
    "increment": 1
  },
  "description": "Increment counter"
}
```

### Variable Substitution
Use `${variable_name}` syntax to reference variables in any string value.

**Example:**
```json
{
  "type": "input_text",
  "selector": "#message",
  "value": "Hello, ${username}! Your ID is ${user_id}",
  "description": "Enter personalized message"
}
```

---

## Logging & Debugging

### LOG_MESSAGE
Record a message to the automation log.

**Parameters:**
- `message` (string): Message to log (supports variables)
- `level` (string, optional): Log level ("info", "warning", "error")
- `file` (string, optional): Log file path

**Example:**
```json
{
  "type": "log_message",
  "value": {
    "message": "Processing task ${task_id} for user ${username}",
    "level": "info",
    "file": "/logs/automation.log"
  },
  "description": "Log task processing"
}
```

---

## Best Practices

### 1. Selector Strategies
- Use unique IDs when available: `#unique-id`
- Use data attributes: `[data-test-id="submit"]`
- Combine classes for specificity: `.form-container .submit-button`
- Avoid overly generic selectors: `button`, `div`

### 2. Timeout Management
- Set appropriate timeouts for network operations
- Use shorter timeouts for local operations
- Implement retry logic for flaky elements

### 3. Error Handling
- Use CHECK_ELEMENT before critical actions
- Implement IF/ELSE blocks for error recovery
- Use CONDITIONAL_WAIT for dynamic content
- Add LOG_MESSAGE for debugging

### 4. Variable Usage
- Initialize variables at the start
- Use descriptive variable names
- Clean up variables when done
- Document variable purposes

### 5. Flow Control
- Keep loops simple and bounded
- Always include exit conditions
- Use BREAK for early termination
- Test edge cases thoroughly

---

## Examples

### Complete Form Submission
```json
{
  "actions": [
    {"type": "wait_for_element", "selector": "#form", "timeout": 5000},
    {"type": "input_text", "selector": "#name", "value": "John Doe"},
    {"type": "input_text", "selector": "#email", "value": "john@example.com"},
    {"type": "toggle_setting", "selector": "#newsletter", "value": true},
    {"type": "click_button", "selector": "#submit"},
    {"type": "wait_for_element", "selector": ".success", "timeout": 10000},
    {"type": "log_message", "value": {"message": "Form submitted successfully"}}
  ]
}
```

### Queue Processing Loop
```json
{
  "actions": [
    {"type": "set_variable", "value": {"name": "max_queue", "value": "8"}},
    {"type": "set_variable", "value": {"name": "processed", "value": "0"}},
    {"type": "check_queue", "selector": ".queue", "check_type": "less", "expected_value": "${max_queue}"},
    {"type": "while_begin", "value": {"condition": "check_result == true"}},
      {"type": "click_button", "selector": "#add-task"},
      {"type": "wait", "value": 2000},
      {"type": "increment_variable", "value": {"name": "processed"}},
      {"type": "check_queue", "selector": ".queue", "check_type": "less", "expected_value": "${max_queue}"},
    {"type": "while_end"},
    {"type": "log_message", "value": {"message": "Processed ${processed} tasks"}}
  ]
}
```

---

*Last Updated: August 2024*