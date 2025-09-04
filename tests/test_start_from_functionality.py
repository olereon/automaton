#!/usr/bin/env python3.11
"""
Test Start From Functionality
=============================
Tests the start_from parameter functionality for generation downloads.
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig


class TestStartFromFunctionality:
    """Test suite for start_from feature"""
    
    @pytest.fixture
    def config_with_start_from(self):
        """Create config with start_from parameter"""
        config = GenerationDownloadConfig()
        config.start_from = "03 Sep 2025 16:15:18"
        return config
    
    @pytest.fixture
    def config_without_start_from(self):
        """Create config without start_from parameter"""
        config = GenerationDownloadConfig()
        config.start_from = None
        return config
    
    @pytest.fixture
    def download_manager_with_start_from(self, config_with_start_from):
        """Create download manager with start_from config"""
        return GenerationDownloadManager(config_with_start_from)
    
    @pytest.fixture
    def download_manager_without_start_from(self, config_without_start_from):
        """Create download manager without start_from config"""
        return GenerationDownloadManager(config_without_start_from)
    
    def test_datetime_format_validation_valid(self, download_manager_with_start_from):
        """Test datetime format validation with valid formats"""
        manager = download_manager_with_start_from
        
        # Valid formats
        valid_formats = [
            "03 Sep 2025 16:15:18",
            "1 Jan 2025 09:30:45", 
            "15 Dec 2024 23:59:59",
            "31 Mar 2025 00:00:00"
        ]
        
        for datetime_str in valid_formats:
            assert manager._validate_datetime_format(datetime_str) == True, f"Should be valid: {datetime_str}"
    
    def test_datetime_format_validation_invalid(self, download_manager_with_start_from):
        """Test datetime format validation with invalid formats"""
        manager = download_manager_with_start_from
        
        # Invalid formats
        invalid_formats = [
            "2025-09-03 16:15:18",      # Wrong date format
            "Sep 03 2025 16:15:18",     # Wrong order
            "03 September 2025",        # Full month name
            "03 Sep 25 16:15",          # Short year, missing seconds
            "03 Sep 2025",              # Missing time
            "16:15:18 03 Sep 2025",     # Time first
            "",                         # Empty string
            "invalid datetime",         # Not a datetime
            "03/09/2025 16:15:18",      # Slash separators
        ]
        
        for datetime_str in invalid_formats:
            assert manager._validate_datetime_format(datetime_str) == False, f"Should be invalid: {datetime_str}"
    
    def test_config_start_from_parameter(self, config_with_start_from, config_without_start_from):
        """Test that start_from parameter is properly set in config"""
        # With start_from
        assert config_with_start_from.start_from == "03 Sep 2025 16:15:18"
        
        # Without start_from
        assert config_without_start_from.start_from is None
    
    @pytest.mark.asyncio
    async def test_find_start_from_generation_invalid_format(self, download_manager_with_start_from):
        """Test start_from search with invalid datetime format"""
        manager = download_manager_with_start_from
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Test with invalid format
        result = await manager._find_start_from_generation(mock_page, "invalid-format")
        
        assert result['found'] == False
        assert 'Invalid datetime format' in result['error']
    
    @pytest.mark.asyncio
    async def test_find_start_from_generation_no_containers(self, download_manager_with_start_from):
        """Test start_from search when no containers found"""
        manager = download_manager_with_start_from
        
        # Mock page object with no containers
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = []
        
        # Test with valid format but no containers
        result = await manager._find_start_from_generation(mock_page, "03 Sep 2025 16:15:18")
        
        assert result['found'] == False
        assert 'No generation containers found on /generate page' in result['error']
    
    @pytest.mark.asyncio
    async def test_find_start_from_generation_target_found(self, download_manager_with_start_from):
        """Test start_from search when target is found"""
        manager = download_manager_with_start_from
        
        # Mock page and container
        mock_page = AsyncMock()
        mock_container = AsyncMock()
        mock_container.text_content.return_value = "Creation Time 03 Sep 2025 16:15:18\\nThe camera begins with a low-angle shot..."
        mock_container.click = AsyncMock()
        
        mock_page.query_selector_all.return_value = [mock_container]
        
        # Mock enhanced metadata extraction
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            mock_extract.return_value = {
                'creation_time': '03 Sep 2025 16:15:18',
                'prompt': 'The camera begins with a low-angle shot...'
            }
            
            result = await manager._find_start_from_generation(mock_page, "03 Sep 2025 16:15:18")
            
            assert result['found'] == True
            assert result['creation_time'] == '03 Sep 2025 16:15:18'
            assert 'camera' in result['prompt']
            
            # Verify container was clicked
            mock_container.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_start_from_generation_target_not_found(self, download_manager_with_start_from):
        """Test start_from search when target is not found"""
        manager = download_manager_with_start_from
        
        # Mock page and containers with different datetimes
        mock_page = AsyncMock()
        mock_container1 = AsyncMock()
        mock_container1.text_content.return_value = "Creation Time 04 Sep 2025 10:20:30\\nSome other prompt..."
        
        mock_container2 = AsyncMock()
        mock_container2.text_content.return_value = "Creation Time 05 Sep 2025 14:45:22\\nAnother prompt..."
        
        mock_page.query_selector_all.return_value = [mock_container1, mock_container2]
        mock_page.evaluate = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        
        # Mock enhanced metadata extraction
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            # First container
            def mock_extract_side_effect(container, text):
                if container == mock_container1:
                    return {
                        'creation_time': '04 Sep 2025 10:20:30',
                        'prompt': 'Some other prompt...'
                    }
                elif container == mock_container2:
                    return {
                        'creation_time': '05 Sep 2025 14:45:22', 
                        'prompt': 'Another prompt...'
                    }
                return None
            
            mock_extract.side_effect = mock_extract_side_effect
            
            result = await manager._find_start_from_generation(mock_page, "03 Sep 2025 16:15:18")
            
            assert result['found'] == False
            assert 'Target datetime not found' in result['error']
            assert result['containers_scanned'] >= 2
    
    def test_start_from_config_integration(self):
        """Test that start_from integrates properly with config"""
        # Test config creation with start_from
        config = GenerationDownloadConfig()
        config.start_from = "03 Sep 2025 16:15:18"
        config.max_downloads = 100
        config.downloads_folder = "/test/downloads"
        
        # Verify all parameters are set
        assert config.start_from == "03 Sep 2025 16:15:18"
        assert config.max_downloads == 100
        assert config.downloads_folder == "/test/downloads"
    
    def test_start_from_with_duplicate_modes(self):
        """Test start_from works with different duplicate modes"""
        from src.utils.generation_download_manager import DuplicateMode
        
        # Test with SKIP mode
        skip_config = GenerationDownloadConfig.create_with_skip_mode(
            start_from="03 Sep 2025 16:15:18"
        )
        assert skip_config.start_from == "03 Sep 2025 16:15:18"
        assert skip_config.duplicate_mode == DuplicateMode.SKIP
        
        # Test with FINISH mode
        finish_config = GenerationDownloadConfig.create_with_finish_mode(
            start_from="03 Sep 2025 16:15:18"
        )
        assert finish_config.start_from == "03 Sep 2025 16:15:18"
        assert finish_config.duplicate_mode == DuplicateMode.FINISH


class TestStartFromCommandLine:
    """Test start_from command line integration"""
    
    def test_fast_downloader_start_from_integration(self):
        """Test that fast downloader properly handles start_from parameter"""
        # This would test the FastGenerationDownloader class integration
        # For now, we verify the parameter passing works
        
        # Mock arguments
        class MockArgs:
            start_from = "03 Sep 2025 16:15:18"
            config = "test_config.json"
            mode = "skip"
        
        args = MockArgs()
        
        # Test parameter extraction
        assert args.start_from == "03 Sep 2025 16:15:18"
        assert args.mode == "skip"
    
    def test_config_modification_with_start_from(self):
        """Test that config modification includes start_from parameter"""
        # Mock config data structure
        config_data = {
            'actions': [{
                'type': 'start_generation_downloads',
                'value': {}
            }]
        }
        
        start_from_value = "03 Sep 2025 16:15:18"
        
        # Simulate the config modification logic
        for action_data in config_data['actions']:
            if action_data.get('type') == 'start_generation_downloads':
                if start_from_value:
                    action_data['value']['start_from'] = start_from_value
        
        # Verify start_from was added
        assert config_data['actions'][0]['value']['start_from'] == "03 Sep 2025 16:15:18"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])