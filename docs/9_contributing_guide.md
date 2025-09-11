# Automaton Contributing Guide

## Introduction

Thank you for your interest in contributing to Automaton! This guide provides information on how to contribute to the project, including development setup, coding standards, and the pull request process.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Code Organization](#code-organization)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation Guidelines](#documentation-guidelines)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)
9. [Feature Requests](#feature-requests)
10. [Community Guidelines](#community-guidelines)

## Getting Started

### Ways to Contribute

There are many ways to contribute to Automaton:

- **Code contributions**: Fix bugs, implement new features, or improve performance
- **Documentation**: Improve or expand documentation
- **Bug reports**: Report issues you encounter
- **Feature requests**: Suggest new features or improvements
- **Testing**: Help test new releases or features
- **Community support**: Help other users on forums or issue trackers

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and discussions
- **Pull Requests**: For code contributions
- **Email**: For sensitive security issues (see SECURITY.md)

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Git
- A GitHub account

### Forking and Cloning

1. Fork the Automaton repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/automaton.git
   cd automaton
   ```
3. Add the original repository as a remote:
   ```bash
   git remote add upstream https://github.com/olereon/automaton.git
   ```

### Setting Up the Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv automaton-dev
   source automaton-dev/bin/activate  # On Windows: automaton-dev\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   make setup
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

Run the test suite:
```bash
make test
```

Run tests with coverage:
```bash
make test-cov
```

Run specific test categories:
```bash
python3.11 -m pytest tests/ -v -m unit
python3.11 -m pytest tests/ -v -m integration
```

## Code Organization

### Project Structure

```
automaton/
├── src/                    # Source code
│   └── automaton/          # Main package
│       ├── actions/        # Action implementations
│       ├── browser/        # Browser management
│       ├── config/         # Configuration handling
│       ├── controller/     # Execution control
│       ├── errors/         # Error handling
│       ├── logging/        # Logging utilities
│       ├── utils/          # Utility functions
│       └── __init__.py     # Package initialization
├── tests/                  # Test files
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── conftest.py         # Test configuration
├── docs/                   # Documentation
├── examples/               # Example configurations
├── Makefile                # Build commands
├── setup.py                # Package setup
└── pyproject.toml          # Project configuration
```

### Adding New Actions

When adding new actions:

1. Create a new file in `src/automaton/actions/` or add to an existing file
2. Implement the `ActionHandler` interface:
   ```python
   from automaton.actions import Action, ActionResult, ActionHandler
   from automaton.context import ExecutionContext
   
   class NewActionHandler(ActionHandler):
       async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
           # Implementation here
           pass
       
       def validate(self, action: Action) -> List[str]:
           # Validation logic here
           pass
   ```

3. Register the action in the appropriate module
4. Add comprehensive tests
5. Update documentation

### Adding New Components

When adding new components:

1. Follow the existing directory structure
2. Implement clear interfaces
3. Add appropriate error handling
4. Include comprehensive tests
5. Update documentation

## Coding Standards

### Python Style Guidelines

- Follow PEP 8 style guidelines
- Use 100-character line length (enforced by Black)
- Use type hints for all function signatures and public attributes
- Use docstrings for all public modules, classes, and functions

### Code Formatting

- Code is formatted using Black with 100-character line length
- Import sorting is handled by isort
- Linting is performed using flake8 with the following ignored rules:
  - E203: Whitespace before ':'
  - W503: Line break before binary operator
  - E722: Bare except

### Naming Conventions

- Use `snake_case` for functions, variables, and modules
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants
- Use `_leading_underscore` for protected/internal attributes
- Use `__double_leading_underscore` for private attributes

### Type Hints

- Use type hints for all function signatures and public attributes
- Use the `typing` module for complex types
- Use `Optional` for nullable values
- Use `Union` for multiple possible types
- Use `List`, `Dict`, `Tuple`, etc. for generic types

### Error Handling

- Use specific exception types rather than generic `Exception`
- Include descriptive error messages
- Use context managers (`with` statements) for resource management
- Implement proper cleanup in `finally` blocks

### Asynchronous Code

- Use `async`/`await` for all I/O operations
- Avoid blocking calls in async functions
- Use `asyncio.gather()` for concurrent operations
- Handle cancellation properly with `asyncio.CancelledError`

## Testing Guidelines

### Test Structure

- Unit tests should be fast and isolated
- Integration tests should test component interactions
- Use pytest fixtures for setup and teardown
- Group related tests in classes

### Test Naming

- Use descriptive test names that explain what is being tested
- Use the format `test_[feature]_[scenario]_[expected_result]`
- Use underscores to separate words in test names

### Test Markers

Use the following pytest markers to categorize tests:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.security`: Security-related tests
- `@pytest.mark.gui`: GUI-related tests
- `@pytest.mark.browser`: Browser-related tests
- `@pytest.mark.login`: Tests requiring login
- `@pytest.mark.network`: Tests requiring network access

### Test Coverage

- Maintain a minimum of 80% code coverage
- Focus on testing critical paths and edge cases
- Use mocking for external dependencies
- Write tests for both success and failure scenarios

### Example Test

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from automaton.actions import Action, ActionResult
from automaton.context import ExecutionContext
from automaton.actions.click_button import ClickButtonHandler

@pytest.mark.unit
class TestClickButtonHandler:
    @pytest.mark.asyncio
    async def test_click_button_success(self):
        # Setup
        mock_page = AsyncMock()
        mock_page.click = AsyncMock()
        
        mock_context = MagicMock()
        mock_context.page = mock_page
        
        handler = ClickButtonHandler()
        action = Action(type="click_button", selector="#submit-button")
        
        # Execute
        result = await handler.execute(action, mock_context)
        
        # Verify
        assert result.success is True
        mock_page.click.assert_called_once_with("#submit-button")
    
    @pytest.mark.asyncio
    async def test_click_button_failure(self):
        # Setup
        mock_page = AsyncMock()
        mock_page.click.side_effect = Exception("Element not found")
        
        mock_context = MagicMock()
        mock_context.page = mock_page
        
        handler = ClickButtonHandler()
        action = Action(type="click_button", selector="#non-existent-button")
        
        # Execute
        result = await handler.execute(action, mock_context)
        
        # Verify
        assert result.success is False
        assert "Element not found" in result.message
```

## Documentation Guidelines

### Code Documentation

- Use Google-style docstrings
- Include parameters, returns, and raises sections
- Provide examples for complex functions
- Document all public APIs

### Example Docstring

```python
def extract_data(page: Page, selector: str, attribute: str = None) -> List[str]:
    """
    Extract data from elements matching the selector.
    
    Args:
        page: The Playwright page object.
        selector: CSS selector for elements to extract data from.
        attribute: Optional attribute to extract. If None, extracts text content.
    
    Returns:
        List of extracted data values.
    
    Raises:
        ElementNotFoundError: If no elements match the selector.
    
    Example:
        >>> page = await browser.new_page()
        >>> data = extract_data(page, ".product-name")
        >>> print(data)
        ['Product 1', 'Product 2', 'Product 3']
    """
    # Implementation here
    pass
```

### User Documentation

- Update relevant documentation files when adding new features
- Include examples for all new functionality
- Follow the existing documentation structure and style
- Use clear, concise language
- Include troubleshooting information for common issues

### API Documentation

- Document all public APIs in the API Reference
- Include parameter types and descriptions
- Include return value types and descriptions
- Include example usage
- Document all possible errors

## Pull Request Process

### Creating a Pull Request

1. Create a new branch from the latest `main` branch:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. Make your changes
3. Ensure your code follows all coding standards:
   ```bash
   make check
   ```

4. Ensure all tests pass:
   ```bash
   make test
   ```

5. Commit your changes with a clear commit message:
   ```bash
   git commit -m "Add new feature: description of changes"
   ```

6. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a pull request against the `main` branch of the original repository

### Pull Request Requirements

- All tests must pass
- Code must adhere to coding standards
- Documentation must be updated for new features
- Changes must be logically grouped into commits
- Commit messages must be clear and descriptive

### Pull Request Review Process

1. Automated checks will run on your pull request
2. A maintainer will review your pull request
3. Address any review comments
4. Update your branch as needed
5. Once approved, your pull request will be merged

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line
- Consider starting the commit message with an applicable emoji:
  - ✨ (`:sparkles:`): New feature
  - 🐛 (`:bug:`): Bug fix
  - 📚 (`:books:`): Documentation
  - 🎨 (`:art:`): Code style/formatting
  - ⚡️ (`:zap:`): Performance
  - 🔒 (`:lock:`): Security
  - 🔧 (`:wrench:`): Configuration/Build

### Example Commit Message

```
✨ Add support for custom actions

Implement a new action handler interface that allows users to
create custom actions. This includes base classes and registration
mechanisms.

Resolves #123
```

## Issue Reporting

### Bug Reports

When reporting bugs, please include:

1. A clear and descriptive title
2. A detailed description of the issue
3. Steps to reproduce the issue
4. Expected behavior
5. Actual behavior
6. Environment information:
   - Automaton version
   - Python version
   - Operating system
   - Browser version (if applicable)
7. Any relevant error messages or stack traces
8. A minimal example that reproduces the issue

### Bug Report Template

```markdown
## Bug Description
A clear and concise description of the bug.

## Steps to Reproduce
1. Set up configuration '...'
2. Run command '...'
3. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Environment
- Automaton version: [e.g., 1.0.0]
- Python version: [e.g., 3.11.0]
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 115]

## Additional Context
Add any other context about the problem here.
```

## Feature Requests

### Requesting Features

When requesting features, please include:

1. A clear and descriptive title
2. A detailed description of the proposed feature
3. The problem this feature would solve
4. Any alternative solutions you've considered
5. How you would use this feature
6. Any potential implementation ideas

### Feature Request Template

```markdown
## Feature Description
A clear and concise description of the feature.

## Problem Statement
What problem does this feature solve? Why is it needed?

## Proposed Solution
Describe the solution you'd like to see implemented.

## Alternative Solutions
Describe any alternative solutions or features you've considered.

## Use Cases
How would you use this feature? Please provide specific examples.

## Implementation Ideas (Optional)
Any ideas on how this feature could be implemented?
```

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Be open to different perspectives
- Assume good faith
- Be collaborative

### Getting Help

- Check the documentation first
- Search existing issues and discussions
- Create a new issue if needed
- Ask questions in GitHub Discussions

### Contributing Etiquette

- Start with small contributions
- Ask for help if you're unsure
- Be patient with the review process
- Be open to feedback and suggestions
- Help review other contributors' pull requests

## Recognition

Contributors will be recognized in:

- The release notes for each version
- The CONTRIBUTORS.md file
- The commit history (for code contributions)

Thank you for contributing to Automaton!

## Next Steps

After familiarizing yourself with the contribution process:

1. [Review Deployment Options](10_deployment_guide.md) for production environments
2. Check the main README for an overview of the project
3. Start with a good first issue (labeled "good first issue")

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*