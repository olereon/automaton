# Automaton Troubleshooting Guide

## Introduction

This guide helps you diagnose and resolve common issues when using Automaton. It covers installation problems, runtime errors, performance issues, and debugging techniques.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Problems](#configuration-problems)
3. [Runtime Errors](#runtime-errors)
4. [Browser Compatibility Issues](#browser-compatibility-issues)
5. [Performance Problems](#performance-problems)
6. [Debugging Techniques](#debugging-techniques)
7. [Logging and Diagnostics](#logging-and-diagnostics)
8. [Common Error Messages](#common-error-messages)
9. [Frequently Asked Questions](#frequently-asked-questions)

## Installation Issues

### Python Version Compatibility

**Problem**: Installation fails with Python version errors.

```
ERROR: This package requires Python 3.11 or higher.
```

**Solution**:
1. Check your Python version:
   ```bash
   python --version
   ```
2. If you have multiple Python versions, use the correct one:
   ```bash
   python3.11 --version
   ```
3. Install using the correct Python version:
   ```bash
   python3.11 -m pip install automaton
   ```

### Missing Dependencies

**Problem**: Installation fails with missing dependencies.

```
ERROR: Could not find a version that satisfies the requirement playwright>=1.20.0
```

**Solution**:
1. Update pip to the latest version:
   ```bash
   pip install --upgrade pip
   ```
2. Install dependencies manually:
   ```bash
   pip install playwright>=1.20.0
   ```
3. Try installing Automaton again:
   ```bash
   pip install automaton
   ```

### Playwright Browser Installation

**Problem**: Browser-related errors when running Automaton.

```
Error: Executable doesn't exist at /path/to/playwright/browsers
```

**Solution**:
1. Install Playwright browsers:
   ```bash
   python -m playwright install
   ```
2. If you need specific browsers:
   ```bash
   python -m playwright install chromium
   python -m playwright install firefox
   python -m playwright install webkit
   ```

### Permission Issues

**Problem**: Installation fails with permission errors.

```
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Solution**:
1. Use a virtual environment:
   ```bash
   python -m venv automaton-env
   source automaton-env/bin/activate  # On Windows: automaton-env\Scripts\activate
   pip install automaton
   ```
2. Or use the `--user` flag:
   ```bash
   pip install --user automaton
   ```

## Configuration Problems

### Invalid JSON Configuration

**Problem**: Automaton fails to start with JSON parsing errors.

```
Error: Failed to parse configuration file: Expecting property name enclosed in double quotes
```

**Solution**:
1. Validate your JSON using a JSON linter or online validator.
2. Check for common JSON syntax errors:
   - Missing commas between objects
   - Trailing commas
   - Single quotes instead of double quotes
   - Unescaped special characters
3. Use a JSON schema validator if available.

### Missing Required Configuration Fields

**Problem**: Automaton reports missing required configuration fields.

```
Error: Missing required configuration field: 'url'
```

**Solution**:
1. Ensure your configuration includes all required fields:
   ```json
   {
     "name": "My Automation",
     "url": "https://example.com",
     "actions": []
   }
   ```
2. Refer to the [Configuration Guide](2_installation_setup.md) for a complete list of required fields.

### Invalid Action Configuration

**Problem**: Actions fail to execute with configuration errors.

```
Error: Invalid action configuration: 'selector' is required for 'click_button' action
```

**Solution**:
1. Check the [API Reference](5_api_reference.md) for required parameters for each action.
2. Ensure all required parameters are provided:
   ```json
   {
     "type": "click_button",
     "selector": "#submit-button"
   }
   ```
3. Validate parameter types match expected values.

### Environment Variable Substitution

**Problem**: Environment variables are not being substituted correctly.

```
Error: Environment variable 'API_TOKEN' not found
```

**Solution**:
1. Ensure environment variables are set before running Automaton:
   ```bash
   export API_TOKEN=your_token_here
   automaton run config.json
   ```
2. Verify variable names match exactly (case-sensitive).
3. Use default values in configuration:
   ```json
   {
     "type": "input_text",
     "selector": "#api-key",
     "value": "${API_TOKEN || default_token}"
   }
   ```

## Runtime Errors

### Element Not Found

**Problem**: Actions fail with element not found errors.

```
Error: Element not found: #non-existent-element
```

**Solution**:
1. Verify the selector is correct:
   - Use browser developer tools to test selectors
   - Check for typos in selector names
   - Ensure the element exists on the page
2. Add explicit waits:
   ```json
   {
     "type": "wait_for_element",
     "selector": "#dynamic-element",
     "timeout": 10000
   },
   {
     "type": "click_button",
     "selector": "#dynamic-element"
   }
   ```
3. Use more robust selectors:
   ```json
   {
     "type": "click_button",
     "selector": "button[type='submit']"
   }
   ```

### Timeout Errors

**Problem**: Actions fail with timeout errors.

```
Error: Timeout 30000ms exceeded while waiting for element to be visible
```

**Solution**:
1. Increase timeout values:
   ```json
   {
     "type": "wait_for_element",
     "selector": "#slow-loading-element",
     "timeout": 60000
   }
   ```
2. Use conditional waits with backoff:
   ```json
   {
     "type": "conditional_wait",
     "selector": "#dynamic-content",
     "timeout": 60000,
     "interval": 2000,
     "backoff": 1.5
   }
   ```
3. Check for network issues or slow page loads.

### Authentication Failures

**Problem**: Login actions fail with authentication errors.

```
Error: Authentication failed: Invalid credentials
```

**Solution**:
1. Verify credentials are correct:
   - Test login manually in a browser
   - Check for username/password typos
2. Ensure proper login sequence:
   ```json
   {
     "type": "input_text",
     "selector": "#username",
     "value": "${username}"
   },
   {
     "type": "input_text",
     "selector": "#password",
     "value": "${password}"
   },
   {
     "type": "click_button",
     "selector": "#login-button"
   },
   {
     "type": "wait_for_element",
     "selector": ".user-dashboard"
   }
   ```
3. Handle CAPTCHAs or multi-factor authentication if present.

### Network Errors

**Problem**: Actions fail with network-related errors.

```
Error: net::ERR_CONNECTION_TIMED_OUT
```

**Solution**:
1. Check network connectivity:
   - Verify internet connection is stable
   - Check if target website is accessible
2. Increase network timeouts:
   ```json
   {
     "name": "Network Timeout Example",
     "url": "https://example.com",
     "browser": {
       "timeout": 60000
     },
     "actions": []
   }
   ```
3. Add retry logic for network operations:
   ```json
   {
     "type": "set_variable",
     "value": {
       "name": "retry_count",
       "value": 0
     }
   },
   {
     "type": "while_begin",
     "condition": "retry_count",
     "operator": "<",
     "value": 3
   },
   {
     "type": "try_begin"
   },
   {
     "type": "navigate_to",
     "value": "https://example.com"
   },
   {
     "type": "catch_begin"
   },
   {
     "type": "increment_variable",
     "value": {
       "name": "retry_count",
       "increment": 1
     }
   },
   {
     "type": "wait",
     "value": 2000
   },
   {
     "type": "continue"
   },
   {
     "type": "catch_end"
   },
   {
     "type": "while_end"
   }
   ```

## Browser Compatibility Issues

### Browser-Specific Behavior

**Problem**: Automation works in one browser but fails in another.

**Solution**:
1. Test with different browser configurations:
   ```json
   {
     "name": "Browser Test",
     "browser": {
       "type": "chromium"  # or "firefox" or "webkit"
     },
     "actions": []
   }
   ```
2. Add browser-specific selectors or waits:
   ```json
   {
     "type": "if_begin",
     "condition": "browser_type",
     "operator": "==",
     "value": "firefox"
   },
   {
     "type": "click_button",
     "selector": ".firefox-specific-button"
   },
   {
     "type": "else"
   },
   {
     "type": "click_button",
     "selector": ".chrome-specific-button"
   },
   {
     "type": "if_end"
   }
   ```
3. Use universal selectors that work across browsers.

### Headless Mode Issues

**Problem**: Automation works in headed mode but fails in headless mode.

**Solution**:
1. Test with headless mode explicitly:
   ```json
   {
     "name": "Headless Test",
     "browser": {
       "headless": true
     },
     "actions": []
   }
   ```
2. Add explicit waits and checks for headless mode:
   ```json
   {
     "type": "wait",
     "value": 2000
   },
   {
     "type": "check_element",
     "selector": ".content",
     "operator": "visible"
   }
   ```
3. Handle differences in viewport size:
   ```json
   {
     "name": "Viewport Test",
     "browser": {
       "viewport": {
         "width": 1920,
         "height": 1080
       }
     },
     "actions": []
   }
   ```

## Performance Problems

### Slow Execution

**Problem**: Automation runs much slower than expected.

**Solution**:
1. Optimize wait times:
   - Replace fixed waits with conditional waits
   - Reduce timeout values where possible
2. Disable unnecessary browser features:
   ```json
   {
     "name": "Performance Test",
     "browser": {
       "args": [
         "--disable-gpu",
         "--disable-dev-shm-usage",
         "--no-sandbox"
       ]
     },
     "actions": []
   }
   ```
3. Use parallel execution for independent actions:
   ```json
   {
     "type": "parallel_execute",
     "value": {
       "actions": [
         {
           "type": "click_button",
           "selector": "#button1"
         },
         {
           "type": "click_button",
           "selector": "#button2"
         }
       ]
     }
   }
   ```

### High Memory Usage

**Problem**: Automation consumes excessive memory.

**Solution**:
1. Clear browser data periodically:
   ```json
   {
     "type": "clear_browser_data",
     "value": {
       "cookies": true,
       "cache": true
     }
   }
   ```
2. Restart browser periodically:
   ```json
   {
     "type": "restart_browser"
   }
   ```
3. Optimize data extraction to process in batches:
   ```json
   {
     "type": "set_variable",
     "value": {
       "name": "batch_size",
       "value": 100
     }
   },
   {
     "type": "process_data_in_batches",
     "value": {
       "batch_size": "${batch_size}"
     }
   }
   ```

## Debugging Techniques

### Enabling Debug Mode

**Solution**: Enable debug mode for detailed logging:

```json
{
  "name": "Debug Example",
  "debug": {
    "enabled": true,
    "screenshots_on_error": true,
    "verbose_logging": true,
    "slow_motion": 1000
  },
  "actions": []
}
```

### Taking Screenshots

**Solution**: Add screenshot actions to debug visual state:

```json
{
  "type": "screenshot",
  "value": "before_click.png"
},
{
  "type": "click_button",
  "selector": "#submit-button"
},
{
  "type": "screenshot",
  "value": "after_click.png"
}
```

### Adding Logging

**Solution**: Add log messages to track execution:

```json
{
  "type": "log_message",
  "value": "Starting login process"
},
{
  "type": "input_text",
  "selector": "#username",
  "value": "${username}"
},
{
  "type": "log_message",
  "value": "Username entered"
}
```

### Step-by-Step Execution

**Solution**: Use pause actions to debug step-by-step:

```json
{
  "type": "log_message",
  "value": "About to click submit button"
},
{
  "type": "pause",
  "value": "Press Enter to continue..."
},
{
  "type": "click_button",
  "selector": "#submit-button"
}
```

## Logging and Diagnostics

### Log Levels

**Solution**: Configure appropriate log levels:

```json
{
  "name": "Logging Example",
  "logging": {
    "level": "debug",  // "error", "warn", "info", "debug"
    "file": "automation.log",
    "console": true
  },
  "actions": []
}
```

### Performance Metrics

**Solution**: Enable performance metrics:

```json
{
  "name": "Performance Metrics",
  "metrics": {
    "enabled": true,
    "interval": 1000
  },
  "actions": []
}
```

### Execution Traces

**Solution**: Enable execution traces:

```json
{
  "name": "Execution Trace",
  "trace": {
    "enabled": true,
    "screenshots": true,
    "network": true
  },
  "actions": []
}
```

## Common Error Messages

### "Action execution failed: Timeout exceeded"

**Cause**: Action took longer than the allowed timeout.

**Solution**:
1. Increase timeout for the specific action:
   ```json
   {
     "type": "wait_for_element",
     "selector": "#slow-element",
     "timeout": 60000
   }
   ```
2. Optimize the action to be more efficient.
3. Check for network or performance issues.

### "Element not found: [selector]"

**Cause**: The specified element could not be found on the page.

**Solution**:
1. Verify the selector is correct using browser developer tools.
2. Add explicit waits for dynamic content:
   ```json
   {
     "type": "wait_for_element",
     "selector": "#dynamic-element"
   }
   ```
3. Use more robust selectors that are less likely to change.

### "Variable '[name]' not found"

**Cause**: Referenced variable has not been defined.

**Solution**:
1. Ensure the variable is defined before use:
   ```json
   {
     "type": "set_variable",
     "value": {
       "name": "username",
       "value": "test_user"
     }
   },
   {
     "type": "input_text",
     "selector": "#username-field",
     "value": "${username}"
   }
   ```
2. Check for typos in variable names.
3. Use default values for optional variables:
   ```json
   {
     "type": "input_text",
     "selector": "#username-field",
     "value": "${username || default_user}"
   }
   ```

### "Invalid action type: [type]"

**Cause**: Specified action type is not recognized.

**Solution**:
1. Check the [API Reference](5_api_reference.md) for valid action types.
2. Verify the action type name is spelled correctly.
3. Ensure any custom action types are properly registered.

## Frequently Asked Questions

### How do I handle CAPTCHAs?

Automaton cannot solve CAPTCHAs automatically. Consider these approaches:
1. Use test environments with CAPTCHAs disabled.
2. Use manual intervention for CAPTCHA steps:
   ```json
   {
     "type": "log_message",
     "value": "Please solve the CAPTCHA manually"
   },
   {
     "type": "pause",
     "value": "Press Enter after solving CAPTCHA"
   }
   ```
3. Use third-party CAPTCHA solving services with custom actions.

### How do I handle file downloads?

Use the download_file action:

```json
{
  "type": "click_button",
  "selector": "#download-button"
},
{
  "type": "wait_for_download",
  "value": {
    "timeout": 30000,
    "save_path": "./downloads/"
  }
}
```

### How do I handle iframes?

Switch to iframe context before interacting with elements:

```json
{
  "type": "switch_to_frame",
  "selector": "#iframe-id"
},
{
  "type": "click_button",
  "selector": "#button-inside-iframe"
},
{
  "type": "switch_to_parent_frame"
}
```

### How do I handle pop-up windows?

Use window management actions:

```json
{
  "type": "click_button",
  "selector": "#open-popup"
},
{
  "type": "wait_for_window",
  "value": {
    "timeout": 10000
  }
},
{
  "type": "switch_to_window",
  "value": {
    "index": 1  # 0 is the main window
  }
},
{
  "type": "click_button",
  "selector": "#popup-button"
},
{
  "type": "close_window"
},
{
  "type": "switch_to_window",
  "value": {
    "index": 0
  }
}
```

### How do I run Automaton in a CI/CD pipeline?

1. Use headless mode:
   ```json
   {
     "name": "CI/CD Automation",
     "browser": {
       "headless": true
     },
     "actions": []
   }
   ```
2. Install dependencies in your CI script:
   ```yaml
   # Example GitHub Actions
   - name: Set up Python
     uses: actions/setup-python@v2
     with:
       python-version: 3.11
   - name: Install dependencies
     run: |
       pip install automaton
       python -m playwright install --with-deps chromium
   - name: Run automation
     run: automaton run automation-config.json
   ```
3. Handle authentication securely using environment variables or secrets.

## Next Steps

After resolving your issue, you may want to:

1. [Explore Contributing Guidelines](9_contributing_guide.md) to help improve Automaton
2. [Review Deployment Options](10_deployment_guide.md) for production environments
3. [Learn Advanced Usage](7_advanced_usage.md) for more complex scenarios

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*