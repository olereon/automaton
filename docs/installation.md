# Installation and Setup Guide

## Overview

This guide provides step-by-step instructions for installing and setting up Automaton, an AI-powered web automation platform. Follow these instructions to get Automaton running on your system.

## Prerequisites

Before installing Automaton, ensure your system meets the following requirements:

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, Debian 10+, or equivalent)
- **RAM**: Minimum 4GB, recommended 8GB or more
- **Storage**: Minimum 500MB free space
- **Network**: Internet connection for downloading dependencies

### Software Requirements
- **Python**: Version 3.8 or higher (Python 3.11 recommended for development)
- **Git**: For cloning the repository (if installing from source)
- **Web Browser**: Chrome, Firefox, Safari, or Edge (for browser automation)

## Installation Methods

### Method 1: Install from PyPI (Recommended)

For most users, installing from PyPI is the simplest method:

```bash
# Install Automaton using pip
pip install automaton

# Verify installation
automaton --version
```

### Method 2: Install from Source

For developers or users who want the latest features:

```bash
# Clone the repository
git clone https://github.com/yourusername/automaton.git
cd automaton

# Install dependencies and the package
pip install -e .

# Verify installation
automaton --version
```

### Method 3: Development Installation

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/yourusername/automaton.git
cd automaton

# Install development dependencies
make setup

# Verify installation
automaton --version
```

## Dependencies

Automaton requires several dependencies, which are automatically installed when you install the package:

### Core Dependencies
- **playwright** (>=1.40.0): Browser automation library
- **asyncio-mqtt** (>=0.16.1): MQTT client for async operations

### CLI Dependencies
- **pyyaml** (>=6.0.1): YAML configuration file support
- **colorama** (>=0.4.6): Colored terminal output

### Optional Dependencies

#### For Enhanced Features
- **python-dotenv** (>=1.0.0): Environment variable management
- **requests** (>=2.31.0): HTTP library for API integrations
- **pillow** (>=10.0.0): Image processing capabilities

#### For Security
- **cryptography** (>=41.0.0): Secure credential storage

#### For Performance Monitoring
- **psutil** (>=5.9.0): System resource monitoring

### Development Dependencies
- **pytest** (>=7.4.0): Testing framework
- **pytest-asyncio** (>=0.21.0): Async support for pytest
- **black** (>=23.0.0): Code formatter
- **flake8** (>=6.0.0): Code linter

## Post-Installation Setup

### 1. Install Browser Dependencies

Automaton uses Playwright for browser automation. After installation, you need to install the required browser binaries:

```bash
# Install Playwright browser binaries
python -m playwright install

# Install specific browsers (optional)
python -m playwright install chromium
python -m playwright install firefox
python -m playwright install webkit
```

### 2. Configure Environment Variables (Optional)

Create a `.env` file in your project directory to configure environment variables:

```bash
# Create a .env file
touch .env
```

Add your configuration to the `.env` file:

```env
# Browser configuration
AUTOMATON_HEADLESS=true
AUTOMATON_BROWSER_PATH=/path/to/browser
AUTOMATON_USER_AGENT="Custom User Agent"
AUTOMATON_TIMEOUT=60000
AUTOMATON_KEEP_BROWSER_OPEN=false

# Logging configuration
AUTOMATON_LOG_LEVEL=INFO
AUTOMATON_LOG_FILE=automaton.log
```

### 3. Verify Installation

Run the following commands to verify that Automaton is properly installed:

```bash
# Check version
automaton --version

# Check help
automaton --help

# Test browser automation (simple example)
automaton test-browser
```

## Configuration

### Configuration Files

Automaton supports configuration through YAML files:

1. Create a configuration file named `automaton.yaml` in your project directory:

```yaml
# Browser settings
browser:
  headless: true
  viewport:
    width: 1280
    height: 720
  timeout: 30000

# Default settings
defaults:
  continue_on_error: false
  keep_browser_open: true

# Logging settings
logging:
  level: INFO
  file: automaton.log
```

### Environment Variables

You can also configure Automaton using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTOMATON_HEADLESS` | Run browser in headless mode | `true` |
| `AUTOMATON_BROWSER_PATH` | Path to browser executable | None |
| `AUTOMATON_USER_AGENT` | Custom user agent string | None |
| `AUTOMATON_TIMEOUT` | Default timeout in milliseconds | `30000` |
| `AUTOMATON_KEEP_BROWSER_OPEN` | Keep browser open after completion | `false` |
| `AUTOMATON_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `AUTOMATON_LOG_FILE` | Path to log file | None |

## Troubleshooting

### Common Issues

#### Installation Errors
**Problem**: Permission denied during installation
**Solution**: Use a virtual environment or install with `--user` flag:
```bash
pip install --user automaton
```

#### Browser Binary Issues
**Problem**: "Browser not found" errors
**Solution**: Install Playwright browser binaries:
```bash
python -m playwright install
```

#### Dependency Conflicts
**Problem**: Conflicts between package versions
**Solution**: Create a virtual environment:
```bash
python -m venv automaton-env
source automaton-env/bin/activate  # On Windows: automaton-env\Scripts\activate
pip install automaton
```

#### GUI Mode Issues
**Problem**: GUI doesn't start or display properly
**Solution**: Ensure tkinter is installed (usually included with Python):
```bash
# On Ubuntu/Debian:
sudo apt-get install python3-tk

# On macOS/Windows: tkinter is included with Python
```

### Getting Help

If you encounter issues not covered in this guide:

1. Check the [troubleshooting guide](troubleshooting.md)
2. Search existing [issues](https://github.com/yourusername/automaton/issues)
3. Create a new issue with details about your problem

## Next Steps

After completing the installation:

1. Read the [User Guide](user-guide.md) to learn basic usage
2. Explore the [Core Concepts](core-concepts.md) to understand how Automaton works
3. Check out the [Example Scripts](examples/) directory for practical examples
4. Join our community forum for support and discussions

## Uninstallation

To uninstall Automaton:

```bash
# If installed from PyPI
pip uninstall automaton

# If installed from source in development mode
pip uninstall automaton
```

Note: This will not remove any configuration files or logs you may have created.