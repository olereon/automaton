# Installing and Setting Up Automaton

## Introduction

This guide provides step-by-step instructions for installing and setting up Automaton on your system. Follow these instructions carefully to ensure a successful installation and optimal performance.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Verification](#verification)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Next Steps](#next-steps)

## Prerequisites

Before installing Automaton, ensure your system meets the following requirements:

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+ recommended)
- **RAM**: Minimum 4GB, 8GB recommended
- **Storage**: Minimum 1GB free space
- **Network**: Internet connection for downloading dependencies

### Software Requirements
- **Python**: Version 3.11 or higher
- **pip**: Python package manager (included with Python)
- **Chrome/Chromium**: Browser for automation (Chrome recommended)

### Checking Python Version
To verify your Python version, open a terminal or command prompt and run:

```bash
python3 --version
```

or

```bash
python --version
```

The output should show Python 3.11 or higher. If you have an older version, please upgrade Python before proceeding.

## Installation Steps

### Step 1: Clone the Repository

First, clone the Automaton repository from GitHub:

```bash
git clone https://github.com/yourusername/automaton.git
cd automaton
```

### Step 2: Create a Virtual Environment

Using a virtual environment is highly recommended to isolate dependencies:

```bash
python3.11 -m venv venv
```

#### Activate the Virtual Environment

- **On Windows**:
  ```bash
  venv\Scripts\activate
  ```

- **On macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

After activation, your command prompt should show the virtual environment name, like `(venv)`.

### Step 3: Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

This will install all necessary dependencies including Playwright, which is used for browser automation.

### Step 4: Install Playwright Browsers

Playwright requires browser binaries to function. Install them with:

```bash
playwright install chromium
```

This downloads and installs the Chromium browser that Playwright will control.

### Step 5: Verify Installation

Confirm that the installation was successful by testing the imports:

```bash
python3.11 -c "import playwright; print('✅ Playwright installation successful!')"
python3.11 -c "import src.core.engine; print('✅ Automaton installation successful!')"
```

If both commands print success messages, your installation is complete.

## Configuration

### Environment Variables

Automaton can be configured using environment variables. These are optional but recommended for customization:

```bash
# Optional configuration
export AUTOMATON_HEADLESS=true
export AUTOMATON_BROWSER_PATH=/path/to/chrome
export AUTOMATON_DOWNLOAD_DIR=/path/to/downloads
export AUTOMATON_LOG_LEVEL=DEBUG
```

#### Common Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `AUTOMATON_HEADLESS` | Run browser in headless mode | `false` |
| `AUTOMATON_BROWSER_PATH` | Path to browser executable | Auto-detected |
| `AUTOMATON_DOWNLOAD_DIR` | Directory for downloaded files | `./downloads` |
| `AUTOMATON_LOG_LEVEL` | Logging verbosity level | `INFO` |

### Configuration File

For more complex configurations, you can use a JSON configuration file:

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
  "actions": []
}
```

#### Configuration File Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `name` | String | Name of the automation | Required |
| `url` | String | Starting URL for the automation | Required |
| `headless` | Boolean | Run browser without UI | `false` |
| `viewport` | Object | Browser viewport dimensions | `{"width": 1280, "height": 720}` |
| `keep_browser_open` | Boolean | Keep browser open after completion | `false` |
| `actions` | Array | List of automation actions | `[]` |

## Verification

### Testing the GUI Interface

Launch the graphical interface to verify it works correctly:

```bash
python3.11 automaton-gui.py
```

A window should appear with the Automaton GUI. You can:
1. Enter an automation name and URL
2. Add actions using the interface
3. Save and run automations

### Testing the CLI Interface

Test the command-line interface:

```bash
# List available actions
python3.11 automaton-cli.py list-actions

# Create a simple test automation
python3.11 automaton-cli.py create -n "Test" -u "https://example.com" -o test.json

# Run the test automation
python3.11 automaton-cli.py run -c test.json --show-browser
```

If all commands execute without errors, your installation is working correctly.

## Troubleshooting

### Common Installation Issues

#### Python Version Incompatible
**Problem**: Automaton requires Python 3.11+, but you have an older version.

**Solution**: Upgrade Python:
- **Ubuntu/Debian**: Use `deadsnakes` PPA or compile from source
- **macOS**: Use Homebrew: `brew install python@3.11`
- **Windows**: Download from python.org

#### Playwright Installation Fails
**Problem**: `playwright install chromium` fails with network errors.

**Solution**:
1. Check your internet connection
2. Try again: `playwright install chromium`
3. If behind a proxy, configure proxy settings:
   ```bash
   export HTTPS_PROXY=http://your-proxy:port
   playwright install chromium
   ```

#### Import Errors
**Problem**: `ImportError: No module named 'src'` when running Automaton.

**Solution**: Ensure you're in the project root directory and the virtual environment is activated:
```bash
cd /path/to/automaton
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

#### Browser Not Found
**Problem**: Error message indicating browser not found.

**Solution**:
1. Install Playwright browsers: `playwright install chromium`
2. Or specify browser path:
   ```bash
   export AUTOMATON_BROWSER_PATH=/usr/bin/chromium
   ```

#### Permission Errors
**Problem**: Permission denied when creating files or directories.

**Solution**: Ensure you have write permissions in the project directory and download directory:
```bash
# Check permissions
ls -la
# Change ownership if needed (Linux/macOS)
sudo chown -R $USER:$USER /path/to/automaton
```

### Getting Help

If you encounter issues not covered here:

1. Check the [Troubleshooting Guide](8_troubleshooting_guide.md) for more detailed solutions
2. Search existing issues on [GitHub Issues](https://github.com/yourusername/automaton/issues)
3. Create a new issue with:
   - Operating system and version
   - Python version
   - Complete error message
   - Steps to reproduce the problem

## Next Steps

With Automaton successfully installed, you can:

1. [Explore Core Concepts](3_core_concepts.md) to understand key terminology
2. [Read the User Guide](4_user_guide.md) for basic usage instructions
3. [Try Example Automations](../examples/) to see Automaton in action
4. [Check API Reference](5_api_reference.md) for technical details

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*