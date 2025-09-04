#!/usr/bin/env python3.11

"""
Test for the metadata extraction variable scope fix.

This test verifies that the 'metadata_candidates' UnboundLocalError
has been fixed when using single container optimization path.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig, DuplicateMode

class TestMetadataExtractionVariableScope:
    """Test variable scope fix in metadata extraction"""

    @pytest.fixture
    def config(self, tmp_path):
        """Standard configuration for testing"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            duplicate_mode=DuplicateMode.SKIP,
            creation_time_text="Creation Time",
            max_downloads=100
        )

    def create_mock_single_inspiration_span(self):
        """Create mock single inspiration span that triggers optimization path"""
        inspiration_span = AsyncMock()
        inspiration_span.is_visible.return_value = True
        inspiration_span.text_content.return_value = "Inspiration Mode"
        inspiration_span.get_attribute.return_value = "inspiration-class"
        
        # Mock parent element
        parent = AsyncMock()
        inspiration_span.evaluate_handle.return_value = parent
        
        return inspiration_span, parent

    def create_mock_metadata_container(self, creation_date="03 Sep 2025 16:15:18"):
        """Create mock metadata container"""
        container = AsyncMock()
        container_info = {
            'creation_date': creation_date,
            'text_length': 200,
            'valid': True
        }
        return container, container_info

    @pytest.mark.asyncio
    async def test_single_container_optimization_no_variable_error(self, config):
        """
        Test that single container optimization doesn't cause UnboundLocalError 
        for metadata_candidates variable.
        
        This reproduces the exact scenario from the user's logs:
        - Single visible 'Inspiration Mode' container found
        - Single container optimization path is taken
        - metadata_candidates should be properly initialized and not cause errors
        """
        
        manager = GenerationDownloadManager(config)
        mock_page = AsyncMock()
        
        # Create single inspiration mode span (triggers optimization path)
        inspiration_span, parent = self.create_mock_single_inspiration_span()
        
        # Mock page to return only one inspiration span (triggers single container optimization)
        mock_page.query_selector_all.return_value = [inspiration_span]
        
        # Mock successful metadata extraction from single container
        metadata_container, container_info = self.create_mock_metadata_container("03 Sep 2025 16:15:18")
        
        # Mock the landmark readiness check to pass
        landmark_checks = {
            'creation_time_visible': True,
            'prompt_visible': True,
            'thumbnail_selected': True
        }
        
        with patch.object(manager, '_perform_landmark_readiness_checks', return_value=landmark_checks):
            with patch.object(manager, '_search_creation_time_backwards', return_value=metadata_container):
                with patch.object(manager, '_analyze_metadata_container', return_value=container_info):
                    
                    # This should NOT raise UnboundLocalError: cannot access local variable 'metadata_candidates'
                    result = await manager.extract_metadata_with_landmark_strategy(mock_page, 0)
                    
                    # Should successfully extract metadata from single container
                    assert result is not None
                    assert result.get('generation_date') == "03 Sep 2025 16:15:18"

    @pytest.mark.asyncio 
    async def test_multi_container_path_still_works(self, config):
        """
        Test that multi-container path still works correctly after variable scope fix.
        """
        
        manager = GenerationDownloadManager(config)
        mock_page = AsyncMock()
        
        # Create multiple inspiration spans (triggers multi-container path)
        inspiration_span_on, parent_on = self.create_mock_single_inspiration_span()
        dummy_span = AsyncMock()
        dummy_span.is_visible.return_value = False
        
        # Mock page to return multiple spans (avoids single container optimization)
        mock_page.query_selector_all.return_value = [inspiration_span_on, dummy_span]
        
        # Mock parent spans for the multi-container approach  
        mode_span = AsyncMock()
        mode_span.text_content.return_value = "On"
        mode_span.get_attribute.return_value = "mode-class"
        parent_on.query_selector_all.return_value = [inspiration_span_on, mode_span]
        
        # Mock successful metadata extraction
        metadata_container, container_info = self.create_mock_metadata_container("03 Sep 2025 16:20:00")
        
        # Mock the landmark readiness check to pass
        landmark_checks = {
            'creation_time_visible': True,
            'prompt_visible': True,
            'thumbnail_selected': True
        }
        
        with patch.object(manager, '_perform_landmark_readiness_checks', return_value=landmark_checks):
            with patch.object(manager, '_search_creation_time_backwards', return_value=metadata_container):
                with patch.object(manager, '_analyze_metadata_container', return_value=container_info):
                    
                    result = await manager.extract_metadata_with_landmark_strategy(mock_page, 0)
                    
                    # Should successfully extract metadata from multi-container approach
                    assert result is not None
                    assert result.get('generation_date') == "03 Sep 2025 16:20:00"

    @pytest.mark.asyncio
    async def test_boundary_scenario_reproduction(self, config):
        """
        Test the exact boundary scenario that was failing:
        - Single Inspiration Mode container found
        - Single container optimization succeeds in date extraction
        - No UnboundLocalError when accessing metadata_candidates
        """
        
        manager = GenerationDownloadManager(config)
        mock_page = AsyncMock()
        
        # Simulate the exact boundary scenario from logs
        inspiration_span, parent = self.create_mock_single_inspiration_span()
        mock_page.query_selector_all.return_value = [inspiration_span]
        
        # Mock successful boundary metadata extraction
        boundary_container, boundary_info = self.create_mock_metadata_container("03 Sep 2025 16:15:18")
        
        landmark_checks = {'creation_time_visible': True, 'prompt_visible': True, 'thumbnail_selected': True}
        
        with patch.object(manager, '_perform_landmark_readiness_checks', return_value=landmark_checks):
            with patch.object(manager, '_search_creation_time_backwards', return_value=boundary_container):
                with patch.object(manager, '_analyze_metadata_container', return_value=boundary_info):
                    
                    # This reproduces the exact failure scenario from user logs
                    result = await manager.extract_metadata_with_landmark_strategy(mock_page, -1)
                    
                    # Should succeed without UnboundLocalError and extract boundary generation
                    assert result is not None
                    assert result.get('generation_date') == "03 Sep 2025 16:15:18"
                    
                    print("✅ Boundary generation metadata extraction succeeds without variable errors")

def run_tests():
    """Run the tests directly"""
    import subprocess
    result = subprocess.run(['python3.11', '-m', 'pytest', __file__, '-v', '-s'], 
                          capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr) 
    print("Return code:", result.returncode)
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n🎉 SUCCESS: Metadata extraction variable scope fix is working!")
        print("  ✅ Single container optimization path works without UnboundLocalError")
        print("  ✅ Multi-container path still works correctly")
        print("  ✅ Boundary scenario reproduction succeeds")
        print("  ✅ metadata_candidates variable properly initialized")
        print("\nThe boundary generation at 03 Sep 2025 16:15:18 should now download successfully!")
    else:
        print("\n❌ FAILURE: Metadata extraction variable scope fix needs review")