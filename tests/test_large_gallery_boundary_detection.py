#!/usr/bin/env python3
"""
Test suite for large gallery boundary detection improvements
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.generation_download_manager import GenerationDownloadManager, DuplicateMode, GenerationDownloadConfig

class TestLargeGalleryBoundaryDetection:
    """Test boundary detection for galleries with hundreds of downloads"""
    
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
        
        # Mock large set of existing log entries (simulate 3 download sessions)
        self.manager.existing_log_entries = {}
        
        # Session 1: 100 downloads (Aug 28)
        for i in range(100):
            time_str = f"28 Aug 2025 {10 + i//10:02d}:{i%10:02d}:{i%60:02d}"
            self.manager.existing_log_entries[time_str] = {
                "id": f"#00000{300+i:04d}",
                "date": time_str,
                "prompt": f"Session 1 prompt {i}: A magical forest scene with ancient trees and mystical fog..."
            }
        
        # Session 2: 150 downloads (Aug 29-30)  
        for i in range(150):
            day = 29 if i < 75 else 30
            time_str = f"{day} Aug 2025 {8 + i//20:02d}:{(i*2)%60:02d}:{(i*3)%60:02d}"
            self.manager.existing_log_entries[time_str] = {
                "id": f"#00000{400+i:04d}", 
                "date": time_str,
                "prompt": f"Session 2 prompt {i}: A cyberpunk cityscape with neon lights and flying cars..."
            }
        
        # Session 3: 50 downloads (Sep 1) - most recent
        for i in range(50):
            time_str = f"01 Sep 2025 {2 + i//10:02d}:{(i*3)%60:02d}:{(i*5)%60:02d}"
            self.manager.existing_log_entries[time_str] = {
                "id": f"#00000{550+i:04d}",
                "date": time_str,
                "prompt": f"Session 3 prompt {i}: A fantasy castle floating in the clouds with dragons..."
            }

    def create_mock_container(self, creation_time: str, prompt: str, container_index: int):
        """Create a mock thumbnail container with metadata"""
        container = AsyncMock()
        
        # Mock text content containing creation time and prompt
        text_content = f"Creation Time {creation_time}\n{prompt}"
        container.text_content.return_value = text_content
        
        # Mock interactive elements
        img_element = AsyncMock()
        video_element = AsyncMock()
        container.query_selector.side_effect = lambda selector: {
            'img': img_element if 'img' in selector else None,
            'video': video_element if 'video' in selector else None,
            '.sc-abVJb.eNepQa': img_element
        }.get(selector)
        
        return container

    @pytest.mark.asyncio
    async def test_scroll_entire_gallery_loads_all_thumbnails(self):
        """Test that gallery scrolling loads all thumbnails progressively"""
        page_mock = AsyncMock()
        
        # Simulate progressive thumbnail loading during scrolls
        thumbnail_counts = [50, 100, 200, 350, 350]  # Final count stays same (end reached)
        call_count = 0
        
        def mock_query_selector_all(selector):
            nonlocal call_count
            count = thumbnail_counts[min(call_count, len(thumbnail_counts)-1)]
            call_count += 1
            return [Mock() for _ in range(count)]
        
        page_mock.query_selector_all.side_effect = mock_query_selector_all
        
        await self.manager._scroll_entire_gallery_for_boundary_detection(page_mock)
        
        # Should have scrolled and counted thumbnails multiple times
        assert page_mock.query_selector_all.call_count >= 5
        assert page_mock.evaluate.call_count >= 4  # At least 4 scrolls

    @pytest.mark.asyncio
    async def test_boundary_detection_with_300_containers(self):
        """Test boundary detection across 300+ thumbnail containers"""
        page_mock = AsyncMock()
        
        # Create 350 mock containers
        mock_containers = []
        
        # First 300 containers are duplicates from log entries
        for i in range(300):
            if i < 100:
                # Session 1 duplicates
                time_str = f"28 Aug 2025 {10 + i//10:02d}:{i%10:02d}:{i%60:02d}"
                prompt = f"Session 1 prompt {i}: A magical forest scene with ancient trees and mystical fog..."
            elif i < 250: 
                # Session 2 duplicates
                j = i - 100
                day = 29 if j < 75 else 30
                time_str = f"{day} Aug 2025 {8 + j//20:02d}:{(j*2)%60:02d}:{(j*3)%60:02d}"
                prompt = f"Session 2 prompt {j}: A cyberpunk cityscape with neon lights and flying cars..."
            else:
                # Session 3 duplicates  
                j = i - 250
                time_str = f"01 Sep 2025 {2 + j//10:02d}:{(j*3)%60:02d}:{(j*5)%60:02d}"
                prompt = f"Session 3 prompt {j}: A fantasy castle floating in the clouds with dragons..."
            
            container = self.create_mock_container(time_str, prompt, i)
            mock_containers.append(container)
        
        # Container 301 is NEW (boundary)
        boundary_time = "01 Sep 2025 05:30:00"
        boundary_prompt = "NEW CONTENT: A steampunk airship soaring through storm clouds..."
        boundary_container = self.create_mock_container(boundary_time, boundary_prompt, 301)
        mock_containers.append(boundary_container)
        
        # Remaining containers are also new
        for i in range(302, 350):
            time_str = f"01 Sep 2025 {5 + (i-301)//10:02d}:{((i-301)*5)%60:02d}:00"
            prompt = f"New content {i}: Various creative scenes..."
            container = self.create_mock_container(time_str, prompt, i)
            mock_containers.append(container)
        
        # Mock the gallery scroll to load all containers
        page_mock.query_selector_all.return_value = mock_containers
        
        # Test boundary detection
        result = await self.manager._find_download_boundary_sequential(page_mock)
        
        # Should find the boundary at container 301 (index 300 in 0-based array)
        assert result is not None
        assert result['found'] == True
        assert result['container_index'] == 301
        assert result['creation_time'] == boundary_time
        assert "NEW CONTENT" in result['prompt']
        assert result['containers_scanned'] >= 301
        assert result['duplicates_found'] == 300
        assert result['total_containers'] == 350

    @pytest.mark.asyncio 
    async def test_boundary_detection_handles_session_gaps(self):
        """Test boundary detection with gaps between download sessions"""
        page_mock = AsyncMock()
        
        # Create containers with gaps between sessions
        mock_containers = []
        
        # 20 containers from Session 1 (old)
        for i in range(20):
            time_str = f"28 Aug 2025 {10 + i//10:02d}:{i%10:02d}:{i%60:02d}"
            prompt = f"Session 1 prompt {i}: A magical forest scene..."
            container = self.create_mock_container(time_str, prompt, i)
            mock_containers.append(container)
        
        # GAP: 30 containers with new content (not in logs)
        for i in range(20, 50):
            time_str = f"29 Aug 2025 {i//10:02d}:{(i*3)%60:02d}:00"
            prompt = f"NEW gap content {i}: Unseen creative content..."
            container = self.create_mock_container(time_str, prompt, i)
            mock_containers.append(container)
        
        # 10 more from Session 2 (old)
        for i in range(50, 60):
            j = i - 50
            time_str = f"29 Aug 2025 {15 + j//5:02d}:{(j*2)%60:02d}:{(j*3)%60:02d}"
            prompt = f"Session 2 prompt {j}: A cyberpunk cityscape..."
            container = self.create_mock_container(time_str, prompt, i)
            mock_containers.append(container)
        
        page_mock.query_selector_all.return_value = mock_containers
        
        result = await self.manager._find_download_boundary_sequential(page_mock)
        
        # Should find boundary at first gap container (index 20)
        assert result is not None
        assert result['found'] == True
        assert result['container_index'] == 21  # 1-based indexing
        assert result['duplicates_found'] == 20  # Found 20 duplicates before boundary
        assert "NEW gap content" in result['prompt']

    @pytest.mark.asyncio
    async def test_boundary_detection_all_duplicates_scenario(self):
        """Test behavior when all containers are duplicates (no new content)"""
        page_mock = AsyncMock()
        
        # Create 100 containers, all matching existing log entries
        mock_containers = []
        
        for i in range(100):
            time_str = f"28 Aug 2025 {10 + i//10:02d}:{i%10:02d}:{i%60:02d}"  
            prompt = f"Session 1 prompt {i}: A magical forest scene with ancient trees and mystical fog..."
            container = self.create_mock_container(time_str, prompt, i)
            mock_containers.append(container)
        
        page_mock.query_selector_all.return_value = mock_containers
        
        result = await self.manager._find_download_boundary_sequential(page_mock)
        
        # Should return None (no boundary found)
        assert result is None

    @pytest.mark.asyncio
    async def test_boundary_click_success_with_multiple_selectors(self):
        """Test successful container clicking with selector fallbacks"""
        container = AsyncMock()
        
        # First selector fails, second succeeds
        img_element = AsyncMock()
        container.query_selector.side_effect = [
            None,  # First selector fails
            img_element,  # Second selector succeeds  
        ]
        
        result = await self.manager._click_boundary_container(container, 155)
        
        assert result == True
        img_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_comprehensive_workflow_with_large_gallery(self):
        """Test complete workflow: detect duplicate → exit → scroll → find boundary → resume"""
        
        # Step 1: Detect duplicate (should trigger exit-scan-return)
        # Debug: Check what log entries we have
        print(f"Number of log entries: {len(self.manager.existing_log_entries)}")
        sample_entries = list(self.manager.existing_log_entries.items())[:5]
        print(f"Sample entries: {sample_entries}")
        
        # Use exact time/prompt from Session 3 entry (index 20)
        # Session 3: i=20, hour = 2 + 20//10 = 4, minute = (20*3)%60 = 0, second = (20*5)%60 = 40
        target_time = "01 Sep 2025 04:00:40"
        target_prompt = "Session 3 prompt 20: A fantasy castle floating in the clouds with dragons..."
        
        # Check if this entry exists
        found_entry = target_time in self.manager.existing_log_entries
        print(f"Entry exists: {found_entry}")
        if found_entry:
            print(f"Existing entry: {self.manager.existing_log_entries[target_time]}")
        
        duplicate_result = self.manager.check_duplicate_exists(
            target_time,
            target_prompt,
            existing_log_entries=self.manager.existing_log_entries
        )
        print(f"Duplicate result: {duplicate_result}")
        assert duplicate_result == "exit_scan_return"
        
        # Step 2: Mock exit-scan-return workflow
        page_mock = AsyncMock()
        
        # Mock successful exit from gallery
        exit_button = AsyncMock()
        page_mock.wait_for_selector.return_value = exit_button
        
        # Mock large gallery with boundary at position 280
        mock_containers = []
        
        # First 280 containers are duplicates
        session_times = [
            ("28 Aug 2025", 100, "Session 1 prompt", "A magical forest scene"),
            ("29 Aug 2025", 150, "Session 2 prompt", "A cyberpunk cityscape"), 
            ("01 Sep 2025", 30, "Session 3 prompt", "A fantasy castle")
        ]
        
        container_idx = 0
        for date_prefix, count, prompt_prefix, prompt_suffix in session_times:
            for i in range(count):
                time_str = f"{date_prefix} {10 + i//10:02d}:{(i*2)%60:02d}:{(i*3)%60:02d}"
                prompt = f"{prompt_prefix} {i}: {prompt_suffix}..."
                container = self.create_mock_container(time_str, prompt, container_idx)
                mock_containers.append(container)
                container_idx += 1
        
        # Container 281 is the boundary (new content)
        boundary_container = self.create_mock_container(
            "01 Sep 2025 06:15:00", 
            "BRAND NEW: A quantum laboratory with floating experiments...",
            280
        )
        mock_containers.append(boundary_container)
        
        page_mock.query_selector_all.return_value = mock_containers
        
        # Execute workflow
        result = await self.manager.exit_gallery_and_scan_generations(page_mock)
        
        # Verify results
        assert result is not None
        assert result['found'] == True
        assert result['container_index'] == 281
        assert result['duplicates_found'] == 280
        assert result['total_containers'] == 281
        assert "BRAND NEW" in result['prompt']
        
        print("✅ Large gallery boundary detection test passed!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])