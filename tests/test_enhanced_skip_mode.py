#!/usr/bin/env python3
"""
Test Enhanced SKIP Mode Functionality
Tests for the smart checkpoint resume feature in generation downloads.
"""

import pytest
import asyncio
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


class TestEnhancedSkipMode:
    """Test Enhanced SKIP mode functionality"""
    
    @pytest.fixture
    def skip_config(self, tmp_path):
        """Create a SKIP mode configuration"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            max_downloads=50,
            duplicate_mode=DuplicateMode.SKIP,
            stop_on_duplicate=False,
            duplicate_check_enabled=True
        )
    
    @pytest.fixture
    def finish_config(self, tmp_path):
        """Create a FINISH mode configuration for comparison"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            max_downloads=50,
            duplicate_mode=DuplicateMode.FINISH,
            stop_on_duplicate=True,
            duplicate_check_enabled=True
        )
    
    @pytest.fixture
    def sample_log_entries(self):
        """Sample log entries for testing"""
        return [
            {
                "file_id": "#000000001",
                "generation_date": "29 Aug 2025 10:15:30",
                "prompt": "A cinematic shot of a futuristic city with towering skyscrapers and flying cars"
            },
            {
                "file_id": "#000000002", 
                "generation_date": "29 Aug 2025 09:45:20",
                "prompt": "A serene mountain landscape at sunset with golden light reflecting on a pristine lake"
            },
            {
                "file_id": "#000000003",
                "generation_date": "28 Aug 2025 14:20:10", 
                "prompt": "An underwater scene with colorful coral reefs and tropical fish swimming gracefully"
            }
        ]
    
    def test_enhanced_skip_mode_initialization(self, skip_config, sample_log_entries):
        """Test that Enhanced SKIP mode initializes correctly"""
        manager = GenerationDownloadManager(skip_config)
        
        # Mock the log reading
        with patch.object(manager.logger, 'get_last_log_entry') as mock_get_last:
            mock_get_last.return_value = sample_log_entries[0]
            
            # Initialize enhanced skip mode
            result = manager.initialize_enhanced_skip_mode()
            
            assert result is True
            assert manager.fast_forward_mode is True
            assert manager.checkpoint_found is False
            assert manager.checkpoint_data == sample_log_entries[0]
    
    def test_enhanced_skip_mode_not_activated_for_finish_mode(self, finish_config):
        """Test that Enhanced SKIP mode does not activate for FINISH mode"""
        manager = GenerationDownloadManager(finish_config)
        
        # Should not activate for FINISH mode
        result = manager.initialize_enhanced_skip_mode()
        
        assert result is False
        assert not hasattr(manager, 'fast_forward_mode') or manager.fast_forward_mode is False
    
    def test_enhanced_skip_mode_no_checkpoint(self, skip_config):
        """Test Enhanced SKIP mode when no checkpoint is available"""
        manager = GenerationDownloadManager(skip_config)
        
        # Mock empty log
        with patch.object(manager.logger, 'get_last_log_entry') as mock_get_last:
            mock_get_last.return_value = None
            
            result = manager.initialize_enhanced_skip_mode()
            
            assert result is False
            assert not hasattr(manager, 'fast_forward_mode') or manager.fast_forward_mode is False
    
    @pytest.mark.asyncio
    async def test_fast_forward_to_checkpoint_skip_action(self, skip_config, sample_log_entries):
        """Test fast-forward returns skip action for non-matching thumbnails"""
        manager = GenerationDownloadManager(skip_config)
        manager.fast_forward_mode = True
        manager.checkpoint_found = False
        manager.checkpoint_data = sample_log_entries[0]
        
        # Mock page and metadata extraction
        mock_page = AsyncMock()
        
        # Mock metadata that doesn't match checkpoint
        non_matching_metadata = {
            "generation_date": "30 Aug 2025 11:30:00",
            "prompt_start": "A different prompt that doesn't match",
            "thumbnail_id": "thumbnail_1"
        }
        
        with patch.object(manager, '_extract_metadata_fast') as mock_extract:
            mock_extract.return_value = non_matching_metadata
            
            action = await manager.fast_forward_to_checkpoint(mock_page, "thumbnail_1")
            
            assert action == "skip"
            assert manager.fast_forward_mode is True  # Still in fast-forward mode
            assert manager.checkpoint_found is False
    
    @pytest.mark.asyncio 
    async def test_fast_forward_to_checkpoint_found_action(self, skip_config, sample_log_entries):
        """Test fast-forward returns skip_checkpoint action when checkpoint is found"""
        manager = GenerationDownloadManager(skip_config)
        manager.fast_forward_mode = True
        manager.checkpoint_found = False
        manager.checkpoint_data = sample_log_entries[0]
        
        # Mock page and metadata extraction
        mock_page = AsyncMock()
        
        # Mock metadata that matches checkpoint
        matching_metadata = {
            "generation_date": "29 Aug 2025 10:15:30",  # Matches checkpoint
            "prompt_start": "A cinematic shot of a futuristic city",  # Matches checkpoint start
            "thumbnail_id": "thumbnail_15"
        }
        
        with patch.object(manager, '_extract_metadata_fast') as mock_extract:
            with patch.object(manager, '_is_checkpoint_match') as mock_match:
                mock_extract.return_value = matching_metadata
                mock_match.return_value = True
                
                action = await manager.fast_forward_to_checkpoint(mock_page, "thumbnail_15")
                
                assert action == "skip_checkpoint"
                assert manager.fast_forward_mode is False  # Switched off
                assert manager.checkpoint_found is True
    
    @pytest.mark.asyncio
    async def test_extract_metadata_fast(self, skip_config):
        """Test fast metadata extraction for checkpoint comparison"""
        manager = GenerationDownloadManager(skip_config)
        
        # Mock page with elements
        mock_page = AsyncMock()
        mock_element = AsyncMock()
        mock_element.is_visible = AsyncMock(return_value=True)
        mock_element.text_content = AsyncMock(return_value="29 Aug 2025 10:15:30")
        
        mock_page.locator.return_value.first = mock_element
        
        # Mock prompt element
        mock_prompt_element = AsyncMock()
        mock_prompt_element.is_visible = AsyncMock(return_value=True) 
        mock_prompt_element.text_content = AsyncMock(return_value="A cinematic shot of a futuristic city")
        
        # Set up the locator to return different elements for different selectors
        def mock_locator(selector):
            mock_loc = AsyncMock()
            if "Creation Time" in selector:
                mock_loc.first = mock_element
            else:
                mock_loc.first = mock_prompt_element
            return mock_loc
        
        mock_page.locator = mock_locator
        
        result = await manager._extract_metadata_fast(mock_page, "thumbnail_1")
        
        assert result is not None
        assert result["generation_date"] == "29 Aug 2025 10:15:30"
        assert result["prompt_start"] == "A cinematic shot of a futuristic city"
        assert result["thumbnail_id"] == "thumbnail_1"
    
    def test_checkpoint_match_creation_time(self, skip_config, sample_log_entries):
        """Test checkpoint matching based on creation time AND prompt similarity"""
        manager = GenerationDownloadManager(skip_config)
        
        current_metadata = {
            "generation_date": "29 Aug 2025 10:15:30",
            "prompt_start": "A cinematic shot of a futuristic city with towering",  # Must match prompt start
            "thumbnail_id": "thumbnail_1"
        }
        
        # Should match the first sample entry (both time AND prompt match)
        result = manager._is_checkpoint_match(current_metadata, sample_log_entries[0])
        
        assert result is True
    
    def test_checkpoint_match_different_time(self, skip_config, sample_log_entries):
        """Test checkpoint matching with different creation time"""
        manager = GenerationDownloadManager(skip_config)
        
        current_metadata = {
            "generation_date": "30 Aug 2025 11:30:00",  # Different time
            "prompt_start": "A cinematic shot of a futuristic city",
            "thumbnail_id": "thumbnail_1"
        }
        
        # Should not match
        result = manager._is_checkpoint_match(current_metadata, sample_log_entries[0])
        
        assert result is False
    
    def test_checkpoint_match_time_same_prompt_different(self, skip_config, sample_log_entries):
        """Test checkpoint matching when time matches but prompt is very different"""
        manager = GenerationDownloadManager(skip_config)
        
        current_metadata = {
            "generation_date": "29 Aug 2025 10:15:30",  # Same time
            "prompt_start": "A completely different scene with dragons",  # Very different prompt
            "thumbnail_id": "thumbnail_1"
        }
        
        # The implementation requires BOTH time AND prompt similarity for robustness
        # Time match alone is not sufficient - this prevents false positives
        result = manager._is_checkpoint_match(current_metadata, sample_log_entries[0])
        
        # Should return False because prompt is completely different
        assert result is False
    
    @pytest.mark.asyncio
    async def test_download_single_generation_robust_fast_forward_skip(self, skip_config, sample_log_entries):
        """Test that download_single_generation_robust respects fast-forward skip action"""
        manager = GenerationDownloadManager(skip_config)
        manager.fast_forward_mode = True
        manager.checkpoint_found = False
        manager.checkpoint_data = sample_log_entries[0]
        
        mock_page = AsyncMock()
        thumbnail_info = {
            'element': AsyncMock(),
            'unique_id': 'thumbnail_5',
            'position': 5
        }
        
        # Mock fast_forward_to_checkpoint to return "skip"
        with patch.object(manager, 'fast_forward_to_checkpoint') as mock_fast_forward:
            mock_fast_forward.return_value = "skip"
            
            result = await manager.download_single_generation_robust(mock_page, thumbnail_info)
            
            assert result is True  # Should return True for skip
            mock_fast_forward.assert_called_once_with(mock_page, 'thumbnail_5')
    
    @pytest.mark.asyncio
    async def test_download_single_generation_robust_fast_forward_checkpoint(self, skip_config, sample_log_entries):
        """Test that download_single_generation_robust respects fast-forward checkpoint action"""
        manager = GenerationDownloadManager(skip_config)
        manager.fast_forward_mode = True
        manager.checkpoint_found = False
        manager.checkpoint_data = sample_log_entries[0]
        
        mock_page = AsyncMock()
        thumbnail_info = {
            'element': AsyncMock(),
            'unique_id': 'thumbnail_checkpoint',
            'position': 15
        }
        
        # Mock fast_forward_to_checkpoint to return "skip_checkpoint"
        with patch.object(manager, 'fast_forward_to_checkpoint') as mock_fast_forward:
            mock_fast_forward.return_value = "skip_checkpoint"
            
            result = await manager.download_single_generation_robust(mock_page, thumbnail_info)
            
            assert result is True  # Should return True for checkpoint skip
            mock_fast_forward.assert_called_once_with(mock_page, 'thumbnail_checkpoint')
    
    @pytest.mark.asyncio
    async def test_download_single_generation_fast_forward_modes(self, skip_config, sample_log_entries):
        """Test that download_single_generation also respects fast-forward modes"""
        manager = GenerationDownloadManager(skip_config)
        manager.fast_forward_mode = True
        manager.checkpoint_found = False
        
        mock_page = AsyncMock()
        
        # Test skip action
        with patch.object(manager, 'fast_forward_to_checkpoint') as mock_fast_forward:
            mock_fast_forward.return_value = "skip"
            
            result = await manager.download_single_generation(mock_page, 10)
            
            assert result is True
            mock_fast_forward.assert_called_once_with(mock_page, "thumbnail_10")
    
    def test_get_last_log_entry_integration(self, skip_config, tmp_path):
        """Test integration with GenerationDownloadLogger.get_last_log_entry"""
        manager = GenerationDownloadManager(skip_config)
        
        # Create a sample log file
        log_file = tmp_path / "logs" / "generation_downloads.txt"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        log_content = """#000000001
29 Aug 2025 10:15:30
A cinematic shot of a futuristic city with towering skyscrapers
========================================
#000000002  
29 Aug 2025 09:45:20
A serene mountain landscape at sunset
========================================
"""
        log_file.write_text(log_content)
        
        # Test getting last log entry
        last_entry = manager.logger.get_last_log_entry()
        
        assert last_entry is not None
        assert last_entry["generation_date"] == "29 Aug 2025 10:15:30"
        assert "futuristic city" in last_entry["prompt"]
        assert last_entry["file_id"] == "#000000001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])