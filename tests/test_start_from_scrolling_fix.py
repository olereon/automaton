#!/usr/bin/env python3.11
"""
Test Start From Scrolling Fix
=============================
Tests that start_from feature uses the correct BoundaryScrollManager scrolling methods
instead of simple window.scrollBy()
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


class TestStartFromScrollingFix:
    """Test suite to verify start_from uses BoundaryScrollManager scrolling"""
    
    @pytest.fixture
    def config_with_start_from(self):
        """Create config with start_from parameter"""
        config = GenerationDownloadConfig()
        config.start_from = "03 Sep 2025 16:15:18"
        config.scroll_amount = 2000  # Standard scroll amount
        return config
    
    @pytest.fixture
    def download_manager(self, config_with_start_from):
        """Create download manager with start_from config"""
        return GenerationDownloadManager(config_with_start_from)
    
    @pytest.mark.asyncio
    async def test_start_from_initializes_boundary_scroll_manager(self, download_manager):
        """Test that start_from search initializes BoundaryScrollManager"""
        
        # Mock page object
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = []  # No containers found
        
        # Ensure boundary_scroll_manager starts as None
        assert download_manager.boundary_scroll_manager is None
        
        # Call start_from search
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced'):
            result = await download_manager._find_start_from_generation(mock_page, "03 Sep 2025 16:15:18")
        
        # Verify boundary_scroll_manager was initialized
        assert download_manager.boundary_scroll_manager is not None
        assert result['found'] == False  # Expected since no containers
        assert 'No generation containers found on /generate page' in result['error']
    
    @pytest.mark.asyncio
    async def test_start_from_uses_boundary_scroll_manager_for_scrolling(self, download_manager):
        """Test that start_from search uses BoundaryScrollManager.perform_scroll_with_fallback()"""
        
        # Mock page and containers
        mock_page = AsyncMock()
        mock_container = AsyncMock()
        mock_container.text_content.return_value = "Creation Time 04 Sep 2025 10:20:30\\nSome other prompt..."
        
        # Return containers for specific selector, then empty to trigger scrolling
        def mock_query_selector_all(selector):
            if selector == "div[id$='__0']":
                return [mock_container]  # Return container for first selector only
            else:
                return []  # No containers for other selectors
        
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        
        # Mock BoundaryScrollManager
        mock_boundary_scroll_manager = AsyncMock()
        mock_scroll_result = Mock()
        mock_scroll_result.success = True
        mock_scroll_result.scroll_distance = 2000
        mock_scroll_result.method_name = "Element.scrollIntoView()"
        mock_scroll_result.error_message = ""
        
        mock_boundary_scroll_manager.perform_scroll_with_fallback.return_value = mock_scroll_result
        
        # Mock enhanced metadata extraction
        with patch('src.utils.generation_download_manager.extract_container_metadata_enhanced') as mock_extract:
            mock_extract.return_value = {
                'creation_time': '04 Sep 2025 10:20:30',
                'prompt': 'Some other prompt...'
            }
            
            # Mock the boundary scroll manager initialization
            with patch.object(download_manager, 'initialize_boundary_scroll_manager'):
                download_manager.boundary_scroll_manager = mock_boundary_scroll_manager
                
                # Call start_from search (target not found to trigger scrolling)
                result = await download_manager._find_start_from_generation(mock_page, "03 Sep 2025 16:15:18")
                
                # Verify BoundaryScrollManager.perform_scroll_with_fallback was called
                assert mock_boundary_scroll_manager.perform_scroll_with_fallback.called
                
                # Verify it was called with the correct scroll amount
                call_args = mock_boundary_scroll_manager.perform_scroll_with_fallback.call_args
                assert call_args[1]['target_distance'] == 2000
                
                assert result['found'] == False  # Target not found as expected
                assert result['containers_scanned'] >= 1
    
    @pytest.mark.asyncio 
    async def test_boundary_scroll_manager_methods_are_used(self, download_manager):
        """Test that the BoundaryScrollManager uses verified scroll methods"""
        
        # Mock page
        mock_page = AsyncMock()
        
        # Initialize boundary scroll manager
        download_manager.initialize_boundary_scroll_manager(mock_page)
        
        # Verify boundary scroll manager was created
        assert download_manager.boundary_scroll_manager is not None
        assert download_manager.boundary_scroll_manager.page == mock_page
        
        # Verify the manager has the correct scroll methods
        assert hasattr(download_manager.boundary_scroll_manager, 'scroll_method_1_element_scrollintoview')
        assert hasattr(download_manager.boundary_scroll_manager, 'scroll_method_2_container_scrolltop') 
        assert hasattr(download_manager.boundary_scroll_manager, 'perform_scroll_with_fallback')
    
    def test_scrolling_method_changed_from_window_scrollby(self):
        """Test that we're no longer using simple window.scrollBy()"""
        
        # Read the generation_download_manager.py file
        manager_file = os.path.join(os.path.dirname(__file__), '..', 'src', 'utils', 'generation_download_manager.py')
        
        with open(manager_file, 'r') as f:
            content = f.read()
        
        # Check that within _find_start_from_generation method, we're using BoundaryScrollManager
        start_from_method = content[content.find('async def _find_start_from_generation'):content.find('async def', content.find('async def _find_start_from_generation') + 1)]
        
        # Verify BoundaryScrollManager usage
        assert 'boundary_scroll_manager.perform_scroll_with_fallback' in start_from_method
        assert 'Using BoundaryScrollManager verified scroll methods' in start_from_method
        
        # Verify old window.scrollBy method is NOT used in start_from
        assert 'window.scrollBy(' not in start_from_method
        
        print("✅ Confirmed: start_from now uses BoundaryScrollManager instead of window.scrollBy()")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])