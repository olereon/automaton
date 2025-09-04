#!/usr/bin/env python3
"""
Test suite to validate algorithm-compliant fixes to generation_download_manager.py
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.generation_download_manager import GenerationDownloadManager, DuplicateMode, GenerationDownloadConfig

class TestAlgorithmCompliantFixes:
    """Test algorithm-compliant fixes"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = GenerationDownloadConfig(
            downloads_folder="/tmp/test",
            duplicate_mode=DuplicateMode.SKIP,
            duplicate_check_enabled=True
        )
        self.manager = GenerationDownloadManager(self.config)
        
        # Mock existing log entries
        self.manager.existing_log_entries = {
            "31 Aug 2025 13:32:04": {
                "prompt": "The camera begins with a wide shot of the colossal skeletal guardian...",
                "file_path": "/tmp/test/file1.mp4"
            },
            "30 Aug 2025 12:00:00": {
                "prompt": "A beautiful landscape with mountains and rivers flowing...",
                "file_path": "/tmp/test/file2.mp4"
            }
        }

    def test_duplicate_detection_datetime_prompt_pair(self):
        """Test Step 6a: datetime + prompt pair duplicate detection"""
        
        # Test 1: Exact duplicate should trigger exit-scan-return in SKIP mode
        result = self.manager.check_duplicate_exists(
            "31 Aug 2025 13:32:04",
            "The camera begins with a wide shot of the colossal skeletal guardian..."
        )
        assert result == "exit_scan_return", "Should initiate skipping for exact duplicate in SKIP mode"
        
        # Test 2: Different datetime, same prompt = not duplicate
        result = self.manager.check_duplicate_exists(
            "01 Sep 2025 14:00:00", 
            "The camera begins with a wide shot of the colossal skeletal guardian..."
        )
        assert result == False, "Different datetime should not be duplicate"
        
        # Test 3: Same datetime, different prompt = not duplicate  
        result = self.manager.check_duplicate_exists(
            "31 Aug 2025 13:32:04",
            "A completely different prompt about something else..."
        )
        assert result == False, "Different prompt should not be duplicate"
        
        # Test 4: FINISH mode behavior
        self.config.duplicate_mode = DuplicateMode.FINISH
        self.manager.config = self.config
        
        result = self.manager.check_duplicate_exists(
            "31 Aug 2025 13:32:04",
            "The camera begins with a wide shot of the colossal skeletal guardian..."
        )
        assert result == True, "Should return True for duplicate in FINISH mode"

    def test_prompt_truncation_100_chars(self):
        """Test that prompt comparison uses first 100 characters as specified"""
        
        # Use a 120-character prompt in both places, so first 100 chars match
        long_base_prompt = "The camera begins with a wide shot of the colossal skeletal guardian, its eye sockets glowing with piercing green light. The ancient bones are weathered..."
        
        # Update the mock log entry to use the same long prompt
        self.manager.existing_log_entries["31 Aug 2025 13:32:04"]["prompt"] = long_base_prompt
        
        # Create test prompt with same first 100 chars but different ending
        test_prompt = long_base_prompt[:100] + " DIFFERENT ENDING that should be ignored in comparison!"
        
        # Debug output
        print(f"Log entry first 100: '{long_base_prompt[:100]}'")
        print(f"Test prompt first 100: '{test_prompt[:100]}'")
        print(f"Are first 100 chars equal? {long_base_prompt[:100] == test_prompt[:100]}")
        
        # Should match because first 100 chars are identical
        result = self.manager.check_duplicate_exists(
            "31 Aug 2025 13:32:04",
            test_prompt
        )
        assert result == "exit_scan_return", f"Should detect duplicate using first 100 chars. Got: {result}"

    def test_no_duplicate_detection_when_disabled(self):
        """Test that duplicate detection is bypassed when disabled"""
        
        self.config.duplicate_check_enabled = False
        self.manager.config = self.config
        
        result = self.manager.check_duplicate_exists(
            "31 Aug 2025 13:32:04",
            "The camera begins with a wide shot of the colossal skeletal guardian..."
        )
        assert result == False, "Should not detect duplicates when disabled"

    def test_enhanced_skip_mode_initialization(self):
        """Test simplified Enhanced SKIP mode initialization"""
        
        # Test SKIP mode initialization
        result = self.manager.initialize_enhanced_skip_mode()
        assert result == True, "Should initialize successfully in SKIP mode"
        assert hasattr(self.manager, 'skip_mode_active'), "Should set skip_mode_active"
        assert self.manager.skip_mode_active == True, "Should activate skip mode"
        
        # Test FINISH mode (should not initialize)
        self.config.duplicate_mode = DuplicateMode.FINISH
        self.manager.config = self.config
        
        result = self.manager.initialize_enhanced_skip_mode()
        assert result == False, "Should not initialize in FINISH mode"

    @pytest.mark.asyncio
    async def test_fast_forward_to_checkpoint_simplified(self):
        """Test simplified fast_forward_to_checkpoint method"""
        
        page_mock = Mock()
        
        # Should always return "download" (simplified behavior)
        result = await self.manager.fast_forward_to_checkpoint(page_mock, "thumbnail_123")
        assert result == "download", "Should always return download for algorithm compliance"

    @pytest.mark.asyncio  
    async def test_is_still_duplicate_delegates_to_check_duplicate(self):
        """Test that _is_still_duplicate delegates to check_duplicate_exists"""
        
        metadata = {
            "generation_date": "31 Aug 2025 13:32:04",
            "prompt": "The camera begins with a wide shot of the colossal skeletal guardian..."
        }
        
        result = await self.manager._is_still_duplicate(metadata)
        assert result == True, "Should delegate to check_duplicate_exists and return True for duplicate"

    def test_algorithm_compliance_steps_covered(self):
        """Test that all algorithm steps are addressed"""
        
        # Check that key algorithm components are implemented
        assert hasattr(self.manager, 'check_duplicate_exists'), "Step 6a: Duplicate detection"
        assert hasattr(self.manager, 'exit_gallery_and_scan_generations'), "Steps 11-15: Exit-scan-return"
        assert hasattr(self.manager, 'find_completed_generations_on_page'), "Steps 2-3: Sequential container checking"
        assert hasattr(self.manager, '_find_download_boundary_sequential'), "Steps 13-14: Sequential comparison"
        
        print("✅ All algorithm steps are implemented!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])