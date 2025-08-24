# Automaton - Advanced Web Automation Framework 🤖

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-latest-green.svg)](https://playwright.dev/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A powerful, lightweight web automation framework with both GUI and CLI interfaces. Built with Python and Playwright for reliable browser automation with advanced flow control, queue management, and intelligent download handling.

## ✨ Features

### 🎯 Core Capabilities
- **Dual Interface**: Modern GUI with Tkinter or powerful CLI for automation
- **30+ Action Types**: Comprehensive set of web interaction actions
- **Flow Control**: Advanced IF/ELIF/ELSE and WHILE loop support
- **Queue Management**: Intelligent queue detection and capacity management
- **Variable System**: Dynamic variables with substitution support
- **Stop Functionality**: Graceful termination with controller integration
- **Download Automation**: Advanced file download with metadata tracking
- **Scheduler Support**: Datetime-based scheduling with timezone support

### 🔧 Technical Features
- **Async Execution**: Fast and efficient browser automation
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Headless/Headed Mode**: Run with or without browser UI
- **Detailed Logging**: Comprehensive logging for debugging
- **Error Recovery**: Automatic retry mechanisms and error handling
- **Browser Persistence**: Keep browser open for debugging
- **Security Features**: Credential management and input validation

## 📋 Supported Action Types

### Basic Actions
| Action | Description | Example |
|--------|-------------|---------|
| `INPUT_TEXT` | Fill text fields | Enter username/password |
| `CLICK_BUTTON` | Click elements | Submit forms |
| `UPLOAD_IMAGE` | Upload files | Profile pictures |
| `TOGGLE_SETTING` | Check/uncheck boxes | Accept terms |
| `WAIT` | Pause execution | Wait 2 seconds |
| `WAIT_FOR_ELEMENT` | Wait for element | Wait for button |
| `REFRESH_PAGE` | Reload page | Refresh content |
| `EXPAND_DIALOG` | Expand dialogs | Show more options |
| `SWITCH_PANEL` | Switch panels | Navigate tabs |

### Advanced Actions
| Action | Description | Use Case |
|--------|-------------|----------|
| `CHECK_ELEMENT` | Validate content | Verify text/values |
| `CHECK_QUEUE` | Monitor queues | Check capacity |
| `SET_VARIABLE` | Store values | Save user data |
| `INCREMENT_VARIABLE` | Increment numbers | Count iterations |
| `LOG_MESSAGE` | Record progress | Debug logging |
| `LOGIN` | Automated login | Authentication |
| `DOWNLOAD_FILE` | Download files | Save documents |

### Flow Control
| Action | Description | Example |
|--------|-------------|---------|
| `IF_BEGIN`/`IF_END` | Conditional blocks | If element exists |
| `ELIF`/`ELSE` | Conditional branches | Multiple conditions |
| `WHILE_BEGIN`/`WHILE_END` | Loop blocks | Repeat until done |
| `BREAK`/`CONTINUE` | Loop control | Exit/skip iteration |
| `CONDITIONAL_WAIT` | Retry with backoff | Wait for success |
| `SKIP_IF` | Conditional skip | Skip on condition |
| `STOP_AUTOMATION` | Terminate | Emergency stop |

### Generation Downloads (Enhanced)
| Action | Description | Features |
|--------|-------------|----------|
| `START_GENERATION_DOWNLOADS` | Begin downloads | **NEW**: Descriptive naming, Infinite scroll |
| `STOP_GENERATION_DOWNLOADS` | Stop downloads | Graceful stop |
| `CHECK_GENERATION_STATUS` | Check progress | Status monitoring |

#### 🆕 New Download Features
- **Infinite Scroll**: Automatically scrolls to download entire galleries
- **Enhanced Naming**: `vid_2025-08-24-14-35-22_project.mp4` instead of `#000000001.mp4`
- **Text-Based Detection**: Robust element finding using text landmarks
- **Full Prompt Extraction**: Complete prompt text without truncation

## 🚀 Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Chrome/Chromium browser

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/automaton.git
cd automaton
```

### Step 2: Create Virtual Environment
```bash
python3.11 -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux  
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install Playwright Browsers
```bash
playwright install chromium
```

### Step 5: Verify Installation
```bash
python3.11 -c "import playwright; print('✅ Installation successful!')"
```

## 🎮 Quick Start

### GUI Mode

Launch the graphical interface:
```bash
python3.11 automaton-gui.py
```

**Steps:**
1. Enter automation name and target URL
2. Add actions using the "Add Action" button
3. Configure selectors and values
4. Save configuration for reuse
5. Click "Run Automation" to execute
6. Use "Stop" button for graceful termination

### CLI Mode

#### Create New Automation
```bash
python3.11 automaton-cli.py create -n "My Task" -u "https://example.com" -o config.json
```

#### Run Automation
```bash
# Run headless
python3.11 automaton-cli.py run -c config.json

# Run with browser visible
python3.11 automaton-cli.py run -c config.json --show-browser

# Continue on error
python3.11 automaton-cli.py run -c config.json --continue-on-error
```

#### List Available Actions
```bash
python3.11 automaton-cli.py list-actions
```

## 📖 Usage Examples

### Example 1: Simple Form Submission
```python
from src.core.engine import AutomationSequenceBuilder

builder = AutomationSequenceBuilder("Form Submit", "https://example.com/form")

sequence = (builder
    .add_wait_for_element("#form-container")
    .add_input_text("#name", "John Doe")
    .add_input_text("#email", "john@example.com")
    .add_click_button("#submit")
    .add_wait_for_element(".success-message")
    .build()
)

builder.save_to_file("form_automation.json")
```

### Example 2: Queue Management with WHILE Loop
```python
sequence = (builder
    .add_set_variable("max_tasks", "8")
    .add_set_variable("current", "0")
    
    # Check queue status
    .add_check_element(".queue-count", "less", "${max_tasks}")
    
    # WHILE loop - create tasks until full
    .add_while_begin("check_result == true")
        .add_click_button(".create-task")
        .add_wait(2000)
        .add_increment_variable("current", 1)
        .add_check_element(".queue-count", "less", "${max_tasks}")
    .add_while_end()
    
    .add_log_message("Queue filled: ${current} tasks created")
    .build()
)
```

### Example 3: Conditional Download with Error Handling
```python
sequence = (builder
    .add_check_element("#download-ready", "equals", "true")
    
    .add_if_begin("check_result == true")
        .add_click_button("#download-btn")
        .add_wait(3000)
        .add_download_file("#file-link")
        .add_log_message("Download completed")
    .add_else()
        .add_log_message("Download not ready")
        .add_refresh_page()
    .add_if_end()
    .build()
)
```

### Example 4: Generation Downloads (Enhanced)
```json
{
  "name": "Download Generations with Enhanced Features",
  "url": "https://platform.com",
  "actions": [
    {
      "type": "login",
      "value": {
        "username": "user@example.com",
        "password": "password"
      }
    },
    {
      "type": "start_generation_downloads",
      "value": {
        "max_downloads": 100,
        "downloads_folder": "/path/to/downloads",
        
        "_comment": "Enhanced Naming (NEW)",
        "use_descriptive_naming": true,
        "unique_id": "project_alpha",
        "naming_format": "{media_type}_{creation_date}_{unique_id}",
        
        "_comment": "Infinite Scroll (NEW)",
        "scroll_batch_size": 10,
        "scroll_amount": 600,
        
        "_comment": "Text-Based Detection (NEW)",
        "image_to_video_text": "Image to video",
        "download_no_watermark_text": "Download without Watermark"
      }
    }
  ]
}
```
**Output**: Files named like `vid_2025-08-24-14-35-22_project_alpha.mp4`

## 🧪 Testing

### Run All Tests
```bash
python3.11 -m pytest tests/ -v
```

### Run Specific Tests
```bash
# Stop functionality tests
python3.11 -m pytest tests/test_stop_functionality.py -v

# Generation download tests
python3.11 -m pytest tests/test_generation_downloads.py -v

# GUI tests
python3.11 -m pytest tests/test_edit_action_windows.py -v
```

### Run with Coverage
```bash
python3.11 -m pytest tests/ --cov=src --cov-report=html
```

## 📚 Documentation

### Essential Guides
- [Stop Functionality Guide](docs/STOP_FUNCTIONALITY_GUIDE.md) - Stop mechanism implementation
- [Generation Download Guide](docs/GENERATION_DOWNLOAD_GUIDE.md) - Automated downloads
- [Automation Scheduler Guide](docs/AUTOMATION_SCHEDULER_GUIDE.md) - Scheduling automation
- [While Loop Guide](docs/WHILE_LOOP_AUTOMATION_GUIDE.md) - Loop control
- [Conditional Flow Guide](docs/conditional_flow_guide.md) - IF/ELSE usage
- [Selector Guide](docs/selector_guide.md) - CSS selector strategies

### API Documentation
- [ActionType Reference](src/core/engine.py) - All action types
- [Controller API](src/core/controller.py) - Control signals
- [GUI Components](src/interfaces/gui.py) - Interface elements
- [CLI Commands](src/interfaces/cli.py) - Command reference

## 🏗️ Project Structure

```
automaton/
├── src/
│   ├── core/
│   │   ├── engine.py                 # Main automation engine
│   │   ├── controller.py             # State management
│   │   ├── keyboard_handler.py       # Keyboard control
│   │   └── generation_download_handlers.py
│   ├── interfaces/
│   │   ├── gui.py                    # GUI interface
│   │   └── cli.py                    # CLI interface
│   └── utils/
│       ├── download_manager.py       # Download handling
│       ├── generation_download_manager.py
│       ├── performance_monitor.py
│       └── credential_manager.py
├── tests/                             # Test suite
├── docs/                              # Documentation
├── examples/                          # Example scripts
├── scripts/                           # Utility scripts
├── configs/                           # Configuration files
└── workflows/                         # Saved workflows
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional configuration
export AUTOMATON_HEADLESS=true
export AUTOMATON_BROWSER_PATH=/path/to/chrome
export AUTOMATON_DOWNLOAD_DIR=/path/to/downloads
export AUTOMATON_LOG_LEVEL=DEBUG
```

### Configuration File
```json
{
  "name": "My Automation",
  "url": "https://example.com",
  "headless": false,
  "viewport": {
    "width": 1600,
    "height": 1000
  },
  "keep_browser_open": true,
  "actions": [...]
}
```

## 🐛 Troubleshooting

### Common Issues

#### Stop Button Not Working
- Ensure controller is properly initialized
- Check that engine has controller reference
- Verify control signal propagation

#### Downloads Failing
- Check download directory permissions
- Verify CSS selectors are correct
- Increase timeout values if needed

#### Queue Detection Issues
- Update selectors for current page structure
- Try multiple detection strategies
- Check browser console for values

#### Browser Not Found
```bash
# Install Playwright browsers
playwright install chromium

# Or specify browser path
export AUTOMATON_BROWSER_PATH=/usr/bin/chromium
```

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new features
5. Run the test suite
6. Update documentation
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linter
flake8 src/

# Run formatter
black src/

# Run type checker
mypy src/
```

## 📈 Performance Tips

- Use headless mode for better performance
- Batch similar operations together
- Implement appropriate wait strategies
- Monitor memory usage for long-running automations
- Use caching for repeated operations
- Optimize CSS selectors for speed

## 🔒 Security

- Never hardcode credentials in automation files
- Use environment variables for sensitive data
- Validate all user inputs
- Sanitize file paths to prevent traversal
- Implement rate limiting for API calls
- Review logs for sensitive information

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/) for reliable browser automation
- GUI powered by [Tkinter](https://docs.python.org/3/library/tkinter.html)
- Testing with [pytest](https://pytest.org/)

## 📞 Support

- 📧 Email: support@automaton.example
- 💬 Discord: [Join our community](https://discord.gg/automaton)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/automaton/issues)
- 📖 Wiki: [Documentation Wiki](https://github.com/yourusername/automaton/wiki)

---

**Automaton** - Making web automation simple, powerful, and reliable 🚀

*Last Updated: August 2024 | Version: 2.0.0*