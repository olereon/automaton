#!/usr/bin/env python3
"""
Integration Tests for Metadata Extraction Fixes

End-to-end tests that validate the complete metadata extraction workflow.
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, call
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager,
    GenerationDownloadConfig,
    GenerationMetadata
)


class MockFullPage:
    """Complete mock page that simulates real webpage behavior"""
    
    def __init__(self, scenario_data):
        self.scenario_data = scenario_data
        self.url = "https://test-generation-site.com/completed"
        self.current_thumbnail_index = 0
    
    async def title(self):
        return "Generation Site - Completed Tasks"
    
    async def query_selector_all(self, selector):
        """Return appropriate mock elements based on selector"""
        
        if "Creation Time" in selector:
            # Return Creation Time elements for each thumbnail
            elements = []
            for thumbnail in self.scenario_data.get("thumbnails", []):
                elements.append(MockCreationTimeElement(
                    thumbnail["creation_date"]
                ))
            return elements
        
        elif "aria-describedby" in selector:
            # Return prompt elements
            elements = []
            for thumbnail in self.scenario_data.get("thumbnails", []):
                elements.append(MockPromptElement(
                    thumbnail["prompt"],
                    attributes={"aria-describedby": f"tooltip-{thumbnail['id']}"}
                ))
            return elements
        
        elif "div" in selector:
            # Return div containers for prompt pattern search
            containers = []
            for i, thumbnail in enumerate(self.scenario_data.get("thumbnails", [])):
                containers.append(MockDivContainer(
                    thumbnail["prompt"],
                    pattern_match="</span>..." in thumbnail.get("html_content", "")
                ))
            return containers
        
        elif ".thumsItem" in selector or ".thumbnail-item" in selector:
            # Return thumbnail elements
            elements = []
            for thumbnail in self.scenario_data.get("thumbnails", []):
                elements.append(MockThumbnailElement(
                    thumbnail["id"],
                    visible=True
                ))
            return elements
        
        return []
    
    async def click(self, selector, timeout=5000):
        """Simulate clicking on elements"""
        if "thumsItem" in selector or "thumbnail-item" in selector:
            # Extract thumbnail index from selector
            if "nth-child" in selector:
                import re
                match = re.search(r'nth-child\((\d+)\)', selector)
                if match:
                    self.current_thumbnail_index = int(match.group(1)) - 1
        await asyncio.sleep(0.1)  # Simulate click delay
    
    async def wait_for_timeout(self, timeout):
        """Simulate waiting"""
        await asyncio.sleep(timeout / 1000.0)
    
    async def wait_for_selector(self, selector, timeout=5000):
        """Simulate waiting for selector"""
        await asyncio.sleep(0.1)
        return MockElement()
    
    async def is_visible(self, selector):
        """Check if element is visible"""
        return True
    
    async def evaluate(self, script):
        """Execute JavaScript"""
        if "innerText" in script or "textContent" in script:
            return "Page content with Creation Time and prompts"
        return {}


class MockCreationTimeElement:
    """Mock Creation Time element"""
    
    def __init__(self, date):
        self.date = date
    
    async def text_content(self):
        return "Creation Time"
    
    async def is_visible(self):
        return True
    
    async def evaluate_handle(self, script):
        return MockElementHandle(self.date)


class MockElementHandle:
    """Mock element handle for parent traversal"""
    
    def __init__(self, date):
        self.date = date
    
    async def query_selector_all(self, selector):
        if "span" in selector:
            return [
                MockElement(text="Creation Time"),
                MockElement(text=self.date)
            ]
        return []


class MockPromptElement:
    """Mock prompt element"""
    
    def __init__(self, prompt, attributes=None):
        self.prompt = prompt
        self.attributes = attributes or {}
    
    async def text_content(self):
        return self.prompt
    
    async def is_visible(self):
        return True
    
    async def get_attribute(self, name):
        return self.attributes.get(name)
    
    async def evaluate(self, script):
        if "innerText" in script:
            return self.prompt
        return self.prompt


class MockDivContainer:
    """Mock div container for pattern search"""
    
    def __init__(self, prompt, pattern_match=False):
        self.prompt = prompt
        self.pattern_match = pattern_match
    
    async def evaluate(self, script):
        if "innerHTML" in script:
            if self.pattern_match:
                return f'<span aria-describedby="tooltip">content</span>...'
            return f'<span>{self.prompt}</span>'
        return ""
    
    async def query_selector_all(self, selector):
        if "aria-describedby" in selector:
            return [MockPromptElement(self.prompt)]
        return []


class MockThumbnailElement:
    """Mock thumbnail element"""
    
    def __init__(self, thumbnail_id, visible=True):
        self.thumbnail_id = thumbnail_id
        self.visible = visible
    
    async def is_visible(self):
        return self.visible
    
    async def click(self):
        await asyncio.sleep(0.1)


class MockElement:
    """Generic mock element"""
    
    def __init__(self, text="", visible=True):
        self.text = text
        self.visible = visible
    
    async def text_content(self):
        return self.text
    
    async def is_visible(self):
        return self.visible


class TestIntegrationMetadataFixes:
    """Integration test suite for metadata extraction fixes"""

    @pytest.fixture
    def integration_config(self):
        """Create configuration for integration tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield GenerationDownloadConfig(
                downloads_folder=f"{temp_dir}/downloads",
                logs_folder=f"{temp_dir}/logs",
                creation_time_text="Creation Time",
                prompt_ellipsis_pattern="</span>...",
                use_descriptive_naming=True,
                unique_id="integration_test",
                max_downloads=5
            )

    @pytest.mark.asyncio
    async def test_complete_metadata_extraction_workflow(self, integration_config):
        """Test the complete metadata extraction workflow for multiple thumbnails"""
        
        # Create scenario with multiple thumbnails having different metadata
        scenario_data = {
            "thumbnails": [
                {
                    "id": 1,
                    "creation_date": "24 Aug 2025 01:37:01",
                    "prompt": "A majestic giant frost camera in a mystical forest setting",
                    "html_content": "<span aria-describedby='tooltip-1'>content</span>..."
                },
                {
                    "id": 2, 
                    "creation_date": "23 Aug 2025 15:42:13",
                    "prompt": "Ethereal blue dragon soaring through cloudy mountains",
                    "html_content": "<span aria-describedby='tooltip-2'>content</span>..."
                },
                {
                    "id": 3,
                    "creation_date": "22 Aug 2025 09:15:30", 
                    "prompt": "Cyberpunk cityscape with neon lights and flying cars",
                    "html_content": "<span aria-describedby='tooltip-3'>content</span>..."
                }
            ]
        }
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        # Test metadata extraction for each thumbnail
        extracted_metadata = []
        
        for i, expected_thumbnail in enumerate(scenario_data["thumbnails"]):
            # Simulate clicking on the thumbnail
            await mock_page.click(f".thumsItem:nth-child({i+1})")
            
            # Extract metadata
            metadata = await manager.extract_metadata_from_page(mock_page)
            
            assert metadata is not None
            extracted_metadata.append(metadata)
            
            # Validate extracted data matches expected
            assert expected_thumbnail["creation_date"] in metadata["generation_date"]
            assert expected_thumbnail["prompt"] == metadata["prompt"]
        
        # Verify each thumbnail got different metadata
        dates = [m["generation_date"] for m in extracted_metadata]
        prompts = [m["prompt"] for m in extracted_metadata]
        
        assert len(set(dates)) == 3, "Each thumbnail should have a different date"
        assert len(set(prompts)) == 3, "Each thumbnail should have a different prompt"

    @pytest.mark.asyncio
    async def test_smart_date_selection_integration(self, integration_config):
        """Test smart date selection when multiple dates are visible"""
        
        # Scenario with overlapping dates (common in real usage)
        scenario_data = {
            "thumbnails": [
                {
                    "id": 1,
                    "creation_date": "24 Aug 2025 01:37:01",
                    "prompt": "First generation",
                    "html_content": "<span aria-describedby='tooltip-1'>content</span>..."
                },
                {
                    "id": 2,
                    "creation_date": "24 Aug 2025 01:37:01",  # Same date (common case)
                    "prompt": "Second generation", 
                    "html_content": "<span aria-describedby='tooltip-2'>content</span>..."
                },
                {
                    "id": 3,
                    "creation_date": "23 Aug 2025 15:42:13",  # Different date
                    "prompt": "Third generation",
                    "html_content": "<span aria-describedby='tooltip-3'>content</span>..."
                }
            ]
        }
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        # Mock the smart selection methods
        with patch.object(manager, '_find_selected_thumbnail_date') as mock_find_selected:
            with patch.object(manager, '_select_best_date_candidate') as mock_best_candidate:
                
                # Test scenario 1: Selected thumbnail found
                mock_find_selected.return_value = "23 Aug 2025 15:42:13"
                
                metadata = await manager.extract_metadata_from_page(mock_page)
                assert metadata["generation_date"] == "23 Aug 2025 15:42:13"
                
                # Test scenario 2: No selected thumbnail, use smart selection
                mock_find_selected.return_value = None
                mock_best_candidate.return_value = "24 Aug 2025 01:37:01"
                
                metadata = await manager.extract_metadata_from_page(mock_page)
                assert metadata["generation_date"] == "24 Aug 2025 01:37:01"

    @pytest.mark.asyncio
    async def test_file_naming_integration(self, integration_config):
        """Test complete file naming workflow with extracted metadata"""
        
        scenario_data = {
            "thumbnails": [
                {
                    "id": 1,
                    "creation_date": "24 Aug 2025 01:37:01",
                    "prompt": "Test prompt for file naming",
                    "html_content": "<span aria-describedby='tooltip-1'>content</span>..."
                }
            ]
        }
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        # Mock file operations
        test_file_path = Path("/tmp/downloaded_file.mp4")
        
        with patch.object(manager.file_manager, 'rename_file') as mock_rename:
            mock_rename.return_value = Path("/tmp/vid_2025-08-24-01-37-01_integration_test.mp4")
            
            # Extract metadata
            metadata = await manager.extract_metadata_from_page(mock_page)
            
            # Test file renaming
            renamed_file = manager.file_manager.rename_file(
                test_file_path,
                creation_date=metadata["generation_date"]
            )
            
            # Verify file naming used extracted metadata
            mock_rename.assert_called_once()
            call_args = mock_rename.call_args
            assert call_args[1]["creation_date"] == "24 Aug 2025 01:37:01"

    @pytest.mark.asyncio 
    async def test_debug_logging_integration(self, integration_config):
        """Test debug logging throughout the extraction process"""
        
        scenario_data = {
            "thumbnails": [
                {
                    "id": 1,
                    "creation_date": "24 Aug 2025 01:37:01",
                    "prompt": "Debug test prompt",
                    "html_content": "<span aria-describedby='tooltip-1'>content</span>..."
                }
            ]
        }
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        # Ensure debug logger is available
        assert manager.debug_logger is not None
        
        # Extract metadata (should trigger debug logging)
        metadata = await manager.extract_metadata_from_page(mock_page)
        
        # Verify debug information was logged
        debug_data = manager.debug_logger.debug_data
        
        assert len(debug_data["steps"]) > 0
        assert any(step["step_type"] == "METADATA_EXTRACTION_START" for step in debug_data["steps"])
        
        # Check that configuration was logged
        assert "use_descriptive_naming" in debug_data["configuration"]

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, integration_config):
        """Test error recovery throughout the extraction workflow"""
        
        class PartiallyFailingPage:
            """Mock page that fails some operations but succeeds others"""
            
            def __init__(self):
                self.call_count = 0
            
            @property
            def url(self):
                return "https://test-site.com"
            
            async def title(self):
                return "Test Page"
            
            async def query_selector_all(self, selector):
                self.call_count += 1
                
                if "Creation Time" in selector:
                    # Fail on first call, succeed on second
                    if self.call_count <= 1:
                        raise Exception("Network timeout")
                    return [MockCreationTimeElement("24 Aug 2025 01:37:01")]
                
                elif "aria-describedby" in selector:
                    return [MockPromptElement("Recovered prompt")]
                
                return []
        
        failing_page = PartiallyFailingPage()
        manager = GenerationDownloadManager(integration_config)
        
        # Should recover from partial failures
        metadata = await manager.extract_metadata_from_page(failing_page)
        
        # Should have recovered and extracted some metadata
        assert metadata is not None
        # Date extraction failed, so should get unknown
        assert metadata.get("generation_date") == "Unknown Date"
        # Prompt extraction should succeed
        assert metadata.get("prompt") == "Recovered prompt"

    @pytest.mark.asyncio
    async def test_thumbnail_click_validation_integration(self, integration_config):
        """Test thumbnail click validation in complete workflow"""
        
        scenario_data = {
            "thumbnails": [
                {
                    "id": 1,
                    "creation_date": "24 Aug 2025 01:37:01",
                    "prompt": "First thumbnail",
                    "html_content": "<span aria-describedby='tooltip-1'>content</span>..."
                },
                {
                    "id": 2,
                    "creation_date": "23 Aug 2025 15:42:13", 
                    "prompt": "Second thumbnail",
                    "html_content": "<span aria-describedby='tooltip-2'>content</span>..."
                }
            ]
        }
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        # Test clicking different thumbnails
        for i in range(len(scenario_data["thumbnails"])):
            # Simulate clicking thumbnail
            thumbnail_selector = f".thumsItem:nth-child({i+1})"
            
            with patch.object(mock_page, 'click') as mock_click:
                await mock_page.click(thumbnail_selector)
                
                # Validate page state changed
                state_changed = await manager.validate_page_state_changed(mock_page, i)
                assert state_changed is True
                
                # Validate content loaded
                content_loaded = await manager.validate_content_loaded_for_thumbnail(mock_page, i)
                assert content_loaded is True

    @pytest.mark.asyncio
    async def test_performance_integration(self, integration_config):
        """Test performance with realistic data volumes"""
        
        # Create scenario with many thumbnails
        scenario_data = {"thumbnails": []}
        for i in range(20):  # 20 thumbnails
            scenario_data["thumbnails"].append({
                "id": i + 1,
                "creation_date": f"2{i%2}{(i%12)+1:02d} Aug 2025 {i%24:02d}:{(i*7)%60:02d}:01",
                "prompt": f"Generated prompt number {i+1} with sufficient content for testing",
                "html_content": f"<span aria-describedby='tooltip-{i+1}'>content</span>..."
            })
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        # Test extraction performance
        start_time = datetime.now()
        
        extracted_metadata = []
        for i in range(5):  # Test first 5 thumbnails
            await mock_page.click(f".thumsItem:nth-child({i+1})")
            metadata = await manager.extract_metadata_from_page(mock_page)
            extracted_metadata.append(metadata)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete reasonably quickly
        assert duration < 2.0, f"Extraction took too long: {duration}s"
        
        # Verify all extractions succeeded
        assert len(extracted_metadata) == 5
        assert all(m is not None for m in extracted_metadata)

    @pytest.mark.asyncio
    async def test_concurrent_extraction_integration(self, integration_config):
        """Test concurrent metadata extraction scenarios"""
        
        import asyncio
        
        scenario_data = {
            "thumbnails": [
                {
                    "id": i + 1,
                    "creation_date": f"24 Aug 2025 {i:02d}:37:01",
                    "prompt": f"Concurrent test prompt {i+1}",
                    "html_content": f"<span aria-describedby='tooltip-{i+1}'>content</span>..."
                }
                for i in range(3)
            ]
        }
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        async def extract_for_thumbnail(thumbnail_index):
            """Extract metadata for a specific thumbnail"""
            await mock_page.click(f".thumsItem:nth-child({thumbnail_index+1})")
            return await manager.extract_metadata_from_page(mock_page)
        
        # Run concurrent extractions
        tasks = [
            extract_for_thumbnail(i) for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent access gracefully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 2, "Should handle most concurrent requests"
        
        # Verify results are valid
        for result in successful_results:
            assert result is not None
            assert "generation_date" in result
            assert "prompt" in result

    def test_configuration_validation_integration(self, integration_config):
        """Test that configuration validation works in complete workflow"""
        
        # Test with various configuration scenarios
        configs_to_test = [
            # Valid configuration
            GenerationDownloadConfig(use_descriptive_naming=True, unique_id="test"),
            
            # Configuration with fallbacks
            GenerationDownloadConfig(use_descriptive_naming=False, unique_id=""),
            
            # Configuration with edge case values
            GenerationDownloadConfig(max_downloads=0, download_timeout=1)
        ]
        
        for config in configs_to_test:
            # Should create manager without crashing
            manager = GenerationDownloadManager(config)
            assert manager is not None
            
            # Should handle configuration gracefully
            status = manager.get_status()
            assert isinstance(status, dict)
            assert "downloads_completed" in status

    @pytest.mark.asyncio
    async def test_memory_management_integration(self, integration_config):
        """Test memory management throughout extraction workflow"""
        
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create large scenario
        scenario_data = {"thumbnails": []}
        for i in range(50):
            scenario_data["thumbnails"].append({
                "id": i + 1,
                "creation_date": f"24 Aug 2025 {i%24:02d}:37:01",
                "prompt": "A" * 1000,  # Large prompt
                "html_content": f"<span aria-describedby='tooltip-{i+1}'>{'X' * 500}</span>..."
            })
        
        mock_page = MockFullPage(scenario_data)
        manager = GenerationDownloadManager(integration_config)
        
        # Perform multiple extractions
        for i in range(10):
            await mock_page.click(f".thumsItem:nth-child({i+1})")
            metadata = await manager.extract_metadata_from_page(mock_page)
            
            # Force garbage collection periodically
            if i % 5 == 0:
                gc.collect()
        
        gc.collect()
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        assert memory_increase < 50 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.2f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])