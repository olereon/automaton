# Automaton Quick Start Guide

## Introduction

This guide provides a quick introduction to Automaton, helping you get up and running with basic automation workflows in minutes.

## Prerequisites

Before you begin, ensure you have the following:

- Python 3.11 or higher installed
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Safari, or Edge)

## Installation

### Install Automaton

```bash
pip install automaton
```

### Install Browser Dependencies

```bash
python -m playwright install --with-deps chromium
```

## Your First Automation

### Step 1: Create a Configuration File

Create a new file named `simple_automation.json`:

```json
{
  "name": "My First Automation",
  "browser": {
    "type": "chromium",
    "headless": false
  },
  "actions": [
    {
      "type": "navigate_to",
      "value": "https://example.com"
    },
    {
      "type": "wait_for_element",
      "selector": "h1"
    },
    {
      "type": "screenshot",
      "value": "example.png"
    }
  ]
}
```

### Step 2: Run the Automation

Execute your automation using the command line:

```bash
automaton run simple_automation.json
```

You should see a browser window open, navigate to example.com, and take a screenshot.

## Common Automation Tasks

### Filling and Submitting a Form

```json
{
  "name": "Form Submission",
  "actions": [
    {
      "type": "navigate_to",
      "value": "https://example.com/login"
    },
    {
      "type": "input_text",
      "selector": "#username",
      "value": "myusername"
    },
    {
      "type": "input_text",
      "selector": "#password",
      "value": "mypassword"
    },
    {
      "type": "click_button",
      "selector": "#login-button"
    },
    {
      "type": "wait_for_element",
      "selector": ".welcome-message"
    }
  ]
}
```

### Extracting Data from a Table

```json
{
  "name": "Data Extraction",
  "actions": [
    {
      "type": "navigate_to",
      "value": "https://example.com/data"
    },
    {
      "type": "extract_table",
      "selector": ".data-table",
      "value": {
        "variable": "table_data"
      }
    },
    {
      "type": "save_data",
      "value": {
        "data": "${table_data}",
        "filename": "extracted_data.json"
      }
    }
  ]
}
```

### Working with Variables

```json
{
  "name": "Variable Example",
  "actions": [
    {
      "type": "set_variable",
      "value": {
        "name": "search_term",
        "value": "automation"
      }
    },
    {
      "type": "navigate_to",
      "value": "https://example.com"
    },
    {
      "type": "input_text",
      "selector": "#search",
      "value": "${search_term}"
    },
    {
      "type": "click_button",
      "selector": "#search-button"
    }
  ]
}
```

## Running Automations in Different Modes

### Headless Mode (for production)

```json
{
  "name": "Headless Automation",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": [...]
}
```

### With Debug Information

```json
{
  "name": "Debug Automation",
  "debug": {
    "enabled": true,
    "screenshots_on_error": true,
    "verbose_logging": true
  },
  "actions": [...]
}
```

## Next Steps

Now that you've completed the quick start, you can:

1. Explore the [Core Concepts](3_core_concepts.md) to understand Automaton's architecture
2. Check the [User Guide](4_user_guide.md) for more detailed examples
3. Review the [API Reference](5_api_reference.md) for all available actions
4. Learn [Best Practices](11_best_practices.md) for building robust automations

## Troubleshooting

If you encounter issues:

- Ensure your Python version is 3.11 or higher
- Verify that browser dependencies are installed correctly
- Check that your JSON configuration is valid
- Enable debug mode for detailed error information

For more help, see the [Troubleshooting Guide](8_troubleshooting_guide.md).

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*