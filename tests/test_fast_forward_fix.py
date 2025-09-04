#!/usr/bin/env python3
"""
Test Fast-Forward Mode Fix for Enhanced SKIP Mode
Tests that fast-forward now properly clicks thumbnails before checking metadata.
"""

import pytest
import asyncio
pytest_plugins = ('pytest_asyncio',)
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig,
    GenerationDownloadLogger,
    DuplicateMode
)


class TestFastForwardFix:
    """Test the fast-forward mode fix"""
    
    @pytest.fixture
    def skip_config(self, tmp_path):
        """Create a SKIP mode configuration"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            max_downloads=50,
            duplicate_mode=DuplicateMode.SKIP,
            stop_on_duplicate=False,
            duplicate_check_enabled=True,
            use_exit_scan_strategy=False  # Test traditional fast-forward
        )
    
    @pytest.fixture
    def checkpoint_data(self):
        """Sample checkpoint data"""
        return {
            "file_id": "#000000187",
            "generation_date": "29 Aug 2025 15:29:53",
            "prompt": "The camera moves to a tight close-up of the lich queen's skeletal face"
        }
    
    @pytest.fixture
    def manager_with_checkpoint(self, skip_config, checkpoint_data):
        """Create manager with checkpoint data loaded"""
        manager = GenerationDownloadManager(skip_config)
        manager.checkpoint_data = checkpoint_data
        manager.fast_forward_mode = True
        manager.checkpoint_found = False
        return manager
    
    def test_fast_forward_returns_check_after_click(self, manager_with_checkpoint):
        """Test that fast_forward_to_checkpoint returns 'check_after_click' in fast-forward mode"""
        # When in fast-forward mode, it should return "check_after_click"
        result = asyncio.run(manager_with_checkpoint.fast_forward_to_checkpoint(None, "test_thumb"))
        assert result == "check_after_click"
    
    @pytest.mark.asyncio
    async def test_check_if_checkpoint_after_click_extracts_metadata(self, manager_with_checkpoint):
        """Test that check_if_checkpoint_after_click properly extracts metadata after click"""
        # Mock page with visible metadata after click
        mock_page = AsyncMock()
        
        # Mock creation time element (visible after click)
        mock_time_element = AsyncMock()
        mock_time_element.is_visible = AsyncMock(return_value=True)
        mock_time_element.text_content = AsyncMock(return_value="29 Aug 2025 15:29:53")
        
        # Mock prompt element (visible after click)
        mock_prompt_element = AsyncMock()
        mock_prompt_element.is_visible = AsyncMock(return_value=True)
        mock_prompt_element.text_content = AsyncMock(return_value="The camera moves to a tight close-up of the lich queen's skeletal face")
        
        # Setup locator returns
        def locator_side_effect(selector):
            if "Creation Time" in selector or "bZTHAM" in selector:
                return Mock(first=mock_time_element)
            elif "dnESm" in selector or "prompt" in selector:
                return Mock(first=mock_prompt_element)
            return Mock(first=AsyncMock(is_visible=AsyncMock(return_value=False)))
        
        mock_page.locator = Mock(side_effect=locator_side_effect)
        mock_page.wait_for_timeout = AsyncMock()
        
        # Test checking after click
        result = await manager_with_checkpoint.check_if_checkpoint_after_click(mock_page, "test_thumb")
        
        # Should find the checkpoint and return "skip_checkpoint"
        assert result == "skip_checkpoint"
        assert manager_with_checkpoint.checkpoint_found is True
        assert manager_with_checkpoint.fast_forward_mode is False
    
    @pytest.mark.asyncio
    async def test_check_if_checkpoint_continues_on_non_match(self, manager_with_checkpoint):
        """Test that non-matching metadata continues fast-forward"""
        # Mock page with different metadata
        mock_page = AsyncMock()
        
        mock_time_element = AsyncMock()
        mock_time_element.is_visible = AsyncMock(return_value=True)
        mock_time_element.text_content = AsyncMock(return_value="30 Aug 2025 10:00:00")  # Different time
        
        mock_prompt_element = AsyncMock()
        mock_prompt_element.is_visible = AsyncMock(return_value=True)
        mock_prompt_element.text_content = AsyncMock(return_value="Different prompt text")
        
        def locator_side_effect(selector):
            if "Creation Time" in selector or "bZTHAM" in selector:
                return Mock(first=mock_time_element)
            elif "dnESm" in selector or "prompt" in selector:
                return Mock(first=mock_prompt_element)
            return Mock(first=AsyncMock(is_visible=AsyncMock(return_value=False)))
        
        mock_page.locator = Mock(side_effect=locator_side_effect)
        mock_page.wait_for_timeout = AsyncMock()
        
        # Test checking non-matching thumbnail
        result = await manager_with_checkpoint.check_if_checkpoint_after_click(mock_page, "test_thumb")
        
        # Should continue fast-forward
        assert result == "skip"
        assert manager_with_checkpoint.checkpoint_found is False
        assert manager_with_checkpoint.fast_forward_mode is True
    
    @pytest.mark.asyncio
    async def test_download_single_generation_robust_with_fix(self, manager_with_checkpoint):
        """Test that download_single_generation_robust properly handles the new flow"""
        # Mock thumbnail info
        thumbnail_info = {
            'element': AsyncMock(),
            'unique_id': 'test_thumb',
            'position': 1
        }
        
        # Mock page
        mock_page = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        
        # Mock the thumbnail click
        with patch.object(manager_with_checkpoint, '_robust_thumbnail_click') as mock_click:
            mock_click.return_value = True
            
            # Mock metadata extraction after click
            with patch.object(manager_with_checkpoint, 'check_if_checkpoint_after_click') as mock_check:
                mock_check.return_value = "skip"  # Not the checkpoint
                
                # Run the download function
                result = await manager_with_checkpoint.download_single_generation_robust(
                    mock_page, thumbnail_info
                )
                
                # Should skip this thumbnail
                assert result is True
                
                # Verify click was called
                mock_click.assert_called_once()
                
                # Verify checkpoint was checked after click
                mock_check.assert_called_once_with(mock_page, 'test_thumb')
    
    @pytest.mark.asyncio
    async def test_checkpoint_found_stops_fast_forward(self, manager_with_checkpoint):
        """Test that finding checkpoint stops fast-forward mode"""
        # Mock page with matching checkpoint data
        mock_page = AsyncMock()
        
        mock_time_element = AsyncMock()
        mock_time_element.is_visible = AsyncMock(return_value=True)
        mock_time_element.text_content = AsyncMock(return_value="29 Aug 2025 15:29:53")
        
        mock_prompt_element = AsyncMock()
        mock_prompt_element.is_visible = AsyncMock(return_value=True)
        mock_prompt_element.text_content = AsyncMock(return_value="The camera moves to a tight close-up of the lich queen's skeletal face and more text here")
        
        def locator_side_effect(selector):
            if "Creation Time" in selector or "bZTHAM" in selector:
                return Mock(first=mock_time_element)
            elif "dnESm" in selector or "prompt" in selector:
                return Mock(first=mock_prompt_element)
            return Mock(first=AsyncMock(is_visible=AsyncMock(return_value=False)))
        
        mock_page.locator = Mock(side_effect=locator_side_effect)
        mock_page.wait_for_timeout = AsyncMock()
        
        # Verify initial state
        assert manager_with_checkpoint.fast_forward_mode is True
        assert manager_with_checkpoint.checkpoint_found is False
        
        # Check checkpoint
        result = await manager_with_checkpoint.check_if_checkpoint_after_click(mock_page, "checkpoint_thumb")
        
        # Should find checkpoint and stop fast-forward
        assert result == "skip_checkpoint"
        assert manager_with_checkpoint.fast_forward_mode is False
        assert manager_with_checkpoint.checkpoint_found is True
        
        # Next thumbnail should download normally
        next_action = await manager_with_checkpoint.fast_forward_to_checkpoint(mock_page, "next_thumb")
        assert next_action == "download"


if __name__ == "__main__":
    # Run with asyncio event loop
    import sys
    sys.exit(pytest.main([__file__, "-v", "--asyncio-mode=auto"]))