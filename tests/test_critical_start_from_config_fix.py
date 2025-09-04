#!/usr/bin/env python3.11
"""
Test Critical Start From Config Fix
===================================
Tests that the start_from parameter is properly passed from action value to config
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.core.generation_download_handlers import GenerationDownloadHandlers
from src.utils.generation_download_manager import DuplicateMode


class MockAction:
    def __init__(self, value_dict):
        self.value = value_dict


class TestCriticalStartFromConfigFix:
    """Test the critical fix for start_from config parameter"""
    
    def test_start_from_parameter_passed_to_config(self):
        """Test that start_from is correctly passed from action value to config"""
        
        # Create handler
        handler = GenerationDownloadHandlers()
        handler.__init_generation_downloads__()
        
        # Mock page
        mock_page = Mock()
        mock_page.context = Mock()
        handler.page = mock_page
        
        # Create action with start_from parameter
        action_value = {
            'max_downloads': 100,
            'downloads_folder': '/test/downloads',
            'logs_folder': '/test/logs',
            'start_from': '03 Sep 2025 16:15:18',  # This should be passed to config
            'duplicate_mode': 'skip'
        }
        
        action = MockAction(action_value)
        
        # Mock the run_download_automation to check config
        config_used = None
        
        async def mock_run_download_automation(page):
            nonlocal config_used
            config_used = handler._generation_download_manager.config
            return {
                'success': True,
                'downloads_completed': 0,
                'errors': []
            }
        
        # Temporarily replace the method
        original_method = None
        
        async def test_method():
            nonlocal original_method
            # Call the handler which creates config
            await handler._handle_start_generation_downloads(action)
            
            # Check that config was created with start_from
            assert handler._generation_download_manager is not None
            config = handler._generation_download_manager.config
            assert config.start_from == '03 Sep 2025 16:15:18'
            print("✅ CRITICAL FIX VERIFIED: start_from parameter correctly passed to config")
            
        # Run the test
        asyncio.run(test_method())
    
    def test_start_from_none_when_not_provided(self):
        """Test that start_from is None when not provided in action value"""
        
        # Create handler
        handler = GenerationDownloadHandlers()
        handler.__init_generation_downloads__()
        
        # Mock page
        mock_page = Mock()
        mock_page.context = Mock()
        handler.page = mock_page
        
        # Create action WITHOUT start_from parameter
        action_value = {
            'max_downloads': 100,
            'downloads_folder': '/test/downloads',
            'logs_folder': '/test/logs',
            'duplicate_mode': 'skip'
            # No start_from parameter
        }
        
        action = MockAction(action_value)
        
        async def test_method():
            # Call the handler which creates config
            await handler._handle_start_generation_downloads(action)
            
            # Check that config was created with start_from = None
            assert handler._generation_download_manager is not None
            config = handler._generation_download_manager.config
            assert config.start_from is None
            print("✅ Config correctly sets start_from to None when not provided")
            
        # Run the test
        asyncio.run(test_method())
    
    def test_config_creation_includes_start_from_field(self):
        """Test that the GenerationDownloadConfig creation includes start_from field"""
        
        # Read the handlers file to verify the fix is present
        handlers_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'core', 'generation_download_handlers.py')
        
        with open(handlers_file, 'r') as f:
            content = f.read()
        
        # Check that start_from is included in config creation
        assert 'start_from=config_data.get(\'start_from\')' in content
        assert '# START_FROM PARAMETER (CRITICAL FIX: was missing!)' in content
        
        print("✅ Source code verified: start_from parameter is included in config creation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])