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

- **Expand Dialog**: Click to expand dialogs or panels
- **Input Text**: Fill text fields
- **Upload Image**: Upload files to web forms
- **Toggle Settings**: Check/uncheck checkboxes and switches
- **Click Button**: Click any button element
- **Check Queue**: Monitor task queues for completion
- **Download File**: Download files when ready
- **Refresh Page**: Reload the current page
- **Switch Panel**: Navigate between different panels/tabs
- **Wait**: Pause for specified duration
- **Wait for Element**: Wait for elements to appear

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd web-automation-tool
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
python gui_interface.py
```

1. Enter automation name and target URL
2. Add actions using the "Add Action" button
3. Configure each action with selectors and values
4. Save configuration for reuse
5. Click "Run Automation" to execute

### CLI Mode

#### Create a new automation:
```bash
python cli_interface.py create -n "My Task" -u "https://example.com" -o my_task.json --interactive
```

#### Run automation from config:
```bash
python cli_interface.py run -c my_task.json
```

#### Run with browser visible:
```bash
python cli_interface.py run -c my_task.json --show-browser
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

### Example 2: File Processing Automation

```python
sequence = (builder
    .add_expand_dialog("#upload-dialog")
    .add_upload_image("#file-input", "/path/to/image.jpg")
    .add_toggle_setting("#enhance-option", True)
    .add_click_button("#start-process")
    .add_wait(5000)  # Wait 5 seconds
    .add_check_queue(".queue-item", "Completed")
    .add_download_file(".download-btn")
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

### Custom Action Sequences

Create complex workflows by chaining actions:

```python
# Login -> Navigate -> Process -> Download
sequence = (builder
    # Login flow
    .add_input_text("#username", "user@example.com")
    .add_input_text("#password", "password")
    .add_click_button("#login-btn")
    .add_wait_for_element("#dashboard")
    
    # Navigate to tool
    .add_switch_panel("#tools-tab")
    .add_click_button("#processor-tool")
    
    # Process files
    .add_upload_image("#file-upload", "image.jpg")
    .add_toggle_setting("#high-quality", True)
    .add_click_button("#process-btn")
    
    # Wait and download
    .add_wait(10000)
    .add_check_queue(".task-status", "Complete")
    .add_download_file("#download-result")
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

1. **Use Specific Selectors**: Prefer IDs and unique classes over generic selectors
2. **Add Wait Actions**: Allow time for page loads and dynamic content
3. **Test Selectors**: Use browser DevTools to verify selectors work
4. **Handle Timing**: Use `wait_for_element` before interacting with dynamic content
5. **Error Recovery**: Use `--continue-on-error` for non-critical actions
6. **Debugging**: Run with `--show-browser` to see what's happening

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
python cli_interface.py run -c config.json -v
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