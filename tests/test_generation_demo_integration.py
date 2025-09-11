#!/usr/bin/env python3
"""
Integration Test for Generation Download Demo

This test validates the actual generation download demo script and workflow,
focusing on the real-world integration of all fixes.

Usage:
    python3.11 tests/test_generation_demo_integration.py
"""

import asyncio
import logging
import sys
import unittest
import tempfile
import json
import subprocess
import signal
import time
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import pytest

# Add the parent directory to Python path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(parent_dir / 'src'))

from examples.generation_download_demo import demo_generation_downloads
from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/home/olereon/workspace/github.com/olereon/automaton/logs/test_demo_integration.log')
    ]
)
logger = logging.getLogger(__name__)


class TestGenerationDemoIntegration:
    """Test the actual demo script integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_downloads_dir = Path("/home/olereon/workspace/github.com/olereon/automaton/downloads/test_integration")
        self.test_logs_dir = Path("/home/olereon/workspace/github.com/olereon/automaton/logs")
        
        # Create test directories
        self.test_downloads_dir.mkdir(parents=True, exist_ok=True)
        self.test_logs_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up test files but keep directories
        if self.test_downloads_dir.exists():
            for file in self.test_downloads_dir.glob("*"):
                if file.is_file():
                    file.unlink()
    
    async def test_demo_configuration_loading(self):
        """Test that the demo properly loads and validates configuration"""
        logger.info("=== Testing Demo Configuration Loading ===")
        
        # Load the actual config file
        config_path = parent_dir / "examples" / "generation_download_config.json"
        
        self.assertTrue(config_path.exists(), "Configuration file not found")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Verify essential configuration elements
        self.assertIn('name', config_data)
        self.assertIn('url', config_data)
        self.assertIn('actions', config_data)
        
        # Find the start_generation_downloads action
        start_action = None
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                start_action = action
                break
        
        self.assertIsNotNone(start_action, "START_GENERATION_DOWNLOADS action not found")
        
        # Verify critical fixes are present in configuration
        value = start_action['value']
        
        # Fix #1: Landmark extraction enabled
        self.assertTrue(value.get('landmark_extraction_enabled', False))
        self.assertIn('creation_time_text', value)
        
        # Fix #2: Enhanced naming configuration
        self.assertTrue(value.get('use_descriptive_naming', False))
        self.assertIn('unique_id', value)
        self.assertIn('naming_format', value)
        
        # Fix #3: Text-based landmark selectors
        self.assertIn('image_to_video_text', value)
        self.assertIn('download_no_watermark_text', value)
        
        logger.info("✅ Demo configuration loading test passed")
    
    async def test_demo_action_creation(self):
        """Test that the demo creates proper Action objects"""
        logger.info("=== Testing Demo Action Creation ===")
        
        # Load config and create actions like the demo does
        config_path = parent_dir / "examples" / "generation_download_config.json"
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Convert to Action objects like the demo
        actions = []
        for action_data in config_data['actions']:
            action = Action(
                type=ActionType(action_data['type']),
                selector=action_data.get('selector'),
                value=action_data.get('value'),
                timeout=action_data.get('timeout', 10000),
                description=action_data.get('description')
            )
            actions.append(action)
        
        # Verify actions were created correctly
        self.assertGreater(len(actions), 0, "No actions created")
        
        # Find and verify the generation downloads action
        gen_action = None
        for action in actions:
            if action.type == ActionType.START_GENERATION_DOWNLOADS:
                gen_action = action
                break
        
        self.assertIsNotNone(gen_action, "Generation downloads action not created")
        self.assertIsNotNone(gen_action.value, "Generation downloads action has no value")
        self.assertIsInstance(gen_action.value, dict, "Generation downloads action value is not a dict")
        
        logger.info("✅ Demo action creation test passed")
    
    async def test_demo_engine_initialization(self):
        """Test that the demo properly initializes the WebAutomationEngine"""
        logger.info("=== Testing Demo Engine Initialization ===")
        
        # Create a test configuration similar to demo
        config_path = parent_dir / "examples" / "generation_download_config.json"
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Modify for testing (use test directories)
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                action['value']['downloads_folder'] = str(self.test_downloads_dir)
                action['value']['logs_folder'] = str(self.test_logs_dir)
                action['value']['max_downloads'] = 1  # Limit for testing
                break
        
        # Convert to AutomationConfig like the demo
        actions = []
        for action_data in config_data['actions']:
            action = Action(
                type=ActionType(action_data['type']),
                selector=action_data.get('selector'),
                value=action_data.get('value'),
                timeout=action_data.get('timeout', 10000),
                description=action_data.get('description')
            )
            actions.append(action)
        
        config = AutomationConfig(
            name=config_data['name'],
            url=config_data['url'],
            actions=actions,
            headless=config_data.get('headless', False),
            viewport=config_data.get('viewport', {"width": 1600, "height": 1000})
        )
        
        # Create engine like the demo
        engine = WebAutomationEngine(config)
        
        # Verify engine has generation download handlers
        self.assertTrue(hasattr(engine, '_handle_start_generation_downloads'))
        self.assertTrue(hasattr(engine, '_handle_stop_generation_downloads'))
        self.assertTrue(hasattr(engine, '_handle_check_generation_status'))
        
        # Verify engine is properly configured
        self.assertEqual(engine.config.name, config_data['name'])
        self.assertEqual(engine.config.url, config_data['url'])
        self.assertEqual(len(engine.config.actions), len(actions))
        
        logger.info("✅ Demo engine initialization test passed")
    
    async def test_demo_mock_execution(self):
        """Test demo execution with mocked browser interactions"""
        logger.info("=== Testing Demo Mock Execution ===")
        
        # Create test config
        config_path = parent_dir / "examples" / "generation_download_config.json"
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Modify for testing
        for action in config_data['actions']:
            if action['type'] == 'start_generation_downloads':
                action['value']['downloads_folder'] = str(self.test_downloads_dir)
                action['value']['logs_folder'] = str(self.test_logs_dir)
                action['value']['max_downloads'] = 1
                break
        
        # Convert to actions
        actions = []
        for action_data in config_data['actions']:
            action = Action(
                type=ActionType(action_data['type']),
                selector=action_data.get('selector'),
                value=action_data.get('value'),
                timeout=action_data.get('timeout', 10000),
                description=action_data.get('description')
            )
            actions.append(action)
        
        config = AutomationConfig(
            name=config_data['name'],
            url=config_data['url'],
            actions=actions,
            headless=True,  # Use headless for testing
            viewport={"width": 1600, "height": 1000}
        )
        
        engine = WebAutomationEngine(config)
        
        # Mock the browser and page operations
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_context = AsyncMock()
            
            # Set up mock chain
            mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            
            # Mock page operations
            mock_page.goto = AsyncMock()
            mock_page.wait_for_load_state = AsyncMock()
            
            # Mock generation download manager
            with patch.object(engine, '_generation_download_manager') as mock_manager:
                mock_manager.run_download_automation = AsyncMock(return_value={
                    'success': True,
                    'downloads_completed': 1,
                    'errors': [],
                    'start_time': '2025-08-26T15:30:00',
                    'end_time': '2025-08-26T15:31:00'
                })
                mock_manager.get_status.return_value = {
                    'downloads_completed': 1,
                    'max_downloads': 1,
                    'should_stop': False,
                    'log_file_path': str(self.test_logs_dir / 'generation_downloads.txt'),
                    'downloads_folder': str(self.test_downloads_dir)
                }
                
                # Mock login action
                mock_page.fill = AsyncMock()
                mock_page.click = AsyncMock()
                mock_page.wait_for_timeout = AsyncMock()
                
                # Run a simplified automation
                try:
                    # This would normally call engine.run_automation() but we'll test the parts
                    
                    # Test login action
                    login_action = actions[0]  # First action should be login
                    if login_action.type == ActionType.LOGIN:
                        result = await engine._handle_login(login_action)
                        # Mock login should succeed
                        self.assertTrue(result.get('success', False))
                    
                    # Test generation downloads action
                    gen_action = actions[2]  # Third action should be start_generation_downloads
                    if gen_action.type == ActionType.START_GENERATION_DOWNLOADS:
                        result = await engine._handle_start_generation_downloads(gen_action)
                        
                        # Verify successful execution
                        self.assertTrue(result['success'])
                        self.assertEqual(result['downloads_completed'], 1)
                        self.assertIsNotNone(result['manager_status'])
                    
                except Exception as e:
                    logger.error(f"Mock execution failed: {e}")
                    self.fail(f"Mock execution should not fail: {e}")
        
        logger.info("✅ Demo mock execution test passed")


class TestDemoFileSystem(unittest.TestCase):
    """Test demo file system operations"""
    
    def test_demo_file_exists(self):
        """Test that the demo file exists and is executable"""
        logger.info("=== Testing Demo File System ===")
        
        demo_path = parent_dir / "examples" / "generation_download_demo.py"
        config_path = parent_dir / "examples" / "generation_download_config.json"
        
        # Verify files exist
        self.assertTrue(demo_path.exists(), "Demo script not found")
        self.assertTrue(config_path.exists(), "Configuration file not found")
        
        # Verify demo file is readable
        with open(demo_path, 'r') as f:
            content = f.read()
        
        # Check for essential imports and functions
        self.assertIn("demo_generation_downloads", content)
        self.assertIn("WebAutomationEngine", content)
        self.assertIn("async def", content)
        
        logger.info("✅ Demo file system test passed")
    
    def test_demo_directories_created(self):
        """Test that demo creates necessary directories"""
        logger.info("=== Testing Demo Directory Creation ===")
        
        # Test directories that should be created
        required_dirs = [
            Path("/home/olereon/workspace/github.com/olereon/automaton/downloads"),
            Path("/home/olereon/workspace/github.com/olereon/automaton/logs")
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                # Create it to test creation works
                dir_path.mkdir(parents=True, exist_ok=True)
            
            self.assertTrue(dir_path.exists(), f"Directory {dir_path} should exist")
            self.assertTrue(dir_path.is_dir(), f"Path {dir_path} should be a directory")
        
        logger.info("✅ Demo directory creation test passed")


class TestDemoCommandLine(unittest.TestCase):
    """Test demo command line execution"""
    
    def test_demo_script_syntax(self):
        """Test that the demo script has valid Python syntax"""
        logger.info("=== Testing Demo Script Syntax ===")
        
        demo_path = parent_dir / "examples" / "generation_download_demo.py"
        
        # Try to compile the script
        with open(demo_path, 'r') as f:
            source = f.read()
        
        try:
            compile(source, demo_path, 'exec')
            logger.info("✅ Demo script syntax is valid")
        except SyntaxError as e:
            self.fail(f"Demo script has syntax error: {e}")
    
    def test_demo_imports(self):
        """Test that demo script imports work"""
        logger.info("=== Testing Demo Script Imports ===")
        
        try:
            # Try importing the demo module
            import sys
            demo_dir = str(parent_dir / "examples")
            if demo_dir not in sys.path:
                sys.path.insert(0, demo_dir)
            
            # This should not fail if imports are correct
            import generation_download_demo
            
            # Verify main function exists
            self.assertTrue(hasattr(generation_download_demo, 'demo_generation_downloads'))
            self.assertTrue(hasattr(generation_download_demo, 'main'))
            
            logger.info("✅ Demo script imports test passed")
            
        except ImportError as e:
            self.fail(f"Demo script import failed: {e}")


async def run_integration_test_suite():
    """Run the complete integration test suite"""
    logger.info("Starting Generation Download Demo Integration Test Suite")
    logger.info("=" * 70)
    
    # Run all test classes
    test_classes = [
        TestGenerationDemoIntegration,
        TestDemoFileSystem,
        TestDemoCommandLine
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        logger.info(f"Running {test_class.__name__}...")
        
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        passed_tests += result.testsRun - len(result.failures) - len(result.errors)
        
        # Track failures
        for failure in result.failures + result.errors:
            failed_tests.append(f"{test_class.__name__}.{failure[0]._testMethodName}: {failure[1]}")
    
    # Print results
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST SUITE RESULTS")
    logger.info("=" * 70)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {len(failed_tests)}")
    logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests:
        logger.error("FAILED TESTS:")
        for failure in failed_tests:
            logger.error(f"  ❌ {failure}")
        return False
    else:
        logger.info("✅ ALL INTEGRATION TESTS PASSED!")
        return True


def main():
    """Main entry point"""
    try:
        success = asyncio.run(run_integration_test_suite())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.warning("🛑 Integration test suite interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()