#!/usr/bin/env python3
"""
Simple validation test for boundary detection improvements
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.generation_download_manager import GenerationDownloadManager, DuplicateMode, GenerationDownloadConfig

class TestBoundaryDetectionValidation:
    """Validate boundary detection handles large galleries correctly"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = GenerationDownloadConfig(
            downloads_folder="/tmp/test",
            duplicate_mode=DuplicateMode.SKIP,
            duplicate_check_enabled=True,
            logs_folder="/tmp/logs",
            thumbnail_selector=".thumbnail-item"
        )
        self.manager = GenerationDownloadManager(self.config)
        
        # Create existing log entries (simulates previous downloads)
        self.manager.existing_log_entries = {
            "01 Sep 2025 02:57:51": {
                "id": "#000000413",
                "date": "01 Sep 2025 02:57:51",
                "prompt": "The camera begins with a medium shot, framing the Eldritch priestess centered in the dark temple..."
            },
            "01 Sep 2025 02:57:32": {
                "id": "#000000414", 
                "date": "01 Sep 2025 02:57:32",
                "prompt": "A magical forest scene with ancient trees and mystical fog swirling around the base..."
            }
        }

    @pytest.mark.asyncio
    async def test_scroll_gallery_loads_progressively(self):
        """Test gallery scrolling loads content progressively"""
        page_mock = AsyncMock()
        
        # Simulate progressive thumbnail loading
        thumbnail_counts = [10, 25, 50, 75, 75]  # Final count stays same (end reached)
        call_count = 0
        
        def mock_query_selector_all(selector):
            nonlocal call_count
            count = thumbnail_counts[min(call_count, len(thumbnail_counts)-1)]
            call_count += 1
            return [AsyncMock() for _ in range(count)]
        
        page_mock.query_selector_all.side_effect = mock_query_selector_all
        
        await self.manager._scroll_entire_gallery_for_boundary_detection(page_mock)
        
        # Should scroll and load progressively
        assert page_mock.query_selector_all.call_count >= 4
        assert page_mock.evaluate.call_count >= 3  # Multiple scrolls

    def test_duplicate_detection_triggers_exit_scan_return(self):
        """Test duplicate detection properly triggers exit-scan-return in SKIP mode"""
        
        # Test with exact match from log entries
        result = self.manager.check_duplicate_exists(
            "01 Sep 2025 02:57:51",
            "The camera begins with a medium shot, framing the Eldritch priestess centered in the dark temple...",
            existing_log_entries=self.manager.existing_log_entries
        )
        assert result == "exit_scan_return"
        
        # Test with truncated prompt (first 100 chars)
        result = self.manager.check_duplicate_exists(
            "01 Sep 2025 02:57:32", 
            "A magical forest scene with ancient trees and mystical fog swirling around the base...",
            existing_log_entries=self.manager.existing_log_entries
        )
        assert result == "exit_scan_return"
        
        # Test with new content (should not trigger)
        result = self.manager.check_duplicate_exists(
            "01 Sep 2025 05:30:00",
            "NEW CONTENT: A steampunk airship soaring through storm clouds...",
            existing_log_entries=self.manager.existing_log_entries
        )
        assert result == False

    @pytest.mark.asyncio 
    async def test_boundary_detection_finds_new_content(self):
        """Test boundary detection finds first new content after duplicates"""
        page_mock = AsyncMock()
        
        # Create mock containers
        containers = []
        
        # First 2 are duplicates (match log entries)
        for i, (time, entry) in enumerate(self.manager.existing_log_entries.items()):
            container = AsyncMock()
            text_content = f"Creation Time {time}\n{entry['prompt']}"
            container.text_content.return_value = text_content
            containers.append(container)
        
        # 3rd container is NEW (boundary)
        boundary_container = AsyncMock()
        boundary_text = "Creation Time 01 Sep 2025 06:00:00\nNEW CONTENT: A quantum laboratory with floating experiments..."
        boundary_container.text_content.return_value = boundary_text
        
        # Mock successful click
        img_element = AsyncMock()
        boundary_container.query_selector.return_value = img_element
        containers.append(boundary_container)
        
        page_mock.query_selector_all.return_value = containers
        
        result = await self.manager._find_download_boundary_sequential(page_mock)
        
        # Should find the boundary at 3rd container
        assert result is not None
        assert result['found'] == True
        assert result['container_index'] == 3
        assert result['duplicates_found'] == 2  # Found 2 duplicates before boundary
        assert "NEW CONTENT" in result['prompt']

    def test_large_gallery_scenario_setup(self):
        """Test that the system can handle hundreds of log entries"""
        
        # Add 100 more entries to simulate large download history
        for i in range(100):
            time_str = f"31 Aug 2025 {10 + i//10:02d}:{(i*2)%60:02d}:{(i*3)%60:02d}"
            self.manager.existing_log_entries[time_str] = {
                "id": f"#00000{300+i:03d}",
                "date": time_str,
                "prompt": f"Historical download {i}: Various creative content..."
            }
        
        # Should now have 102 total log entries  
        assert len(self.manager.existing_log_entries) == 102
        
        # Duplicate detection should still work with large sets
        result = self.manager.check_duplicate_exists(
            "01 Sep 2025 02:57:51", 
            "The camera begins with a medium shot, framing the Eldritch priestess centered in the dark temple...",
            existing_log_entries=self.manager.existing_log_entries
        )
        assert result == "exit_scan_return"
        
        print("✅ Large gallery scenario validation passed!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])