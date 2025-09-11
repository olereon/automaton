# Automaton API Reference

## Introduction

This document provides a comprehensive reference to the Automaton API, including all available actions, their parameters, and usage examples. The API is organized by functional categories for easy navigation.

## Table of Contents

1. [Basic Actions](#basic-actions)
2. [Advanced Actions](#advanced-actions)
3. [Flow Control Actions](#flow-control-actions)
4. [Generation Download Actions](#generation-download-actions)
5. [Action Parameters](#action-parameters)
6. [Response Formats](#response-formats)
7. [Error Handling](#error-handling)

## Basic Actions

### INPUT_TEXT

Fills a text input field with the specified value.

**Parameters**:
- `selector` (string, required): CSS selector for the input element
- `value` (string, required): Text to input

**Example**:
```json
{
  "type": "input_text",
  "selector": "#username",
  "value": "john_doe"
}
```

### CLICK_BUTTON

Clicks on a button or clickable element.

**Parameters**:
- `selector` (string, required): CSS selector for the button element

**Example**:
```json
{
  "type": "click_button",
  "selector": "#submit-button"
}
```

### UPLOAD_IMAGE

Uploads a file to a file input element.

**Parameters**:
- `selector` (string, required): CSS selector for the file input element
- `value` (string, required): Path to the file to upload

**Example**:
```json
{
  "type": "upload_image",
  "selector": "#file-upload",
  "value": "/path/to/image.jpg"
}
```

### TOGGLE_SETTING

Toggles a checkbox or radio button.

**Parameters**:
- `selector` (string, required): CSS selector for the checkbox/radio element
- `value` (boolean, optional): Whether to check (true) or uncheck (false). Defaults to true.

**Example**:
```json
{
  "type": "toggle_setting",
  "selector": "#remember-me",
  "value": true
}
```

### WAIT

Pauses execution for a specified duration.

**Parameters**:
- `value` (number, required): Duration to wait in milliseconds

**Example**:
```json
{
  "type": "wait",
  "value": 2000
}
```

### WAIT_FOR_ELEMENT

Waits for an element to appear on the page.

**Parameters**:
- `selector` (string, required): CSS selector for the element to wait for
- `timeout` (number, optional): Maximum time to wait in milliseconds. Defaults to 30000.

**Example**:
```json
{
  "type": "wait_for_element",
  "selector": ".success-message",
  "timeout": 10000
}
```

### REFRESH_PAGE

Reloads the current page.

**Parameters**: None

**Example**:
```json
{
  "type": "refresh_page"
}
```

### EXPAND_DIALOG

Expands a collapsible dialog or section.

**Parameters**:
- `selector` (string, required): CSS selector for the expandable element

**Example**:
```json
{
  "type": "expand_dialog",
  "selector": "#advanced-settings"
}
```

### SWITCH_PANEL

Switches to a different panel or tab.

**Parameters**:
- `selector` (string, required): CSS selector for the panel/tab element

**Example**:
```json
{
  "type": "switch_panel",
  "selector": "#tab-2"
}
```

## Advanced Actions

### CHECK_ELEMENT

Checks if an element exists or has specific properties.

**Parameters**:
- `selector` (string, required): CSS selector for the element to check
- `operator` (string, optional): Comparison operator. One of: "exists", "not_exists", "contains", "equals", "visible", "hidden". Defaults to "exists".
- `value` (string, optional): Expected value for comparison (used with "contains" and "equals")

**Example**:
```json
{
  "type": "check_element",
  "selector": ".error-message",
  "operator": "not_exists"
}
```

### CHECK_QUEUE

Checks the status or capacity of a queue.

**Parameters**:
- `selector` (string, required): CSS selector for the queue element
- `operator` (string, optional): Comparison operator. One of: "exists", "not_exists", "count", "capacity". Defaults to "exists".
- `value` (string/number, optional): Expected value for comparison

**Example**:
```json
{
  "type": "check_queue",
  "selector": ".queue-items",
  "operator": "count",
  "value": 5
}
```

### SET_VARIABLE

Stores a value in a variable for later use.

**Parameters**:
- `value` (object, required): Object with "name" and "value" properties
  - `name` (string): Variable name
  - `value` (string/number/boolean): Variable value

**Example**:
```json
{
  "type": "set_variable",
  "value": {
    "name": "username",
    "value": "john_doe"
  }
}
```

### INCREMENT_VARIABLE

Increments a numeric variable by a specified amount.

**Parameters**:
- `value` (object, required): Object with "name" and "increment" properties
  - `name` (string): Variable name
  - `increment` (number): Amount to increment by

**Example**:
```json
{
  "type": "increment_variable",
  "value": {
    "name": "counter",
    "increment": 1
  }
}
```

### LOG_MESSAGE

Logs a message to the console.

**Parameters**:
- `value` (string, required): Message to log

**Example**:
```json
{
  "type": "log_message",
  "value": "Starting form submission"
}
```

### LOGIN

Performs a login operation with username and password.

**Parameters**:
- `value` (object, required): Object with "username" and "password" properties
  - `username` (string): Username for login
  - `password` (string): Password for login

**Example**:
```json
{
  "type": "login",
  "value": {
    "username": "john_doe",
    "password": "secure_password"
  }
}
```

### DOWNLOAD_FILE

Downloads a file from a link or button.

**Parameters**:
- `selector` (string, required): CSS selector for the download link/button
- `value` (object, optional): Download options
  - `download_dir` (string): Directory to save the file. Defaults to "./downloads".
  - `filename` (string): Filename to save as. If not provided, uses the original filename.

**Example**:
```json
{
  "type": "download_file",
  "selector": "#download-link",
  "value": {
    "download_dir": "./reports",
    "filename": "monthly_report.pdf"
  }
}
```

## Flow Control Actions

### IF_BEGIN / IF_END

Starts and ends a conditional block.

**Parameters**:
- `condition` (string, required): Condition to evaluate
- `operator` (string, optional): Comparison operator. One of: "==", "!=", ">", "<", ">=", "<=". Defaults to "==".
- `value` (string/number/boolean, optional): Value to compare against

**Example**:
```json
{
  "type": "if_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "click_button",
  "selector": "#submit-button"
},
{
  "type": "if_end"
}
```

### ELIF

Adds an else-if condition to an existing if block.

**Parameters**:
- `condition` (string, required): Condition to evaluate
- `operator` (string, optional): Comparison operator. One of: "==", "!=", ">", "<", ">=", "<=". Defaults to "==".
- `value` (string/number/boolean, optional): Value to compare against

**Example**:
```json
{
  "type": "if_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "click_button",
  "selector": "#submit-button"
},
{
  "type": "elif",
  "condition": "check_result",
  "operator": "==",
  "value": "pending"
},
{
  "type": "log_message",
  "value": "Status is pending"
},
{
  "type": "if_end"
}
```

### ELSE

Adds an else condition to an existing if block.

**Parameters**: None

**Example**:
```json
{
  "type": "if_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "click_button",
  "selector": "#submit-button"
},
{
  "type": "else"
},
{
  "type": "log_message",
  "value": "Condition not met"
},
{
  "type": "if_end"
}
```

### WHILE_BEGIN / WHILE_END

Starts and ends a loop block.

**Parameters**:
- `condition` (string, required): Condition to evaluate for each iteration
- `operator` (string, optional): Comparison operator. One of: "==", "!=", ">", "<", ">=", "<=". Defaults to "==".
- `value` (string/number/boolean, optional): Value to compare against

**Example**:
```json
{
  "type": "while_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "click_button",
  "selector": "#load-more"
},
{
  "type": "wait",
  "value": 1000
},
{
  "type": "while_end"
}
```

### BREAK

Exits the current loop.

**Parameters**: None

**Example**:
```json
{
  "type": "while_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "check_element",
  "selector": ".error-message",
  "operator": "exists"
},
{
  "type": "if_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
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

### CONTINUE

Skips to the next iteration of the current loop.

**Parameters**: None

**Example**:
```json
{
  "type": "while_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "check_element",
  "selector": ".special-item",
  "operator": "exists"
},
{
  "type": "if_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "continue"
},
{
  "type": "if_end"
},
{
  "type": "click_button",
  "selector": "#process-item"
},
{
  "type": "while_end"
}
```

### CONDITIONAL_WAIT

Waits for a condition to be met, with retries and backoff.

**Parameters**:
- `selector` (string, required): CSS selector for the element to check
- `timeout` (number, optional): Maximum time to wait in milliseconds. Defaults to 30000.
- `interval` (number, optional): Initial retry interval in milliseconds. Defaults to 1000.
- `backoff` (number, optional): Multiplier for interval increase on each retry. Defaults to 1.5.
- `operator` (string, optional): Comparison operator. One of: "exists", "not_exists", "contains", "equals", "visible", "hidden". Defaults to "exists".
- `value` (string, optional): Expected value for comparison (used with "contains" and "equals")

**Example**:
```json
{
  "type": "conditional_wait",
  "selector": ".dynamic-content",
  "timeout": 60000,
  "interval": 2000,
  "backoff": 2,
  "operator": "contains",
  "value": "Loaded"
}
```

### SKIP_IF

Skips the next action if a condition is met.

**Parameters**:
- `condition` (string, required): Condition to evaluate
- `operator` (string, optional): Comparison operator. One of: "==", "!=", ">", "<", ">=", "<=". Defaults to "==".
- `value` (string/number/boolean, optional): Value to compare against

**Example**:
```json
{
  "type": "skip_if",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "click_button",
  "selector": "#optional-button"
}
```

### STOP_AUTOMATION

Stops the automation execution with an optional message.

**Parameters**:
- `value` (string, optional): Message to log when stopping

**Example**:
```json
{
  "type": "stop_automation",
  "value": "Critical error encountered"
}
```

## Generation Download Actions

### START_GENERATION_DOWNLOADS

Starts a batch download process for generated content.

**Parameters**:
- `value` (object, required): Configuration for generation downloads
  - `image_to_video_text` (string): Text identifier for image-to-video option
  - `download_no_watermark_text` (string): Text identifier for no-watermark option
  - `max_downloads` (number, optional): Maximum number of downloads to start. Defaults to 10.
  - `download_dir` (string, optional): Directory to save downloads. Defaults to "./downloads".

**Example**:
```json
{
  "type": "start_generation_downloads",
  "value": {
    "image_to_video_text": "Image to video",
    "download_no_watermark_text": "Download without Watermark",
    "max_downloads": 5,
    "download_dir": "./generated_videos"
  }
}
```

### STOP_GENERATION_DOWNLOADS

Stops all active generation downloads.

**Parameters**: None

**Example**:
```json
{
  "type": "stop_generation_downloads"
}
```

### CHECK_GENERATION_STATUS

Checks the status of generation downloads.

**Parameters**:
- `value` (object, optional): Status check options
  - `detailed` (boolean): Whether to return detailed status information. Defaults to false.

**Example**:
```json
{
  "type": "check_generation_status",
  "value": {
    "detailed": true
  }
}
```

## Action Parameters

### Common Parameters

Many actions share common parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `selector` | string | Varies | CSS selector for target element |
| `value` | varies | Varies | Primary value for the action |
| `timeout` | number | Optional | Timeout in milliseconds |
| `operator` | string | Optional | Comparison operator for checks |
| `condition` | string | Optional | Condition for flow control |

### Parameter Substitution

Variables can be referenced in parameters using the `${variable_name}` syntax:

```json
{
  "type": "set_variable",
  "value": {
    "name": "username",
    "value": "john_doe"
  }
},
{
  "type": "input_text",
  "selector": "#username-field",
  "value": "${username}"
}
```

## Response Formats

### Action Response

Each action execution returns a response object:

```json
{
  "success": true,
  "message": "Action completed successfully",
  "data": {
    "result": "Expected result data"
  },
  "variables": {
    "username": "john_doe"
  }
}
```

### Error Response

When an action fails, an error response is returned:

```json
{
  "success": false,
  "message": "Element not found: #non-existent-element",
  "error": {
    "type": "ElementNotFoundError",
    "details": "Could not locate element with selector '#non-existent-element'"
  },
  "variables": {
    "username": "john_doe"
  }
}
```

### Batch Response

When executing multiple actions, a batch response is returned:

```json
{
  "success": true,
  "message": "Automation completed successfully",
  "results": [
    {
      "action": "input_text",
      "success": true,
      "message": "Text input successful"
    },
    {
      "action": "click_button",
      "success": false,
      "message": "Button not found"
    }
  ],
  "variables": {
    "username": "john_doe"
  }
}
```

## Error Handling

### Error Types

| Error Type | Description | Common Causes |
|------------|-------------|---------------|
| `ElementNotFoundError` | Target element not found | Incorrect selector, element not loaded |
| `TimeoutError` | Action took too long to complete | Slow network, slow page load |
| `NetworkError` | Network-related failure | Connection lost, server error |
| `AuthenticationError` | Login or permission failure | Invalid credentials, insufficient permissions |
| `ValidationError` | Input validation failed | Invalid parameter values |
| `ExecutionError` | General execution failure | Script error, unexpected state |

### Retry Mechanisms

Some actions include automatic retry mechanisms:

- `WAIT_FOR_ELEMENT`: Automatically retries until element appears or timeout
- `CONDITIONAL_WAIT`: Implements exponential backoff retry strategy
- `CHECK_ELEMENT`: Can be combined with `IF_BEGIN` for manual retry logic

### Error Recovery

Use flow control actions to implement error recovery:

```json
{
  "type": "check_element",
  "selector": ".error-message",
  "operator": "exists"
},
{
  "type": "if_begin",
  "condition": "check_result",
  "operator": "==",
  "value": true
},
{
  "type": "refresh_page"
},
{
  "type": "wait",
  "value": 2000
},
{
  "type": "if_end"
}
```

## Next Steps

With this API reference, you can:

1. [Explore Component Documentation](6_components_reference.md) for implementation details
2. [Learn Advanced Usage](7_advanced_usage.md) for complex scenarios
3. [Review Troubleshooting Techniques](8_troubleshooting_guide.md) for common issues
4. [Check Contributing Guidelines](9_contributing_guide.md) for development information

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*