#!/usr/bin/env python3.11
"""
Test Start From Generation Container Mode
========================================
Tests that start_from feature uses generation container mode when target not found
instead of falling back to thumbnail navigation
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


class TestStartFromGenerationContainerMode:
    """Test suite to verify start_from uses generation container mode as fallback"""
    
    @pytest.fixture
    def config_with_start_from(self):
        """Create config with start_from parameter"""
        config = GenerationDownloadConfig()
        config.start_from = "03 Sep 2025 16:15:18"  # Target that won't be found
        config.max_downloads = 5  # Small limit for testing
        return config
    
    @pytest.fixture
    def download_manager(self, config_with_start_from):
        """Create download manager with start_from config"""
        return GenerationDownloadManager(config_with_start_from)
    
    @pytest.mark.asyncio
    async def test_start_from_target_not_found_triggers_container_mode(self, download_manager):
        """Test that when start_from target is not found, generation container mode is used"""
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Mock _find_start_from_generation to return not found (target not found)
        with patch.object(download_manager, '_find_start_from_generation') as mock_find_start_from:
            mock_find_start_from.return_value = {
                'found': False,
                'error': 'Target datetime not found',
                'containers_scanned': 10
            }
            
            # Mock execute_generation_container_mode
            with patch.object(download_manager, 'execute_generation_container_mode') as mock_container_mode:
                mock_container_mode.return_value = {
                    'success': True,
                    'downloads_completed': 3,
                    'errors': [],
                    'start_time': '2025-09-04T10:00:00',
                    'end_time': '2025-09-04T10:30:00'
                }
                
                # Call run_download_automation
                result = await download_manager.run_download_automation(mock_page)
                
                # Verify _find_start_from_generation was called with correct datetime
                mock_find_start_from.assert_called_once_with(mock_page, "03 Sep 2025 16:15:18")
                
                # Verify execute_generation_container_mode was called (fallback)
                mock_container_mode.assert_called_once()
                
                # Verify result is from generation container mode
                assert result['success'] == True
                assert result['downloads_completed'] == 3
                
                print("✅ Confirmed: start_from target not found triggers generation container mode")
    
    @pytest.mark.asyncio
    async def test_generation_container_mode_finds_containers(self, download_manager):
        """Test that generation container mode can find and process generation containers"""
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Mock generation containers
        mock_container1 = AsyncMock()
        mock_container1.text_content.return_value = "Creation Time 04 Sep 2025 10:20:30\nSome prompt..."
        mock_container1.click = AsyncMock()
        
        mock_container2 = AsyncMock()
        mock_container2.text_content.return_value = "Creation Time 04 Sep 2025 11:15:45\nAnother prompt..."
        mock_container2.click = AsyncMock()
        
        # Mock query_selector_all to return containers only for specific selectors
        def mock_query_selector_all(selector):
            if selector == "div[id$='__0']":
                return [mock_container1]
            elif selector == "div[id$='__1']":
                return [mock_container2]
            else:
                return []  # No containers for other selectors
        
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        mock_page.go_back = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        
        # Mock metadata extraction
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            mock_extract.side_effect = [
                {'creation_time': '04 Sep 2025 10:20:30', 'prompt': 'Some prompt'},
                {'creation_time': '04 Sep 2025 11:15:45', 'prompt': 'Another prompt'}
            ]
            
            # Mock download attempt
            with patch.object(download_manager, '_attempt_download_from_current_position') as mock_download:
                mock_download.return_value = True  # Download succeeds
                
                # Mock browser settings configuration
                with patch.object(download_manager, '_configure_chromium_download_settings') as mock_config:
                    mock_config.return_value = True
                    
                    # Mock initialize_enhanced_skip_mode
                    with patch.object(download_manager, 'initialize_enhanced_skip_mode') as mock_skip:
                        mock_skip.return_value = False
                        
                        # Call execute_generation_container_mode
                        results = {
                            'success': False,
                            'downloads_completed': 0,
                            'errors': [],
                            'start_time': '2025-09-04T10:00:00',
                            'end_time': None
                        }
                        
                        result = await download_manager.execute_generation_container_mode(mock_page, results)
                        
                        # Verify containers were processed
                        assert mock_container1.click.called
                        assert mock_container2.click.called
                        
                        # Verify downloads were attempted
                        assert mock_download.call_count == 2
                        
                        # Verify page navigation
                        assert mock_page.go_back.call_count == 2  # Back after each container
                        
                        # Verify success
                        assert result['success'] == True
                        assert result['downloads_completed'] == 2
                        assert result['total_thumbnails_processed'] == 2
                        
                        print("✅ Confirmed: generation container mode processes containers correctly")
    
    @pytest.mark.asyncio
    async def test_generation_container_mode_no_containers_found(self, download_manager):
        """Test that generation container mode handles case with no containers"""
        
        # Mock page object
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = []  # No containers found
        
        # Mock browser settings configuration
        with patch.object(download_manager, '_configure_chromium_download_settings') as mock_config:
            mock_config.return_value = True
            
            # Mock initialize_enhanced_skip_mode
            with patch.object(download_manager, 'initialize_enhanced_skip_mode') as mock_skip:
                mock_skip.return_value = False
                
                # Call execute_generation_container_mode
                results = {
                    'success': False,
                    'downloads_completed': 0,
                    'errors': [],
                    'start_time': '2025-09-04T10:00:00',
                    'end_time': None
                }
                
                result = await download_manager.execute_generation_container_mode(mock_page, results)
                
                # Verify failure when no containers
                assert result['success'] == False
                assert result['downloads_completed'] == 0
                assert 'No generation containers available for processing' in result['errors']
                
                print("✅ Confirmed: generation container mode handles no containers gracefully")
    
    def test_start_from_flow_logic(self):
        """Test the logical flow when start_from is provided"""
        
        # Read the generation_download_manager.py file
        manager_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'utils', 'generation_download_manager.py')
        
        with open(manager_file, 'r') as f:
            content = f.read()
        
        # Find the run_download_automation method
        method_start = content.find('async def run_download_automation')
        method_end = content.find('\n    async def ', method_start + 1)
        if method_end == -1:
            method_end = len(content)
        method_content = content[method_start:method_end]
        
        # Verify the new flow logic is present
        assert 'if self.config.start_from:' in method_content
        assert 'execute_generation_container_mode' in method_content
        assert 'Since start_from was specified, staying on /generate page' in method_content
        
        # Verify that when start_from target is not found, it doesn't continue with normal flow
        # The method should return directly after calling execute_generation_container_mode
        lines = method_content.split('\n')
        container_mode_line = None
        for i, line in enumerate(lines):
            if 'execute_generation_container_mode' in line and 'return await' in line:
                container_mode_line = i
                break
        
        assert container_mode_line is not None, "execute_generation_container_mode should be called with return await"
        
        print("✅ Confirmed: start_from flow logic correctly uses generation container mode as fallback")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])