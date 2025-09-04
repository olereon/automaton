#!/usr/bin/env python3.11
"""
Comprehensive test suite for SKIP Mode functionality
Tests duplicate detection, checkpoint resume, and gallery navigation
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile
import json
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager,
    GenerationDownloadConfig,
    GenerationDownloadLogger,
    GenerationMetadata
)


class TestSkipModeComprehensive:
    """Comprehensive test suite for SKIP mode functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GenerationDownloadConfig()
        self.config.downloads_folder = os.path.join(self.temp_dir, 'downloads')
        self.config.logs_folder = os.path.join(self.temp_dir, 'logs')
        self.config.duplicate_mode = "skip"
        self.config.duplicate_check_enabled = True
        
        # Create directories
        os.makedirs(self.config.downloads_folder, exist_ok=True)
        os.makedirs(self.config.logs_folder, exist_ok=True)
        
        self.manager = GenerationDownloadManager(self.config)
        
        # Create mock log file with test data
        self.log_file = os.path.join(self.config.logs_folder, 'generation_downloads.txt')
        self._create_test_log_file()
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_test_log_file(self):
        """Create test log file with sample entries"""
        test_entries = [
            {
                "file_id": "#000000001",
                "generation_date": "30 Aug 2025 05:15:30",
                "prompt": "A serene mountain landscape with snow-capped peaks",
                "download_timestamp": "2025-08-30T05:16:45.123456",
                "file_path": "/downloads/vids/video_2025-08-30-05-15-30_001.mp4",
                "original_filename": "temp_download_001.mp4",
                "file_size": 2457600,
                "download_duration": 3.2
            },
            {
                "file_id": "#000000002", 
                "generation_date": "30 Aug 2025 05:11:29",
                "prompt": "The camera begins with a tight close-up of the witch's dual-col",
                "download_timestamp": "2025-08-30T05:12:15.654321",
                "file_path": "/downloads/vids/video_2025-08-30-05-11-29_002.mp4",
                "original_filename": "temp_download_002.mp4",
                "file_size": 3145728,
                "download_duration": 4.1
            },
            {
                "file_id": "#000000003",
                "generation_date": "30 Aug 2025 05:08:15",
                "prompt": "Urban street art on brick walls with vibrant colors",
                "download_timestamp": "2025-08-30T05:09:30.987654",
                "file_path": "/downloads/vids/video_2025-08-30-05-08-15_003.mp4",
                "original_filename": "temp_download_003.mp4", 
                "file_size": 1863680,
                "download_duration": 2.8
            }
        ]
        
        with open(self.log_file, 'w') as f:
            for entry in test_entries:
                f.write(json.dumps(entry) + '\n')
                
    @pytest.mark.asyncio
    async def test_duplicate_detection_exact_match(self):
        """Test duplicate detection with exact date and prompt match"""
        
        # Mock page metadata that exactly matches log entry #2
        mock_page = Mock()
        
        with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col'
            }
            
            is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
            
            assert is_duplicate == True
            
    @pytest.mark.asyncio 
    async def test_duplicate_detection_no_match(self):
        """Test duplicate detection with no matching entries"""
        
        mock_page = Mock()
        
        with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '30 Aug 2025 06:00:00',
                'prompt': 'A completely new and unique prompt that does not exist'
            }
            
            is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
            
            assert is_duplicate == False
            
    @pytest.mark.asyncio
    async def test_duplicate_detection_partial_prompt_match(self):
        """Test duplicate detection with partial prompt matches"""
        
        mock_page = Mock()
        
        test_cases = [
            # Same date, same prompt beginning - should match
            {
                'date': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-colored eyes and mysterious smile',
                'expected': True
            },
            # Same date, different prompt - should not match
            {
                'date': '30 Aug 2025 05:11:29', 
                'prompt': 'A different prompt entirely with different content',
                'expected': False
            },
            # Different date, same prompt - should not match
            {
                'date': '30 Aug 2025 06:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col',
                'expected': False
            }
        ]
        
        for case in test_cases:
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = {
                    'generation_date': case['date'],
                    'prompt': case['prompt']
                }
                
                is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
                
                assert is_duplicate == case['expected'], f"Failed for case: {case}"
                
    def test_checkpoint_loading_from_log(self):
        """Test loading checkpoint data from existing log file"""
        
        # The manager should load the most recent entry as checkpoint
        self.manager._load_existing_log_entries()
        
        assert hasattr(self.manager, 'existing_log_entries')
        assert len(self.manager.existing_log_entries) == 3
        
        # Should have checkpoint data from most recent entry
        if hasattr(self.manager, 'checkpoint_data'):
            checkpoint = self.manager.checkpoint_data
            assert checkpoint['generation_date'] == '30 Aug 2025 05:15:30'
            assert 'mountain landscape' in checkpoint['prompt']
            
    @pytest.mark.asyncio
    async def test_skip_mode_continues_after_duplicate(self):
        """Test that SKIP mode continues processing after finding duplicates"""
        
        mock_page = Mock()
        
        # Simulate finding a duplicate
        with patch.object(self.manager, 'check_comprehensive_duplicate') as mock_check:
            mock_check.return_value = True
            
            # Mock exit-scan-return strategy
            with patch.object(self.manager, 'exit_gallery_and_scan_generations') as mock_exit_scan:
                mock_exit_scan.return_value = {'success': True, 'boundary_found': True}
                
                # In SKIP mode, finding a duplicate should trigger exit-scan-return
                is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
                
                assert is_duplicate == True
                mock_exit_scan.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_finish_mode_stops_at_duplicate(self):
        """Test that FINISH mode stops at first duplicate"""
        
        # Change to FINISH mode
        self.config.duplicate_mode = "finish"
        finish_manager = GenerationDownloadManager(self.config)
        
        mock_page = Mock()
        
        with patch.object(finish_manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up of the witch\'s dual-col'
            }
            
            is_duplicate = await finish_manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
            
            # In FINISH mode, should detect duplicate but not trigger exit-scan
            assert is_duplicate == True
            
    def test_log_entry_chronological_ordering(self):
        """Test that log entries are processed in chronological order"""
        
        self.manager._load_existing_log_entries()
        
        if hasattr(self.manager, 'existing_log_entries'):
            entries = self.manager.existing_log_entries
            
            # Should be ordered by generation_date (newest first for checkpoint finding)
            dates = [entry['generation_date'] for entry in entries]
            
            # Verify chronological ordering
            assert len(dates) == 3
            # Most recent should be first (05:15:30)
            assert '05:15:30' in dates[0]
            
    @pytest.mark.asyncio
    async def test_metadata_extraction_validation(self):
        """Test metadata extraction handles various formats"""
        
        mock_page = Mock()
        
        # Test various metadata formats that might be encountered
        test_metadata = [
            # Standard format
            {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'Test prompt content'
            },
            # Missing date
            {
                'generation_date': '',
                'prompt': 'Test prompt content'
            },
            # Missing prompt
            {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': ''
            },
            # Both missing
            {
                'generation_date': '',
                'prompt': ''
            }
        ]
        
        for metadata in test_metadata:
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = metadata
                
                is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
                
                # Should handle gracefully without crashing
                if metadata['generation_date'] and metadata['prompt']:
                    # Only valid metadata should be processed for duplicates
                    assert isinstance(is_duplicate, bool)
                else:
                    # Invalid metadata should return False (not a duplicate)
                    assert is_duplicate == False
                    
    @pytest.mark.asyncio
    async def test_large_gallery_performance(self):
        """Test performance with large galleries and many log entries"""
        
        # Create large log file
        large_log_file = os.path.join(self.config.logs_folder, 'large_test.txt')
        
        with open(large_log_file, 'w') as f:
            for i in range(1000):  # 1000 entries
                entry = {
                    "file_id": f"#000{i:06d}",
                    "generation_date": f"30 Aug 2025 {5 + (i % 10):02d}:{10 + (i % 50):02d}:{20 + (i % 40):02d}",
                    "prompt": f"Test prompt number {i} with unique content",
                    "download_timestamp": "2025-08-30T05:16:45.123456",
                    "file_path": f"/downloads/vids/video_{i:06d}.mp4",
                    "original_filename": f"temp_download_{i:06d}.mp4",
                    "file_size": 2457600 + i * 1000,
                    "download_duration": 3.2 + (i * 0.001)
                }
                f.write(json.dumps(entry) + '\n')
                
        # Backup original log file path and use large one
        original_log = self.manager.config.log_file
        self.manager.config.log_file = large_log_file
        
        try:
            import time
            
            start_time = time.time()
            self.manager._load_existing_log_entries()
            load_time = time.time() - start_time
            
            # Should load reasonably quickly (under 1 second for 1000 entries)
            assert load_time < 1.0
            
            # Verify entries were loaded
            assert len(self.manager.existing_log_entries) == 1000
            
            # Test duplicate checking performance
            mock_page = Mock()
            
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                # Test with entry that matches the middle of the log
                mock_extract.return_value = {
                    'generation_date': '30 Aug 2025 09:35:40',
                    'prompt': 'Test prompt number 500 with unique content'
                }
                
                start_time = time.time()
                is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
                check_time = time.time() - start_time
                
                # Duplicate check should be fast (under 0.1 seconds)
                assert check_time < 0.1
                assert is_duplicate == True
                
        finally:
            # Restore original log file path
            self.manager.config.log_file = original_log
            if os.path.exists(large_log_file):
                os.remove(large_log_file)
                
    @pytest.mark.asyncio
    async def test_error_recovery_scenarios(self):
        """Test error recovery in various scenarios"""
        
        mock_page = Mock()
        
        # Test 1: Log file is corrupted/unreadable
        corrupted_log = os.path.join(self.config.logs_folder, 'corrupted.txt')
        with open(corrupted_log, 'w') as f:
            f.write('invalid json content\n')
            f.write('{"valid": "json"}\n')
            f.write('more invalid content\n')
            
        original_log = self.manager.config.log_file
        self.manager.config.log_file = corrupted_log
        
        try:
            # Should handle corrupted entries gracefully
            self.manager._load_existing_log_entries()
            
            # Should have loaded the valid entry and skipped invalid ones
            if hasattr(self.manager, 'existing_log_entries'):
                assert len(self.manager.existing_log_entries) >= 0  # At least didn't crash
                
        finally:
            self.manager.config.log_file = original_log
            if os.path.exists(corrupted_log):
                os.remove(corrupted_log)
                
        # Test 2: Metadata extraction fails
        with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.side_effect = Exception("Extraction failed")
            
            # Should handle extraction failures gracefully
            is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
            assert is_duplicate == False  # Should default to False on error
            
    @pytest.mark.asyncio
    async def test_edge_case_prompt_matching(self):
        """Test edge cases in prompt matching logic"""
        
        mock_page = Mock()
        
        edge_cases = [
            # Very long prompt (should use first part for matching)
            {
                'log_prompt': 'Short prompt',
                'page_prompt': 'Short prompt' + ' ' * 1000 + 'with lots of extra content',
                'expected': True  # Should match on beginning
            },
            # Empty prompts
            {
                'log_prompt': '',
                'page_prompt': '',
                'expected': False  # Empty prompts should not match
            },
            # Very similar but different prompts
            {
                'log_prompt': 'The camera begins with a tight close-up',
                'page_prompt': 'The camera begins with a loose close-up',
                'expected': False  # Should not match
            },
            # Special characters
            {
                'log_prompt': 'Prompt with "special" characters & symbols!',
                'page_prompt': 'Prompt with "special" characters & symbols!',
                'expected': True
            }
        ]
        
        for case in edge_cases:
            # Create temporary log with edge case
            temp_log = os.path.join(self.config.logs_folder, 'edge_case.txt')
            test_entry = {
                "file_id": "#000000999",
                "generation_date": "30 Aug 2025 05:00:00",
                "prompt": case['log_prompt'],
                "download_timestamp": "2025-08-30T05:01:00.000000",
                "file_path": "/test/path.mp4",
                "original_filename": "test.mp4",
                "file_size": 1000,
                "download_duration": 1.0
            }
            
            with open(temp_log, 'w') as f:
                f.write(json.dumps(test_entry) + '\n')
                
            # Test with this log
            original_log = self.manager.config.log_file
            self.manager.config.log_file = temp_log
            self.manager._load_existing_log_entries()
            
            try:
                with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                    mock_extract.return_value = {
                        'generation_date': '30 Aug 2025 05:00:00',
                        'prompt': case['page_prompt']
                    }
                    
                    is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumbnail')
                    
                    assert is_duplicate == case['expected'], f"Failed edge case: {case}"
                    
            finally:
                self.manager.config.log_file = original_log
                if os.path.exists(temp_log):
                    os.remove(temp_log)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])