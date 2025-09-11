# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build System

- Uses Makefile instead of standard Python package management
- `make setup` runs full development environment setup (install + check)
- `make check` combines both formatting and linting
- Python 3.11 is explicitly required for testing (see Makefile line 25)

## Python Version Reminder

- Always use `python3.11` explicitly when running Python commands in this project
- This is required for compatibility with project dependencies and testing framework
- Example: Use `python3.11 -m pytest tests/ -v` instead of just `pytest tests/ -v`

## Code Style

- Black formatter uses 100-character line length (not default 88)
- flake8 ignores E203 (whitespace before ':'), W503 (line break before binary operator), E722 (bare except)
- Pre-commit hooks enforce same 100-character line length and ignore rules

## Testing

- pytest requires specific markers for categorization: unit, integration, slow, security, gui, browser, login, network
- Async test support enabled with `asyncio_mode = auto`
- Coverage minimum set to 80% with HTML, term, and XML reports
- Tests run with `python3.11 -m pytest tests/ -v` explicitly (not just pytest)

## Project Structure

- Entry points defined in setup.py: automaton-cli, automaton-gui, and automaton
- Packages located in src/ directory with package_dir={"": "src"}
- Includes JSON/YAML config files as package data
- Memory store system persists context across development stages

## Important File Path Reminders

### GUI File Location

> **CRITICAL REMINDER**: The correct path for the GUI file is [`src/interfaces/gui.py`](src/interfaces/gui.py)
>
> **DO NOT** use `src/automaton/gui.py` as this is the wrong path and will cause errors.
>
> This is a common mistake that should be avoided. When working with GUI-related code, always ensure you are referencing the correct path:
> - **Correct**: [`src/interfaces/gui.py`](src/interfaces/gui.py)
> - **Incorrect**: `src/automaton/gui.py` (this file does not exist)