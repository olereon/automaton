# Core Concepts

## Table of Contents
- [Introduction](#introduction)
- [Automation Sequences](#automation-sequences)
- [Actions and Selectors](#actions-and-selectors)
- [Variables and Substitution](#variables-and-substitution)
- [Flow Control](#flow-control)
- [Browser Context Management](#browser-context-management)
- [Execution Context](#execution-context)
- [Error Handling](#error-handling)

## Introduction

This document explains the core concepts and fundamental principles that underpin the Automaton web automation framework. Understanding these concepts is essential for creating effective and reliable automation sequences.

Automaton is built around a modular architecture that separates concerns into distinct components. At its heart, the framework is designed to be intuitive while providing powerful capabilities for complex automation scenarios.

## Automation Sequences

An automation sequence is a series of actions that Automaton executes to accomplish a specific task. Sequences are typically defined in JSON format and can be created either programmatically using the builder pattern or manually as JSON files.

### Structure of an Automation Sequence

```json
{
  "name": "Example Automation",
  "url": "https://example.com",
  "headless": false,
  "viewport": {
    "width": 1280,
    "height": 720
  },
  "keep_browser_open": true,
  "actions": [
    {
      "type": "WAIT_FOR_ELEMENT",
      "selector": "h1",
      "timeout": 10000,
      "description": "Wait for page title"
    },
    {
      "type": "CLICK_BUTTON",
      "selector": "#submit-button",
      "description": "Click submit button"
    }
  ]
}
```

### Sequence Configuration

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Name of the automation sequence |
| `url` | string | Yes | Starting URL for the automation |
| `headless` | boolean | No | Run browser in headless mode (default: false) |
| `viewport` | object | No | Browser viewport dimensions (default: 1280x720) |
| `keep_browser_open` | boolean | No | Keep browser open after completion (default: true) |
| `actions` | array | Yes | Array of actions to execute |

### Creating Sequences with the Builder Pattern

The builder pattern provides a fluent, programmatic way to create automation sequences:

```python
from src.core.engine import AutomationSequenceBuilder

# Create a new automation sequence
builder = AutomationSequenceBuilder(
    name="Example Automation",
    url="https://example.com",
    keep_browser_open=True
)

# Add actions to the sequence
sequence = (
    builder
    .add_wait_for_element("h1", description="Wait for page title")
    .add_click_button("#submit-button", description="Click submit button")
    .add_wait(5000, description="Wait for 5 seconds")
    .build()
)

# Save the sequence to a file
builder.save_to_file("example_automation.json")
```

## Actions and Selectors

Actions are the individual operations that make up an automation sequence. Each action has a specific type and associated parameters that define its behavior.

### Action Types

Automaton supports a wide variety of action types:

| Action Type | Description |
|-------------|-------------|
| `LOGIN` | Authenticate with username and password |
| `INPUT_TEXT` | Enter text into an input field |
| `CLICK_BUTTON` | Click a button or clickable element |
| `UPLOAD_IMAGE` | Upload an image file |
| `TOGGLE_SETTING` | Toggle a checkbox or switch setting |
| `CHECK_ELEMENT` | Verify an element's state or content |
| `WAIT_FOR_ELEMENT` | Wait for an element to appear on the page |
| `WAIT` | Pause execution for a specified time |
| `DOWNLOAD_FILE` | Download a file from a link |
| `REFRESH_PAGE` | Refresh the current page |
| `SWITCH_PANEL` | Switch to a different panel or tab |
| `SET_VARIABLE` | Set a variable value |
| `INCREMENT_VARIABLE` | Increment a variable value |
| `LOG_MESSAGE` | Write a message to a log file |

### Action Structure

All actions share a common structure:

```json
{
  "type": "ACTION_TYPE",
  "selector": "css-selector",
  "value": "action-value",
  "timeout": 10000,
  "description": "Action description"
}
```

### Selectors

Selectors are used to identify elements on a web page. Automaton primarily uses CSS selectors, which are patterns used to select elements based on their attributes, classes, IDs, and relationships with other elements.

#### Common Selector Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| `#id` | Element with specific ID | `#submit-button` |
| `.class` | Elements with specific class | `.menu-item` |
| `element` | Elements of a specific type | `button` |
| `[attribute]` | Elements with specific attribute | `[data-test-id="submit"]` |
| `parent child` | Child elements of a parent | `div.menu a` |
| `:nth-child(n)` | Nth child of a parent | `li:nth-child(2)` |

#### Selector Best Practices

1. **Be Specific**: Use IDs and unique attributes when possible
2. **Avoid Brittle Selectors**: Don't rely on auto-generated IDs or complex nested structures
3. **Use Test Attributes**: Prefer `data-test-*` attributes for testing selectors
4. **Keep It Simple**: Simple selectors are more maintainable and less likely to break

#### Example Selectors

```json
{
  "type": "CLICK_BUTTON",
  "selector": "#submit-button",  // ID selector
  "description": "Click submit button"
}
```

```json
{
  "type": "INPUT_TEXT",
  "selector": "input[name='username']",  // Attribute selector
  "value": "testuser",
  "description": "Enter username"
}
```

```json
{
  "type": "CLICK_BUTTON",
  "selector": ".btn-primary",  // Class selector
  "description": "Click primary button"
}
```

## Variables and Substitution

Variables allow you to store and reuse values throughout your automation sequences. This is particularly useful for dynamic data, such as usernames, passwords, or other values that might change between runs.

### Setting Variables

Use the `SET_VARIABLE` action to set a variable:

```json
{
  "type": "SET_VARIABLE",
  "value": {
    "variable": "username",
    "value": "testuser"
  },
  "description": "Set username variable"
}
```

### Incrementing Variables

Use the `INCREMENT_VARIABLE` action to increment a numeric variable:

```json
{
  "type": "INCREMENT_VARIABLE",
  "value": {
    "variable": "counter",
    "amount": 1
  },
  "description": "Increment counter"
}
```

### Variable Substitution

Variables can be referenced in other actions using the `${variable}` syntax:

```json
{
  "type": "INPUT_TEXT",
  "selector": "input[name='username']",
  "value": "${username}",
  "description": "Enter username from variable"
}
```

### Variable Scope

Variables are scoped to the current automation sequence and persist for the duration of the sequence execution. They are reset each time the sequence is run.

### Example Variable Usage

```json
{
  "name": "Variable Example",
  "url": "https://example.com",
  "actions": [
    {
      "type": "SET_VARIABLE",
      "value": {
        "variable": "username",
        "value": "testuser"
      },
      "description": "Set username"
    },
    {
      "type": "SET_VARIABLE",
      "value": {
        "variable": "counter",
        "value": "1"
      },
      "description": "Set counter to 1"
    },
    {
      "type": "INPUT_TEXT",
      "selector": "input[name='username']",
      "value": "${username}",
      "description": "Enter username"
    },
    {
      "type": "INPUT_TEXT",
      "selector": "input[name='counter']",
      "value": "${counter}",
      "description": "Enter counter value"
    },
    {
      "type": "INCREMENT_VARIABLE",
      "value": {
        "variable": "counter",
        "amount": 1
      },
      "description": "Increment counter"
    }
  ]
}
```

## Flow Control

Flow control actions allow you to create conditional logic and loops in your automation sequences. This enables more complex and dynamic automation scenarios.

### Conditional Logic

Automaton supports IF/ELSE conditional logic:

```json
{
  "type": "IF_BEGIN",
  "value": {
    "condition": "check_passed"
  },
  "description": "Begin IF block"
}
```

```json
{
  "type": "ELIF",
  "value": {
    "condition": "value_equals",
    "expected_value": "expected"
  },
  "description": "ELIF condition"
}
```

```json
{
  "type": "ELSE",
  "value": {},
  "description": "ELSE block"
}
```

```json
{
  "type": "IF_END",
  "value": {},
  "description": "End IF block"
}
```

### Loops

Automaton supports WHILE loops for repetitive tasks:

```json
{
  "type": "WHILE_BEGIN",
  "value": {
    "condition": "check_failed"
  },
  "description": "Begin WHILE loop"
}
```

```json
{
  "type": "WHILE_END",
  "value": {},
  "description": "End WHILE loop"
}
```

### Loop Control

You can control loop execution with BREAK and CONTINUE statements:

```json
{
  "type": "BREAK",
  "value": {},
  "description": "Break out of loop"
}
```

```json
{
  "type": "CONTINUE",
  "value": {},
  "description": "Continue to next iteration"
}
```

### Condition Types

| Condition | Description |
|-----------|-------------|
| `check_passed` | True if the last CHECK_ELEMENT action passed |
| `check_failed` | True if the last CHECK_ELEMENT action failed |
| `value_equals` | True if the actual value equals the expected value |
| `value_not_equals` | True if the actual value does not equal the expected value |

### Example Flow Control

```json
{
  "name": "Flow Control Example",
  "url": "https://example.com",
  "actions": [
    {
      "type": "CHECK_ELEMENT",
      "selector": ".notification",
      "value": {
        "check": "contains",
        "value": "Success",
        "attribute": "text"
      },
      "description": "Check for success notification"
    },
    {
      "type": "IF_BEGIN",
      "value": {
        "condition": "check_passed"
      },
      "description": "If success notification found"
    },
    {
      "type": "LOG_MESSAGE",
      "value": {
        "message": "Success notification found"
      },
      "description": "Log success"
    },
    {
      "type": "IF_END",
      "value": {},
      "description": "End IF block"
    },
    {
      "type": "WHILE_BEGIN",
      "value": {
        "condition": "check_failed"
      },
      "description": "While no success notification"
    },
    {
      "type": "CLICK_BUTTON",
      "selector": "#retry-button",
      "description": "Click retry button"
    },
    {
      "type": "WAIT",
      "value": 2000,
      "description": "Wait 2 seconds"
    },
    {
      "type": "CHECK_ELEMENT",
      "selector": ".notification",
      "value": {
        "check": "contains",
        "value": "Success",
        "attribute": "text"
      },
      "description": "Check for success notification"
    },
    {
      "type": "WHILE_END",
      "value": {},
      "description": "End WHILE loop"
    }
  ]
}
```

## Browser Context Management

Browser context management is a crucial aspect of web automation. Automaton provides robust tools for managing browser instances, pages, and contexts.

### Browser Lifecycle

Automaton manages the entire browser lifecycle:

1. **Initialization**: Creates a new browser instance with the specified configuration
2. **Context Creation**: Creates a browser context for isolation
3. **Page Creation**: Creates a new page/tab within the context
4. **Navigation**: Navigates to the specified URL
5. **Execution**: Executes the automation sequence
6. **Cleanup**: Cleans up resources based on configuration

### Browser Configuration

Browser behavior can be configured through several options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `headless` | boolean | false | Run browser without visible UI |
| `viewport` | object | {width: 1280, height: 720} | Browser viewport dimensions |
| `keep_browser_open` | boolean | true | Keep browser open after automation completes |

### Context Isolation

Browser contexts provide isolation between automation runs:

- **Cookies**: Each context has its own cookie jar
- **LocalStorage**: Each context has isolated local storage
- **SessionStorage**: Each context has isolated session storage
- **Cache**: Each context has its own cache

### Page Management

Automaton can manage multiple pages within a single browser context:

- **Navigation**: Navigate to different URLs
- **Switching**: Switch between open pages/tabs
- **Creation**: Open new pages/tabs as needed
- **Closure**: Close pages when no longer needed

### Example Browser Configuration

```json
{
  "name": "Browser Configuration Example",
  "url": "https://example.com",
  "headless": false,
  "viewport": {
    "width": 1920,
    "height": 1080
  },
  "keep_browser_open": true,
  "actions": [
    {
      "type": "SWITCH_PANEL",
      "selector": "#new-tab-button",
      "description": "Open new tab"
    },
    {
      "type": "WAIT_FOR_ELEMENT",
      "selector": "h1",
      "timeout": 10000,
      "description": "Wait for page to load"
    }
  ]
}
```

## Execution Context

The execution context is the internal state that Automaton maintains while running an automation sequence. It includes information about variables, loop states, conditional states, and more.

### Context Components

The execution context consists of several key components:

1. **Variables**: A dictionary of variable names and values
2. **Loop Stack**: A stack of active loops and their states
3. **Conditional Stack**: A stack of active conditional blocks
4. **Instruction Pointer**: The current position in the action sequence
5. **Last Check Result**: The result of the last CHECK_ELEMENT action

### State Management

Automaton carefully manages state throughout execution:

- **Variables**: Persist for the duration of the sequence
- **Loop State**: Each loop maintains its own iteration count and condition state
- **Conditional State**: Each conditional block maintains its execution state
- **Error State**: Tracks errors and determines whether to continue execution

### Execution Flow

The execution context controls the flow of execution:

1. **Sequential Execution**: Actions are executed in order by default
2. **Conditional Execution**: Actions may be skipped based on conditional state
3. **Loop Execution**: Actions may be repeated based on loop conditions
4. **Error Recovery**: Execution may continue or halt based on error state

### Context Persistence

The execution context persists for the duration of a single automation sequence:

- **Sequence Start**: Context is initialized with default values
- **Sequence Execution**: Context is updated as actions are executed
- **Sequence End**: Context is discarded (variables are not persisted between runs)

## Error Handling

Robust error handling is essential for reliable automation. Automaton provides comprehensive error handling and recovery mechanisms.

### Error Types

Automaton can encounter several types of errors:

1. **Selector Errors**: Elements cannot be found with the provided selector
2. **Timeout Errors**: Actions take longer than the specified timeout
3. **Navigation Errors**: Page navigation fails or times out
4. **Authentication Errors**: Login actions fail due to invalid credentials
5. **Network Errors**: Network connectivity issues prevent action completion
6. **Browser Errors**: Browser crashes or becomes unresponsive

### Error Recovery

Automaton includes several error recovery strategies:

1. **Retry Mechanisms**: Automatically retry failed actions with exponential backoff
2. **Fallback Selectors**: Try alternative selectors if the primary one fails
3. **Smart Waiting**: Wait for page stability before proceeding
4. **State Reset**: Reset page state between actions to ensure clean execution

### Error Logging

Automaton provides detailed error logging:

```json
{
  "success": false,
  "actions_completed": 3,
  "total_actions": 5,
  "errors": [
    {
      "action_index": 3,
      "action_type": "CLICK_BUTTON",
      "action_description": "Click submit button",
      "selector": "#submit-button",
      "error": "Element not found: #submit-button",
      "error_type": "SelectorError",
      "page_url": "https://example.com/form",
      "page_title": "Example Form"
    }
  ]
}
```

### Error Handling Strategies

1. **Preventive**: Use robust selectors and appropriate timeouts
2. **Detective**: Check for error conditions and handle them gracefully
3. **Corrective**: Implement retry logic and fallback mechanisms
4. **Adaptive**: Learn from errors and adjust future behavior

### Example Error Handling

```json
{
  "name": "Error Handling Example",
  "url": "https://example.com",
  "actions": [
    {
      "type": "WAIT_FOR_ELEMENT",
      "selector": "#submit-button",
      "timeout": 10000,
      "description": "Wait for submit button"
    },
    {
      "type": "CHECK_ELEMENT",
      "selector": "#submit-button",
      "value": {
        "check": "not_zero",
        "attribute": "text"
      },
      "description": "Check if button exists"
    },
    {
      "type": "IF_BEGIN",
      "value": {
        "condition": "check_passed"
      },
      "description": "If button exists"
    },
    {
      "type": "CLICK_BUTTON",
      "selector": "#submit-button",
      "description": "Click submit button"
    },
    {
      "type": "IF_END",
      "value": {},
      "description": "End IF block"
    },
    {
      "type": "LOG_MESSAGE",
      "value": {
        "message": "Submit button not found, using alternative approach"
      },
      "description": "Log error message"
    }
  ]
}
```

## Next Steps

Now that you understand the core concepts of Automaton, you can:

1. Follow the [User Guide](4_user_guide.md) to create your first automation
2. Explore the [API Reference](5_api_reference.md) for detailed technical information
3. Learn about [Advanced Usage](7_advanced_usage.md) for more complex scenarios
4. Check the [Troubleshooting Guide](8_troubleshooting_guide.md) for help with common issues