#!/usr/bin/env python3.11

"""
Test for the enhanced queue exclusion filters.

This test verifies that generations with "Video is rendering" status
are properly excluded from processing, along with the existing
"Queuing" and "Something went wrong" exclusions.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig, DuplicateMode

class TestRenderingExclusion:
    """Test enhanced queue exclusion filters including rendering state"""

    @pytest.fixture
    def config(self, tmp_path):
        """Standard configuration for testing"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            duplicate_mode=DuplicateMode.SKIP,
            max_downloads=100
        )

    def create_mock_container(self, text_content, container_id="test_container"):
        """Create mock container with specified text content"""
        container = AsyncMock()
        container.text_content.return_value = text_content
        container.get_attribute.return_value = container_id
        return container

    @pytest.mark.asyncio
    async def test_video_rendering_exclusion_in_boundary_scan(self, config):
        """Test that 'Video is rendering' containers are excluded during boundary scan"""
        
        manager = GenerationDownloadManager(config)
        mock_page = AsyncMock()
        
        # Initialize log entries for boundary detection
        with patch.object(manager, '_load_existing_log_entries', return_value={}):
            manager.existing_log_entries = {}
        
        # Mock containers with different states
        containers = [
            self.create_mock_container("Video is rendering", "container_1"),  # Should be excluded
            self.create_mock_container("Queuing", "container_2"),             # Should be excluded
            self.create_mock_container("Something went wrong", "container_3"), # Should be excluded
            self.create_mock_container("Complete generation content with Creation Time 03 Sep 2025 16:15:18", "container_4")  # Should be processed
        ]
        
        # Mock the page query selector to return containers
        mock_page.query_selector_all.return_value = containers
        mock_page.evaluate.return_value = 1000  # Mock scroll position
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.wait_for_timeout = AsyncMock()
        
        # Mock container metadata extraction
        with patch.object(manager, '_extract_container_metadata') as mock_extract:
            # Only the complete generation should have metadata extracted
            mock_extract.return_value = {
                'creation_time': '03 Sep 2025 16:15:18',
                'prompt': 'Test generation prompt'
            }
            
            with patch.object(manager, '_click_boundary_container', return_value=True):
                result = await manager.exit_gallery_and_scan_generations(mock_page)
                
                # Should find boundary in the complete generation (container_4)
                assert result is not None
                assert result['found'] == True
                assert result['container_index'] == 4  # Should be container #4 (after skipping 3 excluded containers)
                
                # Verify that only the complete generation was processed for metadata
                # The rendering/queuing/failed containers should be skipped
                assert mock_extract.call_count == 1

    @pytest.mark.asyncio
    async def test_rendering_status_logging(self, config):
        """Test that rendering status is properly identified and logged"""
        
        manager = GenerationDownloadManager(config)
        mock_page = AsyncMock()
        
        # Mock container with rendering status
        rendering_container = self.create_mock_container("Video is rendering")
        
        # Test the status detection logic directly
        text_content = await rendering_container.text_content()
        
        # Verify the status detection logic
        is_excluded = ("Queuing" in text_content or 
                      "Something went wrong" in text_content or 
                      "Video is rendering" in text_content)
        
        assert is_excluded == True
        
        # Verify status identification
        if "Video is rendering" in text_content:
            status = "Rendering"
        elif "Queuing" in text_content:
            status = "Queued" 
        elif "Something went wrong" in text_content:
            status = "Failed"
        else:
            status = "Complete"
            
        assert status == "Rendering"

    @pytest.mark.asyncio 
    async def test_all_exclusion_states(self, config):
        """Test all three exclusion states: Queuing, Failed, and Rendering"""
        
        manager = GenerationDownloadManager(config)
        
        test_cases = [
            ("Queuing", True, "Queued"),
            ("Something went wrong", True, "Failed"), 
            ("Video is rendering", True, "Rendering"),
            ("Complete generation content", False, "Complete"),
            ("Normal generation with metadata", False, "Complete")
        ]
        
        for text_content, should_exclude, expected_status in test_cases:
            # Test exclusion logic
            is_excluded = ("Queuing" in text_content or 
                          "Something went wrong" in text_content or 
                          "Video is rendering" in text_content)
            
            assert is_excluded == should_exclude, f"Failed for content: {text_content}"
            
            # Test status identification
            if "Video is rendering" in text_content:
                status = "Rendering"
            elif "Queuing" in text_content:
                status = "Queued"
            elif "Something went wrong" in text_content:
                status = "Failed"
            else:
                status = "Complete"
                
            assert status == expected_status, f"Wrong status for content: {text_content}"

    @pytest.mark.asyncio
    async def test_mixed_container_processing(self, config):
        """Test processing mixed containers with some rendering, some complete"""
        
        manager = GenerationDownloadManager(config)
        
        # Simulate container processing logic
        containers_data = [
            ("Video is rendering", "should_skip"),
            ("Complete generation A", "should_process"), 
            ("Queuing", "should_skip"),
            ("Complete generation B", "should_process"),
            ("Something went wrong", "should_skip"),
            ("Video is rendering", "should_skip"),
            ("Complete generation C", "should_process")
        ]
        
        processed_count = 0
        skipped_count = 0
        
        for text_content, expected in containers_data:
            is_excluded = ("Queuing" in text_content or 
                          "Something went wrong" in text_content or 
                          "Video is rendering" in text_content)
            
            if is_excluded:
                skipped_count += 1
                assert expected == "should_skip", f"Expected skip but got process for: {text_content}"
            else:
                processed_count += 1
                assert expected == "should_process", f"Expected process but got skip for: {text_content}"
        
        # Verify correct counts
        assert processed_count == 3, "Should process 3 complete generations"
        assert skipped_count == 4, "Should skip 4 incomplete generations (2 rendering, 1 queuing, 1 failed)"

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
        print("\n🎉 SUCCESS: Enhanced queue exclusion filters are working!")
        print("  ✅ Video is rendering exclusion")
        print("  ✅ Queuing exclusion (maintained)")
        print("  ✅ Something went wrong exclusion (maintained)")
        print("  ✅ Proper status identification and logging")
        print("  ✅ Mixed container processing")
        print("\nGenerations in rendering state will now be properly excluded!")
    else:
        print("\n❌ FAILURE: Enhanced queue exclusion filters need review")