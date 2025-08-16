# Web Automation Tool

A lightweight and fast automation tool for executing repetitive web tasks with both GUI and CLI interfaces. Built with Python and Playwright for reliable browser automation.

## Features

- **Dual Interface**: Use either the modern GUI or powerful CLI
- **Modular Action System**: Support for various web interactions
- **Configuration Management**: Save and load automation sequences
- **Headless/Headed Mode**: Run with or without browser UI
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Async Execution**: Fast and efficient automation
- **Detailed Logging**: Track automation progress and debug issues

## Supported Actions

### Basic Actions
- **Input Text**: Fill text fields with dynamic content
- **Click Button**: Click any button or interactive element
- **Upload Image**: Upload files to web forms
- **Toggle Settings**: Check/uncheck checkboxes and switches
- **Wait**: Pause for specified duration
- **Wait for Element**: Wait for elements to appear
- **Refresh Page**: Reload the current page

### Advanced Actions
- **Check Element**: Validate element content with conditions (equals, less, greater)
- **Set Variable**: Store values for use in other actions
- **Increment Variable**: Increase numeric variables
- **Log Message**: Record automation progress and debugging info

### Flow Control
- **IF/ELIF/ELSE**: Conditional execution based on check results
- **WHILE Loops**: Repeat actions while conditions are met
- **BREAK/CONTINUE**: Control loop execution
- **Conditional Wait**: Retry actions with backoff strategies
- **Skip If**: Skip actions based on conditions

### Queue Management
- **Queue Detection**: Monitor task queues with multiple detection strategies
- **Queue Capacity Checking**: Ensure queue space before adding tasks
- **Automated Task Creation**: Create multiple tasks until capacity is reached

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd automaton
```

### 2. Create virtual environment (recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Playwright browsers
```bash
playwright install chromium
```

## Quick Start

### GUI Mode

Run the GUI application:
```bash
python automaton-gui.py
```

1. Enter automation name and target URL
2. Add actions using the "Add Action" button
3. Configure each action with selectors and values
4. Save configuration for reuse
5. Click "Run Automation" to execute

### CLI Mode

#### Create a new automation:
```bash
python automaton-cli.py create -n "My Task" -u "https://example.com" -o my_task.json --interactive
```

#### Run automation from config:
```bash
python automaton-cli.py run -c my_task.json
```

#### Run with browser visible:
```bash
python automaton-cli.py run -c my_task.json --show-browser
```

## Usage Examples

### Example 1: Form Submission Automation

```python
from web_automation import AutomationSequenceBuilder

# Build automation sequence
builder = AutomationSequenceBuilder("Form Submission", "https://example.com/form")

sequence = (builder
    .add_wait_for_element("#form-container")
    .add_input_text("#name-field", "John Doe")
    .add_input_text("#email-field", "john@example.com")
    .add_toggle_setting("#newsletter-checkbox", True)
    .add_click_button("#submit-button")
    .add_wait_for_element(".success-message")
    .build()
)

# Save for reuse
builder.save_to_file("form_automation.json")
```

### Example 2: Queue Management with While Loop

```python
# Automated queue management - create tasks until queue is full
sequence = (builder
    .add_set_variable("max_tasks", "8")
    .add_set_variable("task_count", "0")
    
    # Navigate to queue view
    .add_click_button("[data-test-id='sidebar-menuitem-button-Favorites']")
    .add_wait(2000)
    
    # Check initial queue status
    .add_check_element(
        selector=".sc-dMmcxd.cZTIpi",
        check_type="less",
        expected_value="${max_tasks}",
        attribute="text"
    )
    
    # WHILE loop - continue until queue is full
    .add_while_begin("check_passed")
    
    # Create new task
    .add_click_button(".creation-button")
    .add_upload_image("#file-input", "/path/to/image.jpg")
    .add_input_text("#prompt-field", "Create amazing content")
    .add_click_button("#submit-button")
    .add_increment_variable("task_count", 1)
    
    # Check queue status again
    .add_click_button("[data-test-id='sidebar-menuitem-button-Favorites']")
    .add_wait(2000)
    .add_check_element(
        selector=".sc-dMmcxd.cZTIpi",
        check_type="less",
        expected_value="${max_tasks}",
        attribute="text"
    )
    
    # Exit if queue is full
    .add_if_begin("check_failed")
    .add_log_message("Queue is full - stopping automation", "logs/automation.log")
    .add_break()
    .add_if_end()
    
    .add_while_end()
    .build()
)
```

## Configuration File Format

Automation configurations are stored as JSON files:

```json
{
  "name": "My Automation",
  "url": "https://example.com",
  "headless": true,
  "viewport": {
    "width": 1280,
    "height": 720
  },
  "actions": [
    {
      "type": "wait_for_element",
      "selector": "#main-content",
      "timeout": 30000,
      "description": "Wait for page load"
    },
    {
      "type": "input_text",
      "selector": "#search-box",
      "value": "automation",
      "description": "Enter search term"
    },
    {
      "type": "click_button",
      "selector": "#search-button",
      "description": "Click search"
    },
    {
      "type": "check_element",
      "selector": ".queue-counter",
      "value": {
        "check": "less",
        "value": "8",
        "attribute": "text"
      },
      "description": "Check if queue has space"
    },
    {
      "type": "while_begin",
      "value": {
        "condition": "check_passed"
      },
      "description": "Loop while queue has space"
    },
    {
      "type": "log_message",
      "value": {
        "message": "Creating task - queue has space",
        "log_file": "logs/automation.log"
      },
      "description": "Log task creation"
    },
    {
      "type": "while_end",
      "value": {},
      "description": "End while loop"
    }
  ]
}
```

## CLI Commands Reference

### `run` - Execute automation
```bash
automation run -c config.json [options]

Options:
  -c, --config          Path to config file (required)
  --show-browser        Show browser window
  --continue-on-error   Don't stop on action failure
```

### `create` - Create new automation
```bash
automation create -n NAME -u URL [options]

Options:
  -n, --name         Automation name (required)
  -u, --url          Target URL (required)
  -o, --output       Output file path
  --interactive      Add actions interactively
```

### `add-action` - Add action to config
```bash
automation add-action -c CONFIG --type TYPE [options]

Options:
  -c, --config       Config file to modify (required)
  --type            Action type (required)
  --selector        CSS selector
  --value           Action value
  --description     Action description
  --timeout         Timeout in ms (default: 30000)
```

### `list-actions` - Show available actions
```bash
automation list-actions
```

### `validate` - Validate configuration
```bash
automation validate -c config.json
```

### `convert` - Convert between formats
```bash
automation convert -i input.json -o output.yaml
```

## Advanced Usage

### Complex Automation with Flow Control

Create sophisticated workflows with conditional logic and loops:

```python
# Advanced automation with queue management and error handling
sequence = (builder
    # Login flow
    .add_input_text("#username", "user@example.com")
    .add_input_text("#password", "password")
    .add_click_button("#login-btn")
    .add_wait_for_element("#dashboard")
    
    # Initialize variables
    .add_set_variable("max_attempts", "5")
    .add_set_variable("current_attempt", "0")
    .add_set_variable("queue_capacity", "8")
    
    # Check queue status with retry logic
    .add_while_begin("check_passed")  # Retry loop
    .add_increment_variable("current_attempt", 1)
    
    # Navigate to queue view
    .add_click_button("[data-test-id='sidebar-menuitem-button-Favorites']")
    .add_wait(2000)
    
    # Check if queue has space
    .add_check_element(
        selector=".queue-counter",
        check_type="less",
        expected_value="${queue_capacity}",
        attribute="text"
    )
    
    # If queue has space, create task
    .add_if_begin("check_passed")
    .add_log_message("Queue has space - creating task", "logs/automation.log")
    .add_click_button(".creation-button")
    .add_upload_image("#file-upload", "image.jpg")
    .add_toggle_setting("#high-quality", True)
    .add_input_text("#prompt", "Generate amazing content")
    .add_click_button("#submit-btn")
    .add_break()  # Exit retry loop on success
    .add_if_end()
    
    # If queue is full, wait and retry
    .add_if_begin("check_failed")
    .add_log_message("Queue full - waiting before retry", "logs/automation.log")
    .add_conditional_wait(
        condition="check_failed",
        wait_time=30000,  # Wait 30 seconds
        max_retries=3
    )
    .add_if_end()
    
    # Check if max attempts reached
    .add_check_element(
        selector="body",  # Dummy check to use variable comparison
        check_type="greater",
        expected_value="${max_attempts}",
        attribute="data-attempts"
    )
    .add_if_begin("check_passed")
    .add_log_message("Max attempts reached - stopping", "logs/automation.log")
    .add_break()
    .add_if_end()
    
    .add_while_end()
    .build()
)
```

### Variable Management and Dynamic Content

```python
# Using variables for dynamic automation
sequence = (builder
    # Set up automation parameters
    .add_set_variable("task_prefix", "Automation Task")
    .add_set_variable("task_number", "1")
    .add_set_variable("total_tasks", "0")
    
    # Create multiple tasks with dynamic names
    .add_while_begin("check_passed")
    
    # Create task with dynamic title
    .add_input_text("#task-title", "${task_prefix} #${task_number}")
    .add_input_text("#description", "Automated task created on $(date)")
    .add_click_button("#create-task")
    
    # Update counters
    .add_increment_variable("task_number", 1)
    .add_increment_variable("total_tasks", 1)
    
    # Log progress
    .add_log_message(
        "Created task ${task_number} - Total: ${total_tasks}",
        "logs/task_creation.log"
    )
    
    # Check if we should continue (example: stop at 5 tasks)
    .add_check_element(
        selector=".task-counter",
        check_type="less",
        expected_value="5",
        attribute="text"
    )
    
    .add_while_end()
    .build()
)
```

### Error Handling

The tool provides detailed error reporting:

```python
results = await engine.run_automation()

if not results['success']:
    for error in results['errors']:
        print(f"Action {error['action_index']}: {error['error']}")
```

### Programmatic Usage

Integrate automation into your Python scripts:

```python
import asyncio
from web_automation import WebAutomationEngine, AutomationSequenceBuilder

async def main():
    # Build or load configuration
    config = AutomationSequenceBuilder.load_from_file("config.json")
    
    # Run automation
    engine = WebAutomationEngine(config)
    results = await engine.run_automation()
    
    # Process results
    if results['success']:
        print("Automation completed!")
        print(f"Downloaded files: {results['outputs']}")

asyncio.run(main())
```

## Tips for Reliable Automation

### Selector Best Practices
1. **Use Specific Selectors**: Prefer IDs and unique classes over generic selectors
2. **Test Selectors**: Use browser DevTools to verify selectors work
3. **Avoid Fragile Selectors**: Don't rely on deep nested structures that may change
4. **Use data-test-id**: Prefer test-specific attributes when available

### Timing and Synchronization
5. **Add Wait Actions**: Allow time for page loads and dynamic content
6. **Handle Timing**: Use `wait_for_element` before interacting with dynamic content
7. **Queue Detection**: Use multiple detection strategies for reliable queue monitoring
8. **Element Attribute Matching**: Use correct attributes (`text` for DIV content, `value` for inputs)

### Flow Control and Error Handling
9. **Conditional Logic**: Use IF/ELSE blocks for robust error handling
10. **While Loops**: Implement retry logic with proper exit conditions
11. **Variable Management**: Store state information for complex workflows
12. **Break Conditions**: Always provide exit strategies for loops
13. **Logging**: Add comprehensive logging for debugging and monitoring

### Debugging and Development
14. **Error Recovery**: Use `--continue-on-error` for non-critical actions
15. **Debugging**: Run with `--show-browser` to see what's happening
16. **Test Incrementally**: Build and test automations step by step
17. **Use Log Files**: Monitor automation progress with detailed logging

## Performance Optimization

- **Headless Mode**: Run without browser UI for better performance
- **Parallel Execution**: Run multiple instances for different tasks
- **Minimal Waits**: Use element-based waits instead of fixed delays
- **Reuse Sessions**: For multiple automations on same site

## Troubleshooting

### Common Issues

1. **Element not found**: 
   - Verify selector in browser DevTools
   - Add wait actions before interaction
   - Check if element is in iframe

2. **Timeout errors**:
   - Increase timeout values
   - Check network connectivity
   - Verify page loads completely

3. **Download failures**:
   - Ensure download directory exists
   - Check file permissions
   - Verify download triggers

### Debug Mode

Run with verbose logging:
```bash
python automaton-cli.py run -c config.json -v
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing issues for solutions
- Review debug logs for error details