# Automaton User Guide

## Introduction

This guide provides practical instructions for using Automaton to create and run web automation sequences. Whether you prefer the graphical interface or command-line tools, this guide will help you get started quickly.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Using the GUI Interface](#using-the-gui-interface)
3. [Using the CLI Interface](#using-the-cli-interface)
4. [Creating Your First Automation](#creating-your-first-automation)
5. [Common Automation Patterns](#common-automation-patterns)
6. [Saving and Managing Automations](#saving-and-managing-automations)
7. [Running Automations](#running-automations)
8. [Monitoring Execution](#monitoring-execution)

## Getting Started

Before using Automaton, ensure you have completed the [installation steps](2_installation_setup.md). Once installed, you can choose between the GUI or CLI interface based on your preferences.

### Choosing an Interface

| Interface | Best For | Experience Level |
|-----------|----------|------------------|
| GUI | Visual learners, simple automations, testing | Beginner |
| CLI | Advanced users, scripting, CI/CD | Intermediate/Advanced |
| API | Integration with other applications | Advanced |

## Using the GUI Interface

The GUI provides a user-friendly way to create and test automations without writing code.

### Launching the GUI

```bash
python3.11 automaton-gui.py
```

### GUI Components

The GUI consists of these main sections:

1. **Configuration Panel**: Set automation name and URL
2. **Actions List**: View and manage automation steps
3. **Action Editor**: Configure individual actions
4. **Control Buttons**: Run, stop, save, and load automations

### Creating an Automation with the GUI

1. **Enter Basic Information**:
   - Name your automation in the "Automation Name" field
   - Enter the starting URL in the "Target URL" field

2. **Add Actions**:
   - Click "Add Action" to open the action editor
   - Select an action type from the dropdown
   - Configure the action parameters (selector, value, etc.)
   - Click "Add" to include the action in your sequence

3. **Test Your Automation**:
   - Click "Run Automation" to execute the sequence
   - Monitor the progress in the status area
   - Use "Stop" to terminate if needed

4. **Save Your Work**:
   - Click "Save Configuration" to store your automation
   - Choose a location and filename for your configuration

### Common GUI Actions

| Task | Steps |
|------|-------|
| Add a wait action | Click "Add Action" → Select "WAIT" → Enter duration (ms) |
| Fill a form field | Click "Add Action" → Select "INPUT_TEXT" → Enter CSS selector and text |
| Click a button | Click "Add Action" → Select "CLICK_BUTTON" → Enter CSS selector |
| Save automation | Click "Save Configuration" → Choose location and filename |
| Load automation | Click "Load Configuration" → Select saved configuration file |

## Using the CLI Interface

The CLI provides powerful command-line tools for creating, managing, and running automations.

### Basic CLI Commands

#### Listing Available Actions

```bash
python3.11 automaton-cli.py list-actions
```

This displays all available action types with brief descriptions.

#### Creating a New Automation

```bash
python3.11 automaton-cli.py create -n "My Automation" -u "https://example.com" -o my_automation.json
```

Parameters:
- `-n` or `--name`: Name of the automation
- `-u` or `--url`: Starting URL
- `-o` or `--output`: Output file path

#### Running an Automation

```bash
# Run in headless mode (default)
python3.11 automaton-cli.py run -c my_automation.json

# Run with visible browser
python3.11 automaton-cli.py run -c my_automation.json --show-browser

# Continue on errors
python3.11 automaton-cli.py run -c my_automation.json --continue-on-error
```

Parameters:
- `-c` or `--config`: Path to configuration file
- `--show-browser`: Run with visible browser window
- `--continue-on-error`: Continue execution even if errors occur
- `--timeout`: Global timeout in milliseconds (default: 30000)

### Advanced CLI Usage

#### Editing Automations

While you can edit JSON files manually, the CLI provides a validation tool:

```bash
python3.11 automaton-cli.py validate -c my_automation.json
```

This checks your configuration for syntax errors and common issues.

#### Converting Between Formats

```bash
# Convert JSON to YAML
python3.11 automaton-cli.py convert -i my_automation.json -o my_automation.yaml --format yaml

# Convert YAML to JSON
python3.11 automaton-cli.py convert -i my_automation.yaml -o my_automation.json --format json
```

## Creating Your First Automation

Let's create a simple automation that fills out a contact form.

### Step 1: Create the Configuration

Using the CLI:

```bash
python3.11 automaton-cli.py create -n "Contact Form" -u "https://example.com/contact" -o contact_form.json
```

### Step 2: Add Actions

Edit the `contact_form.json` file to add the following actions:

```json
{
  "name": "Contact Form",
  "url": "https://example.com/contact",
  "actions": [
    {
      "type": "wait_for_element",
      "selector": "#contact-form"
    },
    {
      "type": "input_text",
      "selector": "#name",
      "value": "John Doe"
    },
    {
      "type": "input_text",
      "selector": "#email",
      "value": "john@example.com"
    },
    {
      "type": "input_text",
      "selector": "#message",
      "value": "I would like to learn more about your services."
    },
    {
      "type": "click_button",
      "selector": "#submit-button"
    },
    {
      "type": "wait_for_element",
      "selector": ".success-message"
    }
  ]
}
```

### Step 3: Run the Automation

```bash
python3.11 automaton-cli.py run -c contact_form.json --show-browser
```

### Step 4: Verify Results

Check that:
1. The browser navigates to the contact form
2. All fields are filled correctly
3. The form is submitted
4. The success message appears

## Common Automation Patterns

### Form Submission

```json
{
  "actions": [
    {
      "type": "wait_for_element",
      "selector": "#form-container"
    },
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
    }
  ]
}
```

### Navigation and Content Extraction

```json
{
  "actions": [
    {
      "type": "click_button",
      "selector": "#products-link"
    },
    {
      "type": "wait_for_element",
      "selector": ".product-list"
    },
    {
      "type": "check_element",
      "selector": ".product-item",
      "operator": "exists"
    },
    {
      "type": "log_message",
      "value": "Products loaded successfully"
    }
  ]
}
```

### Conditional Execution

```json
{
  "actions": [
    {
      "type": "check_element",
      "selector": ".popup",
      "operator": "exists"
    },
    {
      "type": "if_begin",
      "condition": "check_result == true"
    },
    {
      "type": "click_button",
      "selector": ".close-popup"
    },
    {
      "type": "else"
    },
    {
      "type": "log_message",
      "value": "No popup to close"
    },
    {
      "type": "if_end"
    }
  ]
}
```

### File Downloads

```json
{
  "actions": [
    {
      "type": "click_button",
      "selector": "#download-report"
    },
    {
      "type": "wait",
      "value": 2000
    },
    {
      "type": "download_file",
      "selector": "#download-link",
      "value": {
        "download_dir": "./downloads",
        "filename": "report.pdf"
      }
    }
  ]
}
```

## Saving and Managing Automations

### Organization Tips

1. **Use Descriptive Names**: Name files based on their purpose (e.g., `login_automation.json`)
2. **Group Related Automations**: Store related automations in the same directory
3. **Use Version Control**: Track changes to your automations with Git
4. **Document Complex Logic**: Add comments to explain complex sequences

### Directory Structure Example

```
automations/
├── login/
│   ├── standard_login.json
│   ├── oauth_login.json
│   └── README.md
├── data_extraction/
│   ├── product_scraping.json
│   ├── price_monitoring.json
│   └── README.md
└── forms/
    ├── contact_form.json
    ├── registration_form.json
    └── README.md
```

### Configuration Templates

Create templates for common automation patterns:

```json
{
  "_template": "form_submission",
  "_description": "Template for filling and submitting forms",
  "name": "Form Template",
  "url": "https://example.com/form",
  "actions": [
    {
      "type": "wait_for_element",
      "selector": "#form-container"
    },
    {
      "type": "input_text",
      "selector": "#field1",
      "value": "${value1}"
    },
    {
      "type": "input_text",
      "selector": "#field2",
      "value": "${value2}"
    },
    {
      "type": "click_button",
      "selector": "#submit-button"
    }
  ]
}
```

## Running Automations

### Execution Modes

| Mode | Description | Use Case |
|------|-------------|---------|
| Headless | Browser runs invisibly | Production environments |
| Headed | Browser window visible | Development, debugging |
| Debug | Enhanced logging and browser persistence | Troubleshooting |

### Running Multiple Automations

Create a shell script to run multiple automations in sequence:

```bash
#!/bin/bash
# run_all_automations.sh

echo "Running login automation..."
python3.11 automaton-cli.py run -c login.json

echo "Running data extraction..."
python3.11 automaton-cli.py run -c data_extraction.json

echo "Running report generation..."
python3.11 automaton-cli.py run -c report_generation.json

echo "All automations completed!"
```

### Scheduling Automations

Use cron (Linux/macOS) or Task Scheduler (Windows) to schedule automations:

```bash
# Run every day at 9 AM
0 9 * * * /usr/bin/python3.11 /path/to/automaton-cli.py run -c daily_report.json
```

## Monitoring Execution

### Understanding Output

When running an automation, you'll see output like:

```
2023-08-24 14:35:22 - INFO - Starting automation: Contact Form
2023-08-24 14:35:23 - INFO - Navigating to: https://example.com/contact
2023-08-24 14:35:25 - INFO - Executing: wait_for_element #contact-form
2023-08-24 14:35:26 - INFO - Executing: input_text #name
2023-08-24 14:35:27 - INFO - Executing: input_text #email
2023-08-24 14:35:28 - INFO - Executing: input_text #message
2023-08-24 14:35:29 - INFO - Executing: click_button #submit-button
2023-08-24 14:35:31 - INFO - Executing: wait_for_element .success-message
2023-08-24 14:35:32 - INFO - Automation completed successfully
```

### Log Levels

Control verbosity with the `AUTOMATON_LOG_LEVEL` environment variable:

```bash
export AUTOMATON_LOG_LEVEL=DEBUG  # Most verbose
export AUTOMATON_LOG_LEVEL=INFO   # Default
export AUTOMATON_LOG_LEVEL=WARNING # Less verbose
export AUTOMATON_LOG_LEVEL=ERROR   # Least verbose
```

### Handling Failures

When an automation fails, check:

1. **Error Messages**: Look for specific error details in the output
2. **Selectors**: Verify CSS selectors are correct and elements exist
3. **Timing**: Increase wait times if elements load slowly
4. **Network**: Check internet connection and website availability

### Debug Mode

Run with debug mode for detailed troubleshooting:

```bash
python3.11 automaton-cli.py run -c automation.json --debug
```

This provides:
- Detailed step-by-step logging
- Screenshots on failures
- Browser state preservation
- Extended error information

## Next Steps

With these basics mastered, you can:

1. [Explore Advanced Usage](7_advanced_usage.md) for complex scenarios
2. [Review the API Reference](5_api_reference.md) for technical details
3. [Check Component Documentation](6_components_reference.md) for implementation specifics
4. [Learn Troubleshooting Techniques](8_troubleshooting_guide.md) for common issues

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*