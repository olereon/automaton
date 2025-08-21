"""
Pytest configuration and fixtures for Automaton test suite
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add src to Python path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_config():
    """Provide a basic automation configuration for testing"""
    return AutomationConfig(
        name="Test Automation",
        url="https://example.com",
        headless=True,
        viewport={"width": 1280, "height": 720},
        actions=[
            Action(
                type=ActionType.WAIT_FOR_ELEMENT,
                selector="#test-element",
                timeout=10000,
                description="Wait for test element"
            ),
            Action(
                type=ActionType.CLICK_BUTTON,
                selector="#test-button",
                timeout=5000,
                description="Click test button"
            )
        ]
    )

@pytest.fixture
def login_config():
    """Provide a configuration with login action for testing"""
    return AutomationConfig(
        name="Login Test",
        url="https://example.com/login",
        headless=True,
        viewport={"width": 1280, "height": 720},
        actions=[
            Action(
                type=ActionType.LOGIN,
                value={
                    "credential_id": "test_login",
                    "username_selector": "input[type='email']",
                    "password_selector": "input[type='password']",
                    "submit_selector": "button[type='submit']"
                },
                timeout=10000,
                description="Login with secure credentials"
            )
        ]
    )

@pytest.fixture
def temp_config_file(sample_config):
    """Create a temporary configuration file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_dict = {
            "name": sample_config.name,
            "url": sample_config.url,
            "headless": sample_config.headless,
            "viewport": sample_config.viewport,
            "actions": [
                {
                    "type": action.type.value,
                    "selector": action.selector,
                    "value": action.value,
                    "timeout": action.timeout,
                    "description": action.description
                }
                for action in sample_config.actions
            ]
        }
        json.dump(config_dict, f, indent=2)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)

@pytest.fixture
def mock_playwright():
    """Mock Playwright browser for testing without real browser"""
    mock_playwright = Mock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    # Setup mock chain
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    # Mock page methods
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock browser cleanup
    mock_context.close = AsyncMock()
    mock_browser.close = AsyncMock()
    
    return {
        'playwright': mock_playwright,
        'browser': mock_browser,
        'context': mock_context,
        'page': mock_page
    }

@pytest.fixture
def automation_engine(sample_config):
    """Create an automation engine instance for testing"""
    return WebAutomationEngine(sample_config)

@pytest.fixture
def mock_credential_manager():
    """Mock credential manager for testing secure credentials"""
    mock_cm = Mock()
    mock_cm.get_credential.return_value = {
        'username': 'test_user@example.com',
        'password': 'secure_test_password'
    }
    return mock_cm

@pytest.fixture(autouse=True)
def cleanup_browsers():
    """Automatically cleanup any browser instances after each test"""
    yield
    # This fixture runs after each test to ensure cleanup
    # In real implementation, we'd ensure all browsers are closed

@pytest.fixture
def security_test_config():
    """Configuration for testing security features"""
    return {
        "name": "Security Test",
        "url": "https://secure-site.example.com",
        "headless": True,
        "actions": [
            {
                "type": "login",
                "value": {
                    "username": "plaintext_user",  # Should trigger security warning
                    "password": "plaintext_pass",  # Should trigger security warning
                    "username_selector": "#username",
                    "password_selector": "#password",
                    "submit_selector": "#login-btn"
                }
            }
        ]
    }

@pytest.fixture(scope="session")
def test_credentials_dir():
    """Create temporary directory for credential testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

# Pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test content"""
    for item in items:
        # Mark tests that use browser fixtures
        if "mock_playwright" in item.fixturenames or "browser" in item.name.lower():
            item.add_marker(pytest.mark.browser)
        
        # Mark GUI tests
        if "gui" in item.name.lower() or "interface" in item.name.lower():
            item.add_marker(pytest.mark.gui)
        
        # Mark security tests
        if "security" in item.name.lower() or "credential" in item.name.lower():
            item.add_marker(pytest.mark.security)
        
        # Mark integration tests
        if "integration" in item.name.lower() or "e2e" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)

# Skip browser tests if no display available (for CI/CD)
def pytest_configure(config):
    """Configure pytest with custom settings"""
    if not os.environ.get('DISPLAY') and not os.environ.get('CI'):
        config.option.markexpr = "not gui"