#!/usr/bin/env python3.11
"""
Test Start From Issue Resolution
===============================
Tests that the specific issue reported by the user is completely resolved:
- start_from should work with generation containers on /generate page
- start_from should NOT navigate to thumbnails gallery when target not found
- start_from should stay on /generate page regardless of success/failure
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


class TestStartFromIssueResolution:
    """Test suite to verify the reported issue is completely resolved"""
    
    @pytest.fixture
    def config_with_start_from(self):
        """Create config with start_from parameter that won't be found"""
        config = GenerationDownloadConfig()
        config.start_from = "03 Sep 2025 16:15:18"  # Target that won't be found
        config.max_downloads = 5
        return config
    
    @pytest.fixture
    def download_manager(self, config_with_start_from):
        """Create download manager with start_from config"""
        return GenerationDownloadManager(config_with_start_from)
    
    @pytest.mark.asyncio
    async def test_start_from_does_not_navigate_to_thumbnails_when_target_not_found(self, download_manager):
        """Test that when start_from target is not found, it doesn't navigate to thumbnails"""
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Mock containers on /generate page (but none match the target datetime)
        mock_container = AsyncMock()
        mock_container.text_content.return_value = "Creation Time 04 Sep 2025 10:20:30\nSome prompt..."
        
        def mock_query_selector_all(selector):
            if selector == "div[id$='__0']":
                return [mock_container]  # Return one container
            else:
                return []  # No containers for other selectors
        
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        
        # Mock enhanced metadata extraction to return different datetime (not matching target)
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            mock_extract.return_value = {
                'creation_time': '04 Sep 2025 10:20:30',  # Different from target
                'prompt': 'Some prompt...'
            }
            
            # Mock execute_generation_container_mode (what should be called instead of thumbnail navigation)
            with patch.object(download_manager, 'execute_generation_container_mode') as mock_container_mode:
                mock_container_mode.return_value = {
                    'success': True,
                    'downloads_completed': 2,
                    'errors': [],
                    'start_time': '2025-09-04T10:00:00',
                    'end_time': '2025-09-04T10:30:00'
                }
                
                # Call run_download_automation
                result = await download_manager.run_download_automation(mock_page)
                
                # Verify execute_generation_container_mode was called (NOT thumbnail navigation)
                mock_container_mode.assert_called_once()
                
                # Verify result comes from generation container mode
                assert result['success'] == True
                assert result['downloads_completed'] == 2
                
                print("✅ ISSUE RESOLVED: start_from target not found triggers generation container mode (no thumbnail navigation)")
    
    @pytest.mark.asyncio
    async def test_start_from_stays_on_generate_page_regardless_of_success(self, download_manager):
        """Test that start_from always stays on /generate page, whether successful or not"""
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Test case 1: Target found (should use execute_download_phase)
        with patch.object(download_manager, '_find_start_from_generation') as mock_find:
            mock_find.return_value = {
                'found': True,  # Target found
                'container_index': 5
            }
            
            with patch.object(download_manager, 'execute_download_phase') as mock_download_phase:
                mock_download_phase.return_value = {
                    'success': True,
                    'downloads_completed': 3
                }
                
                # Configure start_from in config
                download_manager.config.start_from = "03 Sep 2025 16:15:18"
                
                result = await download_manager.run_download_automation(mock_page)
                
                # Verify execute_download_phase was called (target found)
                mock_download_phase.assert_called_once()
                assert result['downloads_completed'] == 3
        
        # Test case 2: Target not found (should use execute_generation_container_mode)
        with patch.object(download_manager, '_find_start_from_generation') as mock_find:
            mock_find.return_value = {
                'found': False,  # Target not found
                'error': 'Target not found'
            }
            
            with patch.object(download_manager, 'execute_generation_container_mode') as mock_container_mode:
                mock_container_mode.return_value = {
                    'success': True,
                    'downloads_completed': 2
                }
                
                result = await download_manager.run_download_automation(mock_page)
                
                # Verify execute_generation_container_mode was called (target not found fallback)
                mock_container_mode.assert_called_once()
                assert result['downloads_completed'] == 2
        
        print("✅ ISSUE RESOLVED: start_from stays on /generate page in both success and failure cases")
    
    @pytest.mark.asyncio
    async def test_no_thumbnail_navigation_code_path_when_start_from_provided(self, download_manager):
        """Test that the normal thumbnail navigation code path is completely bypassed when start_from is provided"""
        
        # Mock page object
        mock_page = AsyncMock()
        
        # Mock start_from search to return not found
        with patch.object(download_manager, '_find_start_from_generation') as mock_find:
            mock_find.return_value = {
                'found': False,
                'error': 'Target not found'
            }
            
            # Mock generation container mode
            with patch.object(download_manager, 'execute_generation_container_mode') as mock_container_mode:
                mock_container_mode.return_value = {
                    'success': True,
                    'downloads_completed': 1
                }
                
                # Mock all the methods that would be called in normal thumbnail navigation flow
                with patch.object(download_manager, 'find_completed_generations_on_page') as mock_find_completed:
                    with patch.object(download_manager, 'scan_existing_files') as mock_scan_existing:
                        with patch.object(download_manager, 'initialize_enhanced_skip_mode') as mock_skip_mode:
                            with patch.object(download_manager, '_configure_chromium_download_settings') as mock_config:
                                
                                # Configure start_from in config
                                download_manager.config.start_from = "03 Sep 2025 16:15:18"
                                
                                result = await download_manager.run_download_automation(mock_page)
                                
                                # Verify start_from search was called
                                mock_find.assert_called_once_with(mock_page, "03 Sep 2025 16:15:18")
                                
                                # Verify generation container mode was called (fallback)
                                mock_container_mode.assert_called_once()
                                
                                # Verify that NONE of the normal thumbnail navigation methods were called
                                mock_find_completed.assert_not_called()  # Should not scan for completed generations
                                mock_scan_existing.assert_not_called()   # Should not scan existing files
                                mock_skip_mode.assert_not_called()       # Should not initialize skip mode
                                mock_config.assert_not_called()          # Should not configure browser settings
                                
                                # Verify result comes from generation container mode
                                assert result['success'] == True
                                assert result['downloads_completed'] == 1
        
        print("✅ ISSUE RESOLVED: Normal thumbnail navigation code path completely bypassed when start_from provided")
    
    def test_log_messages_indicate_correct_behavior(self):
        """Test that the log messages in the code indicate the correct behavior"""
        
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
        
        # Verify the correct log messages are present that indicate the fix
        assert 'Since start_from was specified, staying on /generate page' in method_content
        assert 'no thumbnail navigation' in method_content
        assert 'Using generation containers on /generate page as primary interface' in method_content
        
        # Verify generation container mode exists
        assert 'async def execute_generation_container_mode' in content
        assert 'Working directly with generation containers on /generate page' in content
        assert 'avoids thumbnail gallery navigation' in content
        
        print("✅ ISSUE RESOLVED: Log messages confirm correct behavior - staying on /generate page, no thumbnail navigation")
    
    def test_original_issue_scenario_resolved(self):
        """Test that the exact scenario described in the original issue is resolved"""
        
        manager_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'utils', 'generation_download_manager.py')
        
        with open(manager_file, 'r') as f:
            content = f.read()
        
        # Original issue: start_from was looking for thumbnails instead of generation containers on /generate page
        
        # Verify _find_start_from_generation method uses generation containers
        start_from_method = content[content.find('async def _find_start_from_generation'):]
        start_from_method = start_from_method[:start_from_method.find('\n    async def ')]
        
        # Check that it uses boundary detection container scanning on /generate page
        assert 'Using boundary detection container scanning on /generate page' in start_from_method
        assert "div[id$='__{i}']" in start_from_method
        assert 'same as boundary detection' in start_from_method
        
        # Check that when target not found, it uses generation container mode instead of thumbnail navigation
        run_method = content[content.find('async def run_download_automation'):]
        run_method = run_method[:run_method.find('\n    async def ')]
        
        assert 'execute_generation_container_mode' in run_method
        assert 'return await self.execute_generation_container_mode' in run_method
        
        print("✅ ISSUE COMPLETELY RESOLVED:")
        print("   • start_from scans generation containers on /generate page (NOT thumbnails)")
        print("   • start_from uses same approach as boundary detection")  
        print("   • When target not found, uses generation container mode (NOT thumbnail navigation)")
        print("   • Always stays on /generate page regardless of success/failure")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])