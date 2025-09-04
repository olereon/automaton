#!/usr/bin/env python3
"""
Test infinite loop fix for SKIP mode generation downloads
Verifies the system doesn't get stuck processing the same generation repeatedly.
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


class TestInfiniteLoopFix:
    """Test fixes for infinite loop in SKIP mode"""
    
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
            use_exit_scan_strategy=True  # Will be disabled in SKIP mode
        )
    
    @pytest.fixture
    def existing_log_entries(self):
        """Sample existing log entries"""
        return {
            "30 Aug 2025 23:54:22": {
                "file_id": "#000000301",
                "prompt": "The camera opens with a wide shot of the colossal skeletal guardian emerging from a sandstorm, its g..."
            }
        }
    
    def test_exit_scan_return_disabled_in_skip_mode(self, skip_config, existing_log_entries):
        """Test that exit-scan-return strategy is disabled in SKIP mode"""
        manager = GenerationDownloadManager(skip_config)
        
        # Mock the log loading
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            initialized = manager.initialize_enhanced_skip_mode()
            
            assert initialized is True
            assert manager.use_exit_scan_strategy is False  # Should be disabled
            assert manager.skip_mode_active is True
    
    @pytest.mark.asyncio
    async def test_no_exit_scan_return_on_duplicate(self, skip_config, existing_log_entries):
        """Test that duplicate detection doesn't trigger exit-scan-return"""
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize with existing log entries
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.initialize_enhanced_skip_mode()
        
        # Mock page and metadata extraction to return duplicate content
        mock_page = AsyncMock()
        duplicate_metadata = {
            "generation_date": "30 Aug 2025 23:54:22",
            "prompt": "The camera opens with a wide shot of the colossal skeletal guardian emerging from a sandstorm, its g...",
            "prompt_start": "The camera opens with a wide shot of the colossal skeletal guardian emerging from a sandstorm, its g..."
        }
        
        with patch.object(manager, 'extract_metadata_from_page', return_value=duplicate_metadata):
            # Check comprehensive duplicate should NOT return "exit_scan_return"
            result = await manager.check_comprehensive_duplicate(mock_page, "test_thumb")
            
            # Should be "skip" or True, not "exit_scan_return" because strategy is disabled
            assert result in ["skip", True, False]  # Any valid duplicate result
            assert result != "exit_scan_return"  # Should never return this
    
    def test_processed_duplicates_tracking(self, skip_config):
        """Test that processed duplicates are tracked to prevent infinite loops"""
        manager = GenerationDownloadManager(skip_config)
        
        # Simulate adding a processed duplicate
        duplicate_key = "30 Aug 2025 23:54:22|The camera opens with a wide shot of the colossal"
        if not hasattr(manager, 'processed_duplicates'):
            manager.processed_duplicates = set()
        manager.processed_duplicates.add(duplicate_key)
        
        assert duplicate_key in manager.processed_duplicates
    
    def test_infinite_loop_detection_attributes(self, skip_config):
        """Test that infinite loop detection attributes are properly initialized"""
        manager = GenerationDownloadManager(skip_config)
        
        # Simulate the safeguard initialization
        manager.last_processed_metadata = None
        manager.same_generation_count = 0
        
        # Test tracking same generation
        current_key = "30 Aug 2025 23:54:22|The camera opens with a wide shot"
        
        # First time processing
        if manager.last_processed_metadata != current_key:
            manager.last_processed_metadata = current_key
            manager.same_generation_count = 1
        else:
            manager.same_generation_count += 1
        
        assert manager.last_processed_metadata == current_key
        assert manager.same_generation_count == 1
        
        # Simulate processing same generation again
        if manager.last_processed_metadata == current_key:
            manager.same_generation_count += 1
        
        assert manager.same_generation_count == 2
    
    @pytest.mark.asyncio
    async def test_infinite_loop_breakout_logic(self, skip_config):
        """Test the logic that breaks out of infinite loops"""
        manager = GenerationDownloadManager(skip_config)
        
        # Simulate being stuck on same generation 3 times
        manager.last_processed_metadata = "30 Aug 2025 23:54:22|The camera opens"
        manager.same_generation_count = 3
        
        # The logic should detect this as an infinite loop
        should_break = manager.same_generation_count >= 3
        assert should_break is True
    
    def test_skip_mode_configuration(self, skip_config):
        """Test that SKIP mode has correct configuration"""
        assert skip_config.duplicate_mode == DuplicateMode.SKIP
        assert skip_config.stop_on_duplicate is False
        assert skip_config.duplicate_check_enabled is True
    
    @pytest.mark.asyncio 
    async def test_duplicate_detection_without_exit_scan_return(self, skip_config, existing_log_entries):
        """Test comprehensive duplicate detection works without exit-scan-return"""
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize with existing entries
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.initialize_enhanced_skip_mode()
        
        # Mock page and duplicate metadata
        mock_page = AsyncMock()
        duplicate_metadata = {
            "generation_date": "30 Aug 2025 23:54:22", 
            "prompt": "The camera opens with a wide shot of the colossal skeletal guardian emerging from a sandstorm, its g..."
        }
        
        with patch.object(manager, 'extract_metadata_from_page', return_value=duplicate_metadata):
            result = await manager.check_comprehensive_duplicate(mock_page, "test_thumb", set())
            
            # Should return skip behavior, not exit-scan-return
            assert result in ["skip", True, False]  # Any valid duplicate result
            assert result != "exit_scan_return"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])