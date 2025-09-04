#!/usr/bin/env python3
"""
Test suite to verify SKIP mode fixes for generation downloads
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.generation_download_manager import GenerationDownloadManager, DuplicateMode, GenerationDownloadConfig

class TestSkipModeFixes:
    """Test SKIP mode exit-scan-return workflow fixes"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = GenerationDownloadConfig(
            downloads_folder="/tmp/test",
            duplicate_mode=DuplicateMode.SKIP,
            duplicate_check_enabled=True,
            logs_folder="/tmp/logs"
        )
        self.manager = GenerationDownloadManager(self.config)
        
        # Mock existing log entries (simulating previous downloads)
        self.manager.existing_log_entries = {
            "01 Sep 2025 00:47:18": {
                "id": "#000000412",
                "date": "01 Sep 2025 00:47:18",
                "prompt": "The camera begins with a medium shot, framing the Eldritch priestess centered in the dark temple, her eyes glowing with arcane power as she chants ancient incantations..."
            },
            "31 Aug 2025 23:45:00": {
                "id": "#000000411", 
                "date": "31 Aug 2025 23:45:00",
                "prompt": "A beautiful landscape with mountains and rivers flowing through the valley at sunset..."
            }
        }

    @pytest.mark.asyncio
    async def test_exit_gallery_with_multiple_selectors(self):
        """Test that exit gallery tries multiple selectors"""
        page_mock = AsyncMock()
        
        # Simulate first selector failing, second succeeding
        selector_results = [None, Mock()]  # First fails, second succeeds
        page_mock.wait_for_selector.side_effect = [
            Exception("Timeout"),  # First selector fails
            selector_results[1],   # Second selector succeeds
        ]
        
        # Mock the boundary detection to return a result
        self.manager._find_download_boundary_sequential = AsyncMock(return_value={
            'found': True,
            'container_index': 10,
            'creation_time': '01 Sep 2025 01:50:19',
            'prompt': 'New content prompt'
        })
        
        result = await self.manager.exit_gallery_and_scan_generations(page_mock)
        
        # Should have tried multiple selectors
        assert page_mock.wait_for_selector.call_count >= 2
        assert result is not None
        assert result['found'] == True

    @pytest.mark.asyncio
    async def test_exit_gallery_fallback_to_back_navigation(self):
        """Test that exit gallery falls back to back navigation if all selectors fail"""
        page_mock = AsyncMock()
        
        # All selectors fail
        page_mock.wait_for_selector.side_effect = Exception("Timeout")
        
        # Mock back navigation
        page_mock.go_back = AsyncMock()
        
        # Mock boundary detection
        self.manager._find_download_boundary_sequential = AsyncMock(return_value={
            'found': True,
            'container_index': 10
        })
        
        result = await self.manager.exit_gallery_and_scan_generations(page_mock)
        
        # Should have called go_back as fallback
        page_mock.go_back.assert_called_once()

    def test_duplicate_detection_with_exact_match(self):
        """Test duplicate detection with exact datetime + prompt match"""
        
        # Exact match should trigger exit-scan-return in SKIP mode
        result = self.manager.check_duplicate_exists(
            "01 Sep 2025 00:47:18",
            "The camera begins with a medium shot, framing the Eldritch priestess centered in the dark temple, her eyes glowing with arcane power as she chants ancient incantations..."
        )
        assert result == "exit_scan_return", "Should trigger exit-scan-return for exact duplicate"

    def test_duplicate_detection_with_truncated_prompt(self):
        """Test duplicate detection with truncated prompt (first 100 chars)"""
        
        # First 100 chars match
        truncated_prompt = "The camera begins with a medium shot, framing the Eldritch priestess centered in the dark temple, he..."
        
        result = self.manager.check_duplicate_exists(
            "01 Sep 2025 00:47:18",
            truncated_prompt
        )
        assert result == "exit_scan_return", "Should detect duplicate with truncated prompt"

    @pytest.mark.asyncio
    async def test_container_metadata_extraction(self):
        """Test improved container metadata extraction"""
        
        # Mock container element
        container_mock = AsyncMock()
        
        # Mock prompt div
        prompt_div = AsyncMock()
        prompt_div.text_content.return_value = "The camera begins with a medium shot..."
        
        container_mock.query_selector_all.return_value = [prompt_div]
        
        text_content = """
        Creation Time 01 Sep 2025 00:47:18
        The camera begins with a medium shot...
        """
        
        result = await self.manager._extract_container_metadata(container_mock, text_content)
        
        assert result is not None
        assert result['creation_time'] == "01 Sep 2025 00:47:18"
        assert "The camera begins" in result['prompt']

    @pytest.mark.asyncio
    async def test_boundary_detection_with_improved_selectors(self):
        """Test boundary detection with improved interactive element selectors"""
        
        page_mock = AsyncMock()
        
        # Mock container
        container_mock = AsyncMock()
        container_mock.text_content.return_value = "01 Sep 2025 01:50:19 New prompt text here"
        
        # Mock interactive element (video)
        video_element = AsyncMock()
        container_mock.query_selector.side_effect = [
            None,  # First selector fails
            None,  # Second selector fails  
            video_element,  # Video selector succeeds
        ]
        
        page_mock.query_selector.return_value = container_mock
        
        # Set up manager with no matching log entry for this container
        self.manager.existing_log_entries = {
            "01 Sep 2025 00:47:18": {"prompt": "Old content"}
        }
        
        result = await self.manager._find_download_boundary_sequential(page_mock)
        
        # Should have tried multiple selectors for interactive element
        assert container_mock.query_selector.call_count >= 3

    def test_skip_mode_initialization(self):
        """Test SKIP mode initialization loads log entries correctly"""
        
        # Initialize SKIP mode
        result = self.manager.initialize_enhanced_skip_mode()
        
        assert result == True
        assert hasattr(self.manager, 'skip_mode_active')
        assert self.manager.skip_mode_active == True
        assert hasattr(self.manager, 'existing_log_entries')

    @pytest.mark.asyncio
    async def test_full_skip_workflow_simulation(self):
        """Test complete SKIP mode workflow: detect duplicate → exit → scan → find boundary → resume"""
        
        # Step 1: Detect duplicate (need full 100+ char prompt for match)
        full_prompt = "The camera begins with a medium shot, framing the Eldritch priestess centered in the dark temple, her eyes glowing with arcane power as she chants ancient incantations..."
        duplicate_result = self.manager.check_duplicate_exists(
            "01 Sep 2025 00:47:18",
            full_prompt
        )
        assert duplicate_result == "exit_scan_return"
        
        # Step 2: Exit gallery (mocked)
        page_mock = AsyncMock()
        exit_button = AsyncMock()
        page_mock.wait_for_selector.return_value = exit_button
        
        # Step 3: Mock boundary detection returns new content location
        self.manager._find_download_boundary_sequential = AsyncMock(return_value={
            'found': True,
            'container_index': 17,
            'creation_time': '01 Sep 2025 01:50:19',
            'prompt': 'New content that was not downloaded before'
        })
        
        # Execute exit-scan-return workflow
        result = await self.manager.exit_gallery_and_scan_generations(page_mock)
        
        assert result is not None
        assert result['found'] == True
        assert result['container_index'] == 17
        assert result['creation_time'] == '01 Sep 2025 01:50:19'
        
        print("✅ Full SKIP workflow test passed!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])