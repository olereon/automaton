# Configuration Reference

## Introduction

This document provides a comprehensive reference for all configuration options available in Automaton. Configuration can be provided through JSON files, YAML files, or environment variables, allowing you to customize the behavior of your automation workflows.

## Table of Contents

1. [Configuration Formats](#configuration-formats)
2. [Global Configuration](#global-configuration)
3. [Browser Configuration](#browser-configuration)
4. [Action Configuration](#action-configuration)
5. [Logging Configuration](#logging-configuration)
6. [Security Configuration](#security-configuration)
7. [Performance Configuration](#performance-configuration)
8. [Environment Variables](#environment-variables)
9. [Configuration Examples](#configuration-examples)

## Configuration Formats

Automaton supports multiple configuration formats:

### JSON Configuration

```json
{
  "name": "My Automation",
  "description": "Example automation workflow",
  "url": "https://example.com",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": []
}
```

### YAML Configuration

```yaml
name: My Automation
description: Example automation workflow
url: https://example.com
browser:
  type: chromium
  headless: true
actions: []
```

### Environment Variables

Environment variables can be used to override configuration values:

```bash
export AUTOMATON_BROWSER_TYPE=chromium
export AUTOMATON_BROWSER_HEADLESS=true
export AUTOMATON_LOG_LEVEL=info
```

## Global Configuration

Global configuration options control the overall behavior of Automaton.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| name | string | - | Name of the automation workflow |
| description | string | - | Description of the automation workflow |
| url | string | - | Starting URL for the automation |
| timeout | integer | 30000 | Global timeout in milliseconds |
| retry_count | integer | 3 | Number of times to retry failed actions |
| retry_delay | integer | 1000 | Delay between retries in milliseconds |
| output_dir | string | "./output" | Directory for output files |
| variables | object | {} | Global variables accessible in actions |

### Example

```json
{
  "name": "Web Scraping Automation",
  "description": "Extract data from product pages",
  "url": "https://example.com/products",
  "timeout": 60000,
  "retry_count": 5,
  "retry_delay": 2000,
  "output_dir": "./scraped_data",
  "variables": {
    "base_url": "https://example.com",
    "max_pages": 100
  }
}
```

## Browser Configuration

Browser configuration options control how the browser behaves during automation.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| type | string | "chromium" | Browser type: "chromium", "firefox", or "webkit" |
| headless | boolean | true | Whether to run browser in headless mode |
| viewport | object | { "width": 1280, "height": 720 } | Browser viewport dimensions |
| user_agent | string | - | Custom user agent string |
| args | array | [] | Additional browser launch arguments |
| ignore_https_errors | boolean | false | Whether to ignore HTTPS certificate errors |
| slow_mo | integer | 0 | Slow down operations by specified milliseconds |

### Viewport Configuration

The viewport option accepts an object with width and height properties:

```json
{
  "browser": {
    "type": "chromium",
    "headless": true,
    "viewport": {
      "width": 1920,
      "height": 1080
    }
  }
}
```

### Browser Arguments

Common browser arguments include:

```json
{
  "browser": {
    "type": "chromium",
    "args": [
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--no-sandbox",
      "--disable-setuid-sandbox"
    ]
  }
}
```

## Action Configuration

Action configuration defines the sequence of actions to be performed during automation.

### Common Action Properties

| Property | Type | Description |
|----------|------|-------------|
| type | string | Type of action (e.g., "navigate", "click", "input_text") |
| selector | string | CSS selector for target element |
| timeout | integer | Action-specific timeout in milliseconds |
| retry_count | integer | Number of retries for this action |
| retry_delay | integer | Delay between retries in milliseconds |
| continue_on_error | boolean | Whether to continue execution if this action fails |

### Action Types

#### Navigate Action

Navigates to a specified URL.

```json
{
  "type": "navigate",
  "url": "https://example.com/login",
  "wait_until": "networkidle"
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| url | string | - | URL to navigate to |
| wait_until | string | "load" | When to consider navigation complete: "load", "domcontentloaded", or "networkidle" |
| timeout | integer | 30000 | Navigation timeout in milliseconds |

#### Click Action

Clicks on a specified element.

```json
{
  "type": "click",
  "selector": "#submit-button",
  "button": "left",
  "click_count": 1
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| selector | string | - | CSS selector for target element |
| button | string | "left" | Mouse button: "left", "right", or "middle" |
| click_count | integer | 1 | Number of clicks to perform |
| position | object | - | Relative position to click: { "x": 0.5, "y": 0.5 } for center |
| force | boolean | false | Whether to bypass actionability checks |

#### Input Text Action

Inputs text into a specified element.

```json
{
  "type": "input_text",
  "selector": "#username",
  "value": "user@example.com",
  "clear_first": true,
  "delay": 50
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| selector | string | - | CSS selector for target element |
| value | string | - | Text to input |
| clear_first | boolean | true | Whether to clear existing content first |
| delay | integer | 0 | Delay between key presses in milliseconds |

#### Wait Action

Waits for a specified condition or amount of time.

```json
{
  "type": "wait",
  "duration": 2000
}
```

Or for waiting for an element:

```json
{
  "type": "wait",
  "selector": "#success-message",
  "state": "visible",
  "timeout": 10000
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| duration | integer | - | Time to wait in milliseconds (if not waiting for element) |
| selector | string | - | CSS selector for element to wait for (if waiting for element) |
| state | string | "visible" | Element state to wait for: "visible", "hidden", "attached", or "detached" |
| timeout | integer | 30000 | Maximum time to wait in milliseconds |

#### Screenshot Action

Takes a screenshot of the current page or a specific element.

```json
{
  "type": "screenshot",
  "path": "login_page.png",
  "selector": "#login-form",
  "format": "png"
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| path | string | - | File path to save screenshot |
| selector | string | - | CSS selector for element to screenshot (optional) |
| format | string | "png" | Image format: "png" or "jpeg" |
| quality | integer | 80 | Image quality (for jpeg) |

#### Extract Text Action

Extracts text from a specified element.

```json
{
  "type": "extract_text",
  "selector": ".product-title",
  "variable": "product_title"
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| selector | string | - | CSS selector for target element |
| variable | string | - | Variable name to store extracted text |
| property | string | "textContent" | DOM property to extract: "textContent", "innerText", or "innerHTML" |

#### Extract Attribute Action

Extracts an attribute value from a specified element.

```json
{
  "type": "extract_attribute",
  "selector": ".product-link",
  "attribute": "href",
  "variable": "product_url"
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| selector | string | - | CSS selector for target element |
| attribute | string | - | Name of attribute to extract |
| variable | string | - | Variable name to store extracted attribute |

#### Conditional Action

Executes actions based on a condition.

```json
{
  "type": "if",
  "condition": {
    "type": "element_exists",
    "selector": ".error-message"
  },
  "then": [
    {
      "type": "extract_text",
      "selector": ".error-message",
      "variable": "error_text"
    }
  ],
  "else": [
    {
      "type": "click",
      "selector": "#continue-button"
    }
  ]
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| condition | object | - | Condition to evaluate |
| then | array | - | Actions to execute if condition is true |
| else | array | - | Actions to execute if condition is false |

#### Loop Action

Repeats a sequence of actions.

```json
{
  "type": "loop",
  "count": 5,
  "actions": [
    {
      "type": "click",
      "selector": ".next-page"
    },
    {
      "type": "extract_text",
      "selector": ".page-number",
      "variable": "current_page"
    }
  ]
}
```

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| count | integer | - | Number of times to repeat the actions |
| actions | array | - | Actions to repeat |
| while | object | - | Condition to continue looping (alternative to count) |

## Logging Configuration

Logging configuration options control how logs are generated and stored.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| level | string | "info" | Log level: "error", "warn", "info", "debug", or "trace" |
| file | string | - | Path to log file (if not specified, logs to console) |
| format | string | "simple" | Log format: "simple", "json", or "pretty" |
| max_size | string | "10MB" | Maximum log file size before rotation |
| backup_count | integer | 5 | Number of backup log files to keep |

### Example

```json
{
  "logging": {
    "level": "debug",
    "file": "./logs/automation.log",
    "format": "json",
    "max_size": "20MB",
    "backup_count": 10
  }
}
```

## Security Configuration

Security configuration options control security-related aspects of automation.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| validate_ssl | boolean | true | Whether to validate SSL certificates |
| strict_content_security_policy | boolean | true | Whether to enforce strict CSP |
| disable_web_security | boolean | false | Whether to disable web security features |
| ignore_https_errors | boolean | false | Whether to ignore HTTPS certificate errors |

### Example

```json
{
  "security": {
    "validate_ssl": true,
    "strict_content_security_policy": true,
    "disable_web_security": false,
    "ignore_https_errors": false
  }
}
```

## Performance Configuration

Performance configuration options control performance-related aspects of automation.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| resource_limits | object | {} | Resource limits for browser |
| optimization | object | {} | Optimization settings |
| cache | object | {} | Cache configuration |

### Resource Limits

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| memory_mb | integer | 2048 | Maximum memory usage in MB |
| cpu_percent | integer | 80 | Maximum CPU usage percentage |
| timeout_ms | integer | 300000 | Maximum execution time in MS |

### Example

```json
{
  "performance": {
    "resource_limits": {
      "memory_mb": 4096,
      "cpu_percent": 90,
      "timeout_ms": 600000
    },
    "optimization": {
      "disable_images": true,
      "disable_css": false,
      "disable_javascript": false
    },
    "cache": {
      "enabled": true,
      "ttl": 3600,
      "max_size": "100MB"
    }
  }
}
```

## Environment Variables

Environment variables can be used to override configuration values.

| Variable | Description |
|----------|-------------|
| AUTOMATON_NAME | Name of the automation workflow |
| AUTOMATON_URL | Starting URL for the automation |
| AUTOMATON_BROWSER_TYPE | Browser type: "chromium", "firefox", or "webkit" |
| AUTOMATON_BROWSER_HEADLESS | Whether to run browser in headless mode: "true" or "false" |
| AUTOMATON_LOG_LEVEL | Log level: "error", "warn", "info", "debug", or "trace" |
| AUTOMATON_OUTPUT_DIR | Directory for output files |
| AUTOMATON_TIMEOUT | Global timeout in milliseconds |
| AUTOMATON_RETRY_COUNT | Number of times to retry failed actions |
| AUTOMATON_RETRY_DELAY | Delay between retries in milliseconds |

### Example

```bash
export AUTOMATON_BROWSER_TYPE=chromium
export AUTOMATON_BROWSER_HEADLESS=true
export AUTOMATON_LOG_LEVEL=debug
export AUTOMATON_OUTPUT_DIR=./output
```

## Configuration Examples

### Basic Web Scraping

```json
{
  "name": "Product Scraping",
  "description": "Scrape product information from e-commerce site",
  "url": "https://example.com/products",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": [
    {
      "type": "wait",
      "selector": ".product-list",
      "state": "visible"
    },
    {
      "type": "loop",
      "count": 10,
      "actions": [
        {
          "type": "extract_text",
          "selector": ".product-title",
          "variable": "title"
        },
        {
          "type": "extract_text",
          "selector": ".product-price",
          "variable": "price"
        },
        {
          "type": "click",
          "selector": ".next-page"
        }
      ]
    }
  ]
}
```

### Form Filling with Conditional Logic

```json
{
  "name": "Form Submission",
  "description": "Fill and submit a form with validation",
  "url": "https://example.com/contact",
  "browser": {
    "type": "chromium",
    "headless": false
  },
  "variables": {
    "email": "user@example.com",
    "message": "Hello, I need help with your product."
  },
  "actions": [
    {
      "type": "input_text",
      "selector": "#email",
      "value": "${email}"
    },
    {
      "type": "input_text",
      "selector": "#message",
      "value": "${message}"
    },
    {
      "type": "click",
      "selector": "#submit"
    },
    {
      "type": "wait",
      "duration": 2000
    },
    {
      "type": "if",
      "condition": {
        "type": "element_exists",
        "selector": ".error-message"
      },
      "then": [
        {
          "type": "extract_text",
          "selector": ".error-message",
          "variable": "error"
        },
        {
          "type": "screenshot",
          "path": "form_error.png"
        }
      ],
      "else": [
        {
          "type": "screenshot",
          "path": "form_success.png"
        }
      ]
    }
  ]
}
```

### Performance-Optimized Configuration

```json
{
  "name": "High-Performance Scraping",
  "description": "Optimized configuration for large-scale scraping",
  "url": "https://example.com/data",
  "browser": {
    "type": "chromium",
    "headless": true,
    "args": [
      "--disable-gpu",
      "--disable-dev-shm-usage",
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-extensions",
      "--disable-images",
      "--disable-javascript-har-promises"
    ]
  },
  "performance": {
    "resource_limits": {
      "memory_mb": 8192,
      "cpu_percent": 95,
      "timeout_ms": 1800000
    },
    "optimization": {
      "disable_images": true,
      "disable_css": false,
      "disable_javascript": false,
      "network_idle_timeout": 5000
    },
    "cache": {
      "enabled": true,
      "ttl": 7200,
      "max_size": "500MB"
    }
  },
  "logging": {
    "level": "warn",
    "file": "./logs/scraping.log",
    "format": "json"
  },
  "actions": [
    {
      "type": "wait",
      "selector": ".data-container",
      "state": "visible",
      "timeout": 10000
    },
    {
      "type": "extract_text",
      "selector": ".data-item",
      "variable": "data"
    }
  ]
}
```

## Next Steps

1. Explore the [Action Types Reference](ACTION_TYPES_REFERENCE.md) for detailed information on all available actions
2. Check the [Advanced Usage](7_advanced_usage.md) guide for complex configuration patterns
3. Refer to the [Troubleshooting Guide](8_troubleshooting_guide.md) for common configuration issues

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](README.md).*