# Installation and Setup Guide

## Table of Contents
- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting Installation](#troubleshooting-installation)

## System Requirements

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB minimum for installation, plus additional space for browser data
- **Processor**: Any modern CPU (2015 or newer)

### Software Requirements
- **Operating System**: 
  - Windows 10 or later
  - macOS 10.14 or later
  - Linux (Ubuntu 18.04+, Debian 10+, or equivalent)
- **Python**: 3.8 or later (3.11 recommended for full compatibility)
- **Web Browser**: Chrome, Firefox, Safari, or Edge (latest stable version)

### Python Dependencies
Automaton requires several Python packages that will be automatically installed:
- `playwright` for browser automation
- `asyncio` for asynchronous operations
- `tkinter` for the GUI interface (usually included with Python)
- Additional dependencies as listed in `requirements.txt`

## Installation Methods

### Method 1: Using pip (Recommended)

1. **Install Python 3.11** (if not already installed):
   - **Windows**: Download from [python.org](https://python.org)
   - **macOS**: Use Homebrew: `brew install python@3.11`
   - **Linux**: Use your package manager, e.g., `sudo apt install python3.11`

2. **Install Automaton**:
   ```bash
   pip install automaton
   ```

3. **Install Playwright browsers**:
   ```bash
   python3.11 -m playwright install
   ```

### Method 2: From Source

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/automaton.git
   cd automaton
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

4. **Install Playwright browsers**:
   ```bash
   python3.11 -m playwright install
   ```

### Method 3: Using the Makefile (Linux/macOS)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/automaton.git
   cd automaton
   ```

2. **Run the setup command**:
   ```bash
   make setup
   ```

   This command will:
   - Install Python dependencies
   - Install the package in development mode
   - Install Playwright browsers
   - Run code formatting and linting checks

## Configuration

### Initial Configuration

1. **Create a configuration directory**:
   ```bash
   mkdir -p ~/.config/automaton
   ```

2. **Create a basic configuration file**:
   ```bash
   touch ~/.config/automaton/config.json
   ```

3. **Edit the configuration file** with your preferred settings:
   ```json
   {
     "default_browser": "chromium",
     "headless": false,
     "viewport": {
       "width": 1280,
       "height": 720
     },
     "timeout": 10000,
     "downloads_directory": "~/Downloads/automaton"
   }
   ```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_browser` | string | "chromium" | Default browser to use ("chromium", "firefox", "webkit") |
| `headless` | boolean | false | Run browser in headless mode (no visible UI) |
| `viewport.width` | integer | 1280 | Default browser viewport width |
| `viewport.height` | integer | 720 | Default browser viewport height |
| `timeout` | integer | 10000 | Default timeout for actions in milliseconds |
| `downloads_directory` | string | "~/Downloads/automaton" | Directory for downloaded files |
| `keep_browser_open` | boolean | true | Keep browser open after automation completes |
| `log_level` | string | "INFO" | Logging level ("DEBUG", "INFO", "WARNING", "ERROR") |

### Environment Variables

You can also configure Automaton using environment variables:

```bash
export AUTOMATON_BROWSER=chromium
export AUTOMATON_HEADLESS=false
export AUTOMATON_VIEWPORT_WIDTH=1280
export AUTOMATON_VIEWPORT_HEIGHT=720
export AUTOMATON_TIMEOUT=10000
export AUTOMATON_DOWNLOADS_DIR=~/Downloads/automaton
```

### Credential Management

For secure handling of credentials (usernames, passwords, API keys), Automaton supports encrypted credential storage:

1. **Create a credentials directory**:
   ```bash
   mkdir -p ~/.config/automaton/credentials
   ```

2. **Create a credentials file**:
   ```bash
   touch ~/.config/automaton/credentials/my_service.json
   ```

3. **Add your credentials** (the file will be encrypted when first used):
   ```json
   {
     "username": "your_username",
     "password": "your_password"
   }
   ```

4. **Reference credentials in your automation configurations**:
   ```json
   {
     "credential_file": "my_service.json",
     "credential_key": "my_service"
   }
   ```

## Verification

### Verify Installation

1. **Check if Automaton is installed correctly**:
   ```bash
   automaton --version
   ```

2. **Test the GUI interface**:
   ```bash
   automaton-gui
   ```

3. **Test the CLI interface**:
   ```bash
   automaton-cli --help
   ```

### Run a Simple Test

Create a simple test automation file named `test_automation.json`:

```json
{
  "name": "Test Automation",
  "url": "https://example.com",
  "headless": true,
  "actions": [
    {
      "type": "WAIT_FOR_ELEMENT",
      "selector": "h1",
      "timeout": 10000,
      "description": "Wait for page title"
    },
    {
      "type": "CHECK_ELEMENT",
      "selector": "h1",
      "value": {
        "check": "contains",
        "value": "Example",
        "attribute": "text"
      },
      "description": "Check page title"
    }
  ]
}
```

Run the test automation:

```bash
automaton-cli run test_automation.json
```

If the test runs successfully and reports "Automation completed: true", your installation is working correctly.

## Troubleshooting Installation

### Common Issues

#### Python Version Compatibility
**Issue**: Automaton requires Python 3.8 or later, but your system has an older version.

**Solution**:
1. Check your Python version:
   ```bash
   python --version
   ```
2. Install Python 3.11 or later using your system's package manager or from python.org.
3. Use the specific Python version when installing:
   ```bash
   python3.11 -m pip install automaton
   ```

#### Playwright Browser Installation
**Issue**: Playwright browsers are not installed or are outdated.

**Solution**:
1. Install Playwright browsers:
   ```bash
   python3.11 -m playwright install
   ```
2. If you encounter permission issues, try:
   ```bash
   python3.11 -m playwright install --with-deps
   ```

#### Missing Dependencies
**Issue**: Some required packages are not installed.

**Solution**:
1. Install all dependencies from requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```
2. If you're using a virtual environment, make sure it's activated:
   ```bash
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate  # Windows
   ```

#### GUI Interface Issues
**Issue**: The GUI interface fails to start or displays errors.

**Solution**:
1. Check if tkinter is installed:
   ```bash
   python -c "import tkinter; print('tkinter is available')"
   ```
2. If tkinter is not available, install it:
   - **Ubuntu/Debian**: `sudo apt install python3-tk`
   - **Fedora**: `sudo dnf install python3-tkinter`
   - **macOS**: tkinter is usually included with Python
   - **Windows**: tkinter is usually included with Python

#### Permission Issues
**Issue**: Permission denied errors when installing or running Automaton.

**Solution**:
1. Install Automaton for the current user only:
   ```bash
   pip install --user automaton
   ```
2. Ensure the user has write permissions to the installation directories.
3. On Linux/macOS, consider using a virtual environment to avoid system-wide permission issues.

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**:
   ```bash
   automaton-cli --log-level DEBUG run your_automation.json
   ```

2. **Report an issue**:
   Visit the [GitHub Issues page](https://github.com/yourusername/automaton/issues) and create a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - Automaton version (`automaton --version`)
   - Full error message and stack trace
   - Steps to reproduce the issue

3. **Community Support**:
   Join our community forum or chat channel for help from other users and developers.

## Next Steps

After successfully installing and setting up Automaton, you can:

1. Learn about [Core Concepts](3_core_concepts.md) to understand how Automaton works
2. Follow the [User Guide](4_user_guide.md) to create your first automation
3. Explore the [API Reference](5_api_reference.md) for advanced usage
4. Check out the [Component Documentation](6_components_reference.md) for information on specific components