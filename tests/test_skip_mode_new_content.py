#!/usr/bin/env python3
"""
Test SKIP Mode with NEW content first scenario
Verifies that SKIP mode downloads NEW content before skipping OLD content.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig,
    DuplicateMode
)


class TestSkipModeNewContent:
    """Test SKIP mode handling of new content before old content"""
    
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
            use_exit_scan_strategy=False  # Test traditional mode
        )
    
    @pytest.fixture
    def existing_log_entries(self):
        """Sample existing log entries (old content)"""
        return {
            "29 Aug 2025 16:34:18": {
                "file_id": "#000000183",
                "prompt": "The camera begins with a frontal close-up of the blood witch"
            },
            "29 Aug 2025 15:29:53": {
                "file_id": "#000000187",
                "prompt": "The camera moves to a tight close-up of the lich queen"
            }
        }
    
    @pytest.fixture
    def new_generation_metadata(self):
        """Metadata for a NEW generation (not in log)"""
        return {
            "generation_date": "30 Aug 2025 16:17:57",
            "prompt": "The camera opens with a wide shot of the colossal dragon",
            "prompt_start": "The camera opens with a wide shot of the colossal dragon"
        }
    
    @pytest.fixture
    def old_generation_metadata(self):
        """Metadata for an OLD generation (exists in log)"""
        return {
            "generation_date": "29 Aug 2025 16:34:18",
            "prompt": "The camera begins with a frontal close-up of the blood witch's piercing eyes",
            "prompt_start": "The camera begins with a frontal close-up of the blood witch's piercing eyes"
        }
    
    def test_skip_mode_starts_in_download_mode(self, skip_config, existing_log_entries):
        """Test that SKIP mode starts in download mode, not fast-forward"""
        manager = GenerationDownloadManager(skip_config)
        
        # Mock the log loading
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            initialized = manager.initialize_enhanced_skip_mode()
            
            assert initialized is True
            assert manager.fast_forward_mode is False  # Should NOT start in fast-forward!
            assert hasattr(manager, 'skip_mode_active')
            assert manager.skip_mode_active is True
            assert hasattr(manager, 'existing_log_entries')
            assert len(manager.existing_log_entries) == 2
    
    def test_new_content_gets_downloaded(self, skip_config, existing_log_entries, new_generation_metadata):
        """Test that NEW content is downloaded, not skipped"""
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize with existing log entries
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.initialize_enhanced_skip_mode()
        
        # Check that new content is not a duplicate
        result = asyncio.run(manager._is_still_duplicate(new_generation_metadata))
        assert result is False  # New content should NOT be a duplicate
        
        # Verify fast_forward_to_checkpoint returns "download" for new content
        action = asyncio.run(manager.fast_forward_to_checkpoint(None, "test_thumb"))
        assert action == "download"  # Should download new content
    
    @pytest.mark.asyncio
    async def test_duplicate_activates_fast_forward(self, skip_config, existing_log_entries, old_generation_metadata):
        """Test that finding a duplicate activates fast-forward mode"""
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize with existing log entries
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.initialize_enhanced_skip_mode()
        
        # Mock page for duplicate check
        mock_page = AsyncMock()
        
        # Mock metadata extraction to return old content
        with patch.object(manager, 'extract_metadata_from_page', return_value=old_generation_metadata):
            # Check comprehensive duplicate
            result = await manager.check_comprehensive_duplicate(mock_page, "test_thumb")
            
            # Should detect as duplicate and activate fast-forward
            assert result == "skip"  # Should skip the duplicate
            assert manager.fast_forward_mode is True  # Should activate fast-forward mode
    
    @pytest.mark.asyncio
    async def test_fast_forward_stops_on_new_content(self, skip_config, existing_log_entries):
        """Test that fast-forward mode stops when reaching new content again"""
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize and set up fast-forward mode
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.initialize_enhanced_skip_mode()
            manager.fast_forward_mode = True  # Simulate being in fast-forward after finding duplicate
        
        # Test with old content - should remain in fast-forward
        old_metadata = {
            "generation_date": "29 Aug 2025 15:29:53",
            "prompt_start": "The camera moves to a tight close-up of the lich queen"
        }
        is_old = await manager._is_still_duplicate(old_metadata)
        assert is_old is True  # Should recognize as old content
        
        # Test with new content - should exit fast-forward
        new_metadata = {
            "generation_date": "30 Aug 2025 18:00:00",
            "prompt_start": "A completely new generation prompt"
        }
        is_new = await manager._is_still_duplicate(new_metadata)
        assert is_new is False  # Should recognize as new content
    
    def test_download_order_new_then_old(self, skip_config):
        """Test the correct order: download NEW, skip OLD, download NEW again"""
        manager = GenerationDownloadManager(skip_config)
        
        # Simulated gallery order: [NEW1, NEW2, OLD1, OLD2, NEW3]
        gallery_items = [
            {"date": "30 Aug 2025 18:00:00", "prompt": "New content 1"},
            {"date": "30 Aug 2025 17:00:00", "prompt": "New content 2"},
            {"date": "29 Aug 2025 16:34:18", "prompt": "The camera begins with a frontal close-up"},  # OLD
            {"date": "29 Aug 2025 15:29:53", "prompt": "The camera moves to a tight close-up"},  # OLD
            {"date": "30 Aug 2025 10:00:00", "prompt": "New content 3"}
        ]
        
        existing_log = {
            "29 Aug 2025 16:34:18": {"prompt": "The camera begins with a frontal close-up"},
            "29 Aug 2025 15:29:53": {"prompt": "The camera moves to a tight close-up"}
        }
        
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log):
            manager.initialize_enhanced_skip_mode()
            
            actions = []
            for item in gallery_items:
                metadata = {
                    "generation_date": item["date"],
                    "prompt_start": item["prompt"]
                }
                
                if manager.fast_forward_mode:
                    # In fast-forward, check if still duplicate
                    is_old = asyncio.run(manager._is_still_duplicate(metadata))
                    if is_old:
                        actions.append("skip")
                    else:
                        actions.append("download")
                        manager.fast_forward_mode = False  # Exit fast-forward
                else:
                    # Not in fast-forward, check for duplicates
                    is_duplicate = item["date"] in existing_log
                    if is_duplicate:
                        actions.append("skip")
                        manager.fast_forward_mode = True  # Enter fast-forward
                    else:
                        actions.append("download")
            
            # Expected: download, download, skip, skip, download
            assert actions == ["download", "download", "skip", "skip", "download"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])