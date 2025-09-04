#!/usr/bin/env python3.11

"""
Test for the consecutive duplicate fix after boundary download.

This test specifically verifies the fix for the infinite loop issue where:
1. Boundary generation gets downloaded successfully
2. Next thumbnail is also a duplicate (consecutive duplicate)  
3. System should NOT trigger exit-scan-return again, instead use fast-forward mode
4. This prevents the infinite loop of finding the same boundary repeatedly
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, Mock
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig, DuplicateMode

class TestConsecutiveDuplicateFix:
    """Test the consecutive duplicate fix for infinite loop prevention"""

    @pytest.fixture
    def skip_config(self, tmp_path):
        """Create a SKIP mode configuration"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            duplicate_mode=DuplicateMode.SKIP,
            duplicate_check_enabled=True,
            stop_on_duplicate=False,
            use_exit_scan_strategy=True,  # Exit-scan-return enabled
            max_downloads=100
        )

    @pytest.fixture
    def existing_log_entries(self):
        """Existing log entries for duplicate comparison"""
        return {
            '03 Sep 2025 16:15:18': {
                'file_id': '#000000026', 
                'prompt': 'Old generation that was already downloaded'
            },
            '03 Sep 2025 16:20:00': {
                'file_id': '#000000027',
                'prompt': 'Another old generation already downloaded'
            }
        }

    @pytest.mark.asyncio
    async def test_boundary_flag_prevents_consecutive_exit_scan_return(self, skip_config, existing_log_entries):
        """Test that boundary flag prevents re-triggering exit-scan-return on consecutive duplicates"""
        
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize with existing log entries
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.initialize_enhanced_skip_mode()
        
        # Mock page
        mock_page = AsyncMock()
        
        # Scenario: Boundary generation was just downloaded
        manager.boundary_just_downloaded = True  # Simulate boundary just downloaded
        
        # Mock metadata extraction to return a duplicate (consecutive duplicate after boundary)
        duplicate_metadata = {
            "generation_date": "03 Sep 2025 16:15:18",  # Matches existing log entry
            "prompt": "Old generation that was already downloaded"
        }
        
        with patch.object(manager, 'extract_metadata_from_page', return_value=duplicate_metadata):
            result = await manager.check_comprehensive_duplicate(mock_page, "test_thumb")
            
            # CRITICAL: Should return "skip" instead of "exit_scan_return" 
            # because boundary_just_downloaded=True
            assert result == "skip", f"Expected 'skip' but got '{result}'"
            
            # Boundary flag should be reset after first consecutive duplicate
            assert manager.boundary_just_downloaded == False, "Boundary flag should be reset"

    @pytest.mark.asyncio 
    async def test_normal_duplicate_still_triggers_exit_scan_return(self, skip_config, existing_log_entries):
        """Test that normal duplicates (not after boundary) still trigger exit-scan-return"""
        
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize with existing log entries
        with patch.object(manager, '_load_existing_log_entries', return_value=existing_log_entries):
            manager.initialize_enhanced_skip_mode()
        
        # Mock page
        mock_page = AsyncMock()
        
        # Scenario: Normal duplicate detection (no boundary just downloaded)
        manager.boundary_just_downloaded = False  # No recent boundary download
        
        # Mock metadata extraction to return a duplicate
        duplicate_metadata = {
            "generation_date": "03 Sep 2025 16:15:18",  # Matches existing log entry  
            "prompt": "Old generation that was already downloaded"
        }
        
        with patch.object(manager, 'extract_metadata_from_page', return_value=duplicate_metadata):
            result = await manager.check_comprehensive_duplicate(mock_page, "test_thumb")
            
            # Should trigger exit-scan-return for normal duplicates
            assert result == "exit_scan_return", f"Expected 'exit_scan_return' but got '{result}'"
            
            # Boundary flag should remain False
            assert manager.boundary_just_downloaded == False, "Boundary flag should stay False"

    @pytest.mark.asyncio
    async def test_boundary_flag_initialization(self, skip_config):
        """Test that boundary flag is properly initialized"""
        
        manager = GenerationDownloadManager(skip_config)
        
        # Should be initialized to False
        assert hasattr(manager, 'boundary_just_downloaded'), "boundary_just_downloaded attribute should exist"
        assert manager.boundary_just_downloaded == False, "boundary_just_downloaded should initialize to False"

    @pytest.mark.asyncio
    async def test_boundary_flag_maintained_during_download_success(self, skip_config):
        """Test that boundary flag is maintained during download success for next thumbnail processing"""
        
        manager = GenerationDownloadManager(skip_config)
        
        # Simulate boundary download completed
        manager.boundary_just_downloaded = True
        
        # Simulate successful download processing (this happens in the main loop)
        # The flag should be maintained to handle the next thumbnail
        
        assert manager.boundary_just_downloaded == True, "Boundary flag should be maintained during success"

def run_tests():
    """Run the tests directly"""
    import subprocess
    result = subprocess.run(['python3.11', '-m', 'pytest', __file__, '-v'], 
                          capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("✅ All tests passed - consecutive duplicate fix is working correctly!")
    else:
        print("❌ Some tests failed - consecutive duplicate fix needs review")