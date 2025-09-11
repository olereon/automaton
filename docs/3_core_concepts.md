# Automaton Core Concepts

## Introduction

This document explains the fundamental concepts and terminology used in Automaton. Understanding these core concepts is essential for effectively using the framework and creating powerful automation sequences.

## Table of Contents

1. [Automation Sequences](#automation-sequences)
2. [Actions](#actions)
3. [Selectors](#selectors)
4. [Variables](#variables)
5. [Flow Control](#flow-control)
6. [Controller System](#controller-system)
7. [Browser Context](#browser-context)
8. [Error Handling](#error-handling)
9. [Logging](#logging)

## Automation Sequences

An automation sequence is the fundamental unit of work in Automaton. It represents a series of actions to be performed on a web page, along with configuration and metadata.

### Sequence Structure

```json
{
  "name": "Example Automation",
  "url": "https://example.com",
  "headless": false,
  "viewport": {
    "width": 1280,
    "height": 720
  },
  "actions": [
    {
      "type": "wait_for_element",
      "selector": "#main-content"
    },
    {
      "type": "click_button",
      "selector": "#submit-button"
    }
  ]
}
```

### Key Components

- **name**: Human-readable name for the automation
- **url**: Starting URL for the automation
- **headless**: Whether to run browser without visible UI
- **viewport**: Browser window dimensions
- **actions**: Array of action objects to execute

## Actions

Actions are individual operations that Automaton performs. There are over 30 action types organized into categories.

### Action Structure

Every action follows this basic structure:

```json
{
  "type": "action_type",
  "selector": "css_selector",
  "value": "action_value"
}
```

### Action Categories

#### Basic Actions
- `INPUT_TEXT`: Fill text fields
- `CLICK_BUTTON`: Click elements
- `UPLOAD_IMAGE`: Upload files
- `TOGGLE_SETTING`: Check/uncheck boxes
- `WAIT`: Pause execution
- `WAIT_FOR_ELEMENT`: Wait for element
- `REFRESH_PAGE`: Reload page

#### Advanced Actions
- `CHECK_ELEMENT`: Validate content
- `CHECK_QUEUE`: Monitor queues
- `SET_VARIABLE`: Store values
- `INCREMENT_VARIABLE`: Increment numbers
- `LOG_MESSAGE`: Record progress
- `LOGIN`: Automated login
- `DOWNLOAD_FILE`: Download files

#### Flow Control Actions
- `IF_BEGIN`/`IF_END`: Conditional blocks
- `ELIF`/`ELSE`: Conditional branches
- `WHILE_BEGIN`/`WHILE_END`: Loop blocks
- `BREAK`/`CONTINUE`: Loop control
- `CONDITIONAL_WAIT`: Retry with backoff
- `SKIP_IF`: Conditional skip
- `STOP_AUTOMATION`: Terminate

## Selectors

Selectors are CSS expressions used to locate elements on a web page. Automaton primarily uses CSS selectors, but also supports text-based detection for enhanced reliability.

### CSS Selectors

```json
{
  "type": "click_button",
  "selector": "#submit-button"
}
```

### Text-Based Detection

For enhanced reliability, some actions support text-based detection:

```json
{
  "type": "start_generation_downloads",
  "value": {
    "image_to_video_text": "Image to video",
    "download_no_watermark_text": "Download without Watermark"
  }
}
```

### Selector Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| ID Selectors | Select by element ID | `#submit-button` |
| Class Selectors | Select by element class | `.button.primary` |
| Attribute Selectors | Select by attribute value | `[data-testid="submit"]` |
| Hierarchical Selectors | Select by DOM hierarchy | `div.container > button#submit` |
| Text-Based | Select by visible text | Used in generation downloads |

## Variables

Variables allow you to store and reuse values throughout an automation sequence. They support dynamic substitution and can be manipulated during execution.

### Variable Types

- **String Variables**: Text values
- **Number Variables**: Numeric values
- **Boolean Variables**: True/false values
- **System Variables**: Pre-defined variables (e.g., `${timestamp}`)

### Variable Substitution

Variables can be referenced using the `${variable_name}` syntax:

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

### Variable Manipulation

```json
{
  "type": "set_variable",
  "value": {
    "name": "counter",
    "value": "0"
  }
},
{
  "type": "increment_variable",
  "value": {
    "name": "counter",
    "increment": "1"
  }
}
```

## Flow Control

Flow control structures allow you to create conditional logic and loops in your automations.

### Conditional Execution

```json
{
  "type": "if_begin",
  "condition": "check_result == true"
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
  "value": "Form not ready for submission"
},
{
  "type": "if_end"
}
```

### Loops

```json
{
  "type": "while_begin",
  "condition": "check_result == true"
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

### Loop Control

```json
{
  "type": "while_begin",
  "condition": "check_result == true"
},
{
  "type": "check_element",
  "selector": ".error-message",
  "operator": "not_exists"
},
{
  "type": "if_begin",
  "condition": "check_result == false"
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

## Controller System

The controller system provides centralized management of automation execution, including start, stop, and pause functionality.

### Controller Components

- **Controller**: Central management object
- **Control Signals**: Messages passed between components
- **State Management**: Tracking execution state

### Control Flow

1. Controller receives start signal
2. Controller initializes automation engine
3. Engine executes actions, checking for control signals
4. Controller processes stop signals and terminates gracefully

### Stop Functionality

The controller system enables graceful termination of automations:

```json
{
  "type": "stop_automation",
  "value": "User requested stop"
}
```

## Browser Context

Browser context refers to the state and environment of the browser during automation execution.

### Context Components

- **Browser Instance**: The Chromium browser controlled by Playwright
- **Page**: The current web page being automated
- **Viewport**: Browser window dimensions
- **Cookies**: Session cookies and storage
- **LocalStorage**: Browser local storage

### Context Management

```json
{
  "name": "Example Automation",
  "url": "https://example.com",
  "headless": false,
  "viewport": {
    "width": 1600,
    "height": 1000
  },
  "keep_browser_open": true
}
```

## Error Handling

Automaton includes robust error handling mechanisms to manage failures and retries.

### Error Types

- **Element Not Found**: Target element not located on page
- **Timeout**: Action took longer than allowed time
- **Network Error**: Network-related failure
- **Authentication Error**: Login or permission failure
- **Validation Error**: Content validation failed

### Retry Mechanisms

```json
{
  "type": "conditional_wait",
  "value": {
    "selector": "#dynamic-content",
    "timeout": 30000,
    "interval": 1000
  }
}
```

### Error Recovery

```json
{
  "type": "if_begin",
  "condition": "error_occurred == true"
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

## Logging

Automaton provides comprehensive logging to track execution progress and debug issues.

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General information about execution
- **WARNING**: Potential issues that don't stop execution
- **ERROR**: Serious errors that may stop execution
- **CRITICAL**: Critical errors that stop execution

### Log Actions

```json
{
  "type": "log_message",
  "value": "Starting form submission process"
}
```

### Log Configuration

```bash
export AUTOMATON_LOG_LEVEL=DEBUG
```

## Next Steps

With these core concepts understood, you can:

1. [Read the User Guide](4_user_guide.md) for practical usage examples
2. [Explore the API Reference](5_api_reference.md) for technical details
3. [Check Component Documentation](6_components_reference.md) for implementation specifics
4. [Review Advanced Usage](7_advanced_usage.md) for complex scenarios

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*