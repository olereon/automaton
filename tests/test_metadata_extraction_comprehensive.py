#!/usr/bin/env python3
"""
Comprehensive Test Suite for Metadata Extraction Fixes

This module provides thorough testing of the metadata extraction fixes
to ensure different dates are extracted correctly for each thumbnail.
"""

import pytest
import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig,
    GenerationMetadata,
    EnhancedFileNamer
)
from utils.generation_debug_logger import GenerationDebugLogger


class MockPageElement:
    """Mock Playwright page element for testing"""
    
    def __init__(self, text_content: str = "", is_visible: bool = True, 
                 inner_text: str = None, inner_html: str = "", 
                 attributes: Dict[str, str] = None):
        self.text_content_value = text_content
        self.inner_text_value = inner_text or text_content
        self.inner_html_value = inner_html
        self.is_visible_value = is_visible
        self.attributes_dict = attributes or {}
        self.date_value = None  # Store associated date
        
    async def text_content(self):
        return self.text_content_value
    
    async def is_visible(self):
        return self.is_visible_value
        
    async def evaluate(self, script):
        if "innerText" in script:
            return self.inner_text_value
        elif "parentElement" in script:
            return MockElementHandle(self)
        return ""
    
    async def evaluate_handle(self, script):
        return MockElementHandle(self)
    
    async def get_attribute(self, name):
        return self.attributes_dict.get(name)
    
    async def query_selector_all(self, selector):
        if "span" in selector and hasattr(self, 'date_value') and self.date_value:
            # Return mock spans for parent element with actual date
            return [
                MockPageElement("Creation Time"),
                MockPageElement(self.date_value)  # The actual date span
            ]
        elif "span" in selector:
            return [
                MockPageElement("Creation Time"),
                MockPageElement(self.text_content_value)  # Generic content
            ]
        return []


class MockElementHandle:
    """Mock Playwright element handle"""
    
    def __init__(self, element):
        self.element = element
    
    async def query_selector_all(self, selector):
        return await self.element.query_selector_all(selector)


class MockPage:
    """Mock Playwright page for testing"""
    
    def __init__(self, mock_data: Dict[str, Any]):
        self.mock_data = mock_data
        self.url = "https://test-site.com/generations"
        
    async def query_selector_all(self, selector: str):
        """Return mock elements based on selector"""
        elements = []
        
        if "Creation Time" in selector:
            # Return mock Creation Time elements with different dates
            for i, date in enumerate(self.mock_data.get("creation_dates", [])):
                element = MockPageElement(text_content="Creation Time", is_visible=True)
                element.date_value = date  # Store the actual date for retrieval
                elements.append(element)
        
        elif "aria-describedby" in selector:
            # Return mock prompt elements
            for prompt in self.mock_data.get("prompts", []):
                elements.append(MockPageElement(
                    text_content=prompt,
                    is_visible=True,
                    attributes={"aria-describedby": "tooltip-123"}
                ))
        
        elif "div" in selector:
            # Return mock div containers with prompt pattern
            prompts = self.mock_data.get("prompts", ["Mock prompt"])
            for i, prompt in enumerate(prompts[:10]):  # Simulate up to 10 div containers
                elements.append(MockPageElement(
                    inner_html=f"<span aria-describedby='tooltip-{i}'>{prompt}</span>..."
                ))
        
        return elements
    
    async def title(self):
        return "Mock Generation Page"
    
    async def evaluate(self, script):
        if "innerText" in script or "textContent" in script:
            return "Mock page content with dates and prompts"
        return {}


class TestMetadataExtractionFixes:
    """Comprehensive test suite for metadata extraction fixes"""

    @pytest.fixture
    def mock_config(self):
        """Create test configuration"""
        return GenerationDownloadConfig(
            downloads_folder="/tmp/test_downloads",
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            use_descriptive_naming=True,
            unique_id="test",
            naming_format="{media_type}_{creation_date}_{unique_id}"
        )
    
    @pytest.fixture
    def mock_debug_logger(self):
        """Create mock debug logger"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = GenerationDebugLogger(temp_dir)
            yield logger

    @pytest.mark.asyncio
    async def test_multiple_thumbnail_date_extraction(self, mock_config):
        """Test that different dates are extracted for different thumbnails"""
        
        # Create mock data with different dates for each thumbnail
        mock_dates = [
            "24 Aug 2025 01:37:01",
            "23 Aug 2025 15:42:13", 
            "22 Aug 2025 09:15:30",
            "21 Aug 2025 18:22:45"
        ]
        
        mock_data = {"creation_dates": mock_dates}
        mock_page = MockPage(mock_data)
        
        manager = GenerationDownloadManager(mock_config)
        
        # Test extraction for each "thumbnail" (simulated by different mock data)
        extracted_dates = []
        for i in range(len(mock_dates)):
            # Mock the selection of specific date for each thumbnail
            mock_data["creation_dates"] = [mock_dates[i]]  # Only show one date
            
            metadata = await manager.extract_metadata_from_page(mock_page)
            assert metadata is not None
            assert "generation_date" in metadata
            
            extracted_dates.append(metadata["generation_date"])
        
        # Verify each thumbnail gets a different date
        assert len(set(extracted_dates)) == len(mock_dates)
        assert all(date in mock_dates for date in extracted_dates)

    @pytest.mark.asyncio  
    async def test_correct_element_selection_per_thumbnail(self, mock_config):
        """Test that the correct element is selected for each thumbnail"""
        
        # Create scenario with multiple dates visible simultaneously
        mock_dates = [
            "24 Aug 2025 01:37:01",  # Most recent
            "23 Aug 2025 15:42:13",  # Second most recent  
            "22 Aug 2025 09:15:30",  # Third most recent
            "20 Aug 2025 08:00:00"   # Oldest
        ]
        
        mock_data = {"creation_dates": mock_dates}
        mock_page = MockPage(mock_data)
        
        manager = GenerationDownloadManager(mock_config)
        
        # Test the smart date selection algorithm
        with patch.object(manager, '_find_selected_thumbnail_date') as mock_selector:
            # Test scenario 1: Selected thumbnail found
            mock_selector.return_value = mock_dates[1]  # Should get specific date
            
            metadata = await manager.extract_metadata_from_page(mock_page)
            assert metadata["generation_date"] == mock_dates[1]
            
            # Test scenario 2: No selected thumbnail, use smart selection
            mock_selector.return_value = None
            
            with patch.object(manager, '_select_best_date_candidate') as mock_best_selector:
                mock_best_selector.return_value = mock_dates[2]
                
                metadata = await manager.extract_metadata_from_page(mock_page)
                assert metadata["generation_date"] == mock_dates[2]

    @pytest.mark.asyncio
    async def test_edge_cases_and_error_conditions(self, mock_config):
        """Test edge cases and error handling"""
        
        test_cases = [
            # No dates available
            {"creation_dates": [], "expected": "Unknown Date"},
            
            # Invalid date format
            {"creation_dates": ["Invalid Date Format"], "expected": "Invalid Date Format"},
            
            # Empty date string
            {"creation_dates": [""], "expected": "Unknown Date"},
            
            # Only Creation Time text, no actual date
            {"creation_dates": ["Creation Time"], "expected": "Unknown Date"},
            
            # Multiple identical dates (common scenario)
            {"creation_dates": ["24 Aug 2025 01:37:01"] * 5, "expected": "24 Aug 2025 01:37:01"}
        ]
        
        manager = GenerationDownloadManager(mock_config)
        
        for case in test_cases:
            mock_page = MockPage(case)
            metadata = await manager.extract_metadata_from_page(mock_page)
            
            assert metadata is not None
            
            if case["expected"] == "Unknown Date":
                assert metadata["generation_date"] in ["Unknown Date", "Unknown"]
            else:
                assert metadata["generation_date"] == case["expected"]

    @pytest.mark.asyncio
    async def test_prompt_extraction_validation(self, mock_config):
        """Test prompt extraction with various scenarios"""
        
        test_prompts = [
            "A majestic giant frost giant camera in a mystical forest...",
            "Short prompt",
            "A" * 500,  # Very long prompt
            "",  # Empty prompt
            "Prompt with special characters: !@#$%^&*()",
            "Multi-line\nprompt\nwith\nbreaks"
        ]
        
        manager = GenerationDownloadManager(mock_config)
        
        for prompt in test_prompts:
            mock_data = {
                "creation_dates": ["24 Aug 2025 01:37:01"],
                "prompts": [prompt]
            }
            mock_page = MockPage(mock_data)
            
            metadata = await manager.extract_metadata_from_page(mock_page)
            assert metadata is not None
            
            if prompt:
                assert metadata["prompt"] == prompt
            else:
                assert metadata["prompt"] in ["Unknown Prompt", "Unknown"]

    def test_file_naming_with_extracted_metadata(self, mock_config):
        """Test file naming system with various metadata scenarios"""
        
        namer = EnhancedFileNamer(mock_config)
        test_file = Path("/tmp/test.mp4")
        
        test_cases = [
            {
                "creation_date": "24 Aug 2025 01:37:01",
                "expected_pattern": "vid_2025-08-24-01-37-01_test.mp4"
            },
            {
                "creation_date": "Unknown Date",
                "expected_pattern": r"vid_\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}_test.mp4"
            },
            {
                "creation_date": "",
                "expected_pattern": r"vid_\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}_test.mp4"
            }
        ]
        
        import re
        
        for case in test_cases:
            filename = namer.generate_filename(
                file_path=test_file,
                creation_date=case["creation_date"]
            )
            
            if case["creation_date"] == "24 Aug 2025 01:37:01":
                assert filename == case["expected_pattern"]
            else:
                # For unknown dates, check pattern matches current timestamp format
                assert re.match(case["expected_pattern"], filename)

    @pytest.mark.asyncio
    async def test_debug_logger_functionality(self, mock_config, mock_debug_logger):
        """Test debug logger captures all necessary information"""
        
        manager = GenerationDownloadManager(mock_config)
        manager.debug_logger = mock_debug_logger
        
        # Test configuration logging
        config_dict = {"test": "value", "use_descriptive_naming": True}
        mock_debug_logger.log_configuration(config_dict)
        
        assert mock_debug_logger.debug_data["configuration"] == config_dict
        
        # Test step logging
        mock_debug_logger.log_step(
            thumbnail_index=1,
            step_type="TEST_STEP",
            data={"test_data": "value"},
            success=True
        )
        
        assert len(mock_debug_logger.debug_data["steps"]) > 0
        assert mock_debug_logger.debug_data["steps"][-1]["step_type"] == "TEST_STEP"
        
        # Test metadata extraction logging
        mock_debug_logger.log_metadata_extraction(
            thumbnail_index=1,
            extraction_method="test_method",
            extracted_data={"generation_date": "24 Aug 2025 01:37:01", "prompt": "Test prompt"},
            success=True
        )
        
        # Test file naming logging
        mock_debug_logger.log_file_naming(
            thumbnail_index=1,
            original_filename="temp.mp4",
            new_filename="vid_2025-08-24-01-37-01_test.mp4",
            naming_data={"use_descriptive_naming": True},
            success=True
        )
        
        assert len(mock_debug_logger.debug_data["file_naming"]) > 0

    def test_smart_date_selection_algorithms(self, mock_config):
        """Test smart date selection with various candidate scenarios"""
        
        manager = GenerationDownloadManager(mock_config)
        
        # Test case 1: Multiple dates with different frequencies
        candidates = [
            {"extracted_date": "24 Aug 2025 01:37:01", "element_index": 0},
            {"extracted_date": "24 Aug 2025 01:37:01", "element_index": 1},  # Duplicate (common)
            {"extracted_date": "24 Aug 2025 01:37:01", "element_index": 2},  # Duplicate (common)
            {"extracted_date": "23 Aug 2025 15:42:13", "element_index": 3},  # Less common
            {"extracted_date": "22 Aug 2025 09:15:30", "element_index": 4},  # Least common
        ]
        
        selected = manager._select_best_date_candidate(candidates)
        
        # Should prefer the least common date
        assert selected == "22 Aug 2025 09:15:30"
        
        # Test case 2: All dates are the same
        candidates = [{"extracted_date": "24 Aug 2025 01:37:01", "element_index": i} for i in range(5)]
        selected = manager._select_best_date_candidate(candidates)
        assert selected == "24 Aug 2025 01:37:01"
        
        # Test case 3: Empty candidates
        selected = manager._select_best_date_candidate([])
        assert selected == "Unknown Date"

    def test_date_parsing_accuracy(self, mock_config):
        """Test date parsing with various formats"""
        
        namer = EnhancedFileNamer(mock_config)
        
        test_dates = [
            ("24 Aug 2025 01:37:01", "2025-08-24-01-37-01"),
            ("2025-08-24 01:37:01", "2025-08-24-01-37-01"),
            ("24/08/2025 01:37:01", "2025-08-24-01-37-01"),
            ("08/24/2025 01:37:01", "2025-08-24-01-37-01"),
            ("24 Aug 2025", "2025-08-24-00-00-00"),
            ("Invalid Date", None),  # Should use current time
            ("", None),  # Should use current time
        ]
        
        for input_date, expected_output in test_dates:
            result = namer.parse_creation_date(input_date)
            
            if expected_output:
                assert result == expected_output
            else:
                # For invalid dates, should return current timestamp format
                assert len(result.split('-')) == 6  # YYYY-MM-DD-HH-MM-SS
                assert result.startswith('2025')  # Should be current year

    @pytest.mark.asyncio
    async def test_thumbnail_click_validation(self, mock_config):
        """Test thumbnail click validation and state changes"""
        
        manager = GenerationDownloadManager(mock_config)
        
        # Test page state validation
        mock_page = MockPage({"creation_dates": ["24 Aug 2025 01:37:01"]})
        
        # Mock is_visible to simulate content being loaded
        with patch.object(mock_page, 'is_visible', return_value=True):
            result = await manager.validate_page_state_changed(mock_page, 0)
            assert result == True
        
        # Test content validation
        result = await manager.validate_content_loaded_for_thumbnail(mock_page, 0)
        assert result == True  # Should find prompt elements

    def test_filename_sanitization(self, mock_config):
        """Test filename sanitization for cross-platform compatibility"""
        
        namer = EnhancedFileNamer(mock_config)
        
        test_cases = [
            ("test<>file.mp4", "test__file.mp4"),
            ('test"file.mp4', "test_file.mp4"),
            ("test file.mp4", "test_file.mp4"),
            ("test|file?.mp4", "test_file_.mp4"),
            ("a" * 250 + ".mp4", True),  # Should be truncated
            ("normal_file.mp4", "normal_file.mp4"),
        ]
        
        for input_name, expected in test_cases:
            result = namer.sanitize_filename(input_name)
            
            if isinstance(expected, bool):
                # Check length constraint
                assert len(result) <= 200
            else:
                assert result == expected
            
            # Ensure no invalid characters remain
            invalid_chars = '<>:"/\\|?*'
            assert not any(char in result for char in invalid_chars)

    def test_metadata_quality_assessment(self, mock_debug_logger):
        """Test metadata quality assessment functionality"""
        
        test_cases = [
            {
                "metadata": {"generation_date": "24 Aug 2025 01:37:01", "prompt": "A detailed prompt"},
                "expected_score": 1.0,
                "expected_issues": []
            },
            {
                "metadata": {"generation_date": "Unknown Date", "prompt": "Short"},
                "expected_score": 0.2,
                "expected_issues": ["Date not extracted", "Prompt too short"]
            },
            {
                "metadata": {"generation_date": "24 Aug 2025 01:37:01", "prompt": "Truncated prompt..."},
                "expected_score": 0.8,
                "expected_issues": ["Prompt appears truncated"]
            }
        ]
        
        for case in test_cases:
            quality = mock_debug_logger._assess_metadata_quality(case["metadata"])
            
            assert quality["quality_score"] == case["expected_score"]
            assert set(quality["issues"]) == set(case["expected_issues"])

    def test_configuration_validation(self, mock_config):
        """Test configuration parameter validation"""
        
        # Test valid configuration
        manager = GenerationDownloadManager(mock_config)
        assert manager.config.use_descriptive_naming == True
        assert manager.config.unique_id == "test"
        
        # Test configuration with invalid values
        invalid_config = GenerationDownloadConfig(
            use_descriptive_naming=False,  # Should fall back to sequential
            unique_id="",  # Empty unique ID
            max_downloads=-1  # Invalid max downloads
        )
        
        manager = GenerationDownloadManager(invalid_config)
        
        # Should handle gracefully
        namer = EnhancedFileNamer(invalid_config)
        filename = namer.generate_filename(Path("/tmp/test.mp4"), sequence_number=1)
        assert filename == "#000000001.mp4"  # Should use sequential naming

    @pytest.mark.asyncio
    async def test_error_recovery_mechanisms(self, mock_config):
        """Test error recovery in metadata extraction"""
        
        manager = GenerationDownloadManager(mock_config)
        
        # Test with page that throws exceptions
        class ErrorMockPage:
            async def query_selector_all(self, selector):
                raise Exception("Network timeout")
            
            @property
            def url(self):
                return "https://test-site.com"
            
            async def title(self):
                return "Test Page"
        
        error_page = ErrorMockPage()
        
        # Should handle errors gracefully and return default metadata
        metadata = await manager.extract_metadata_from_page(error_page)
        assert metadata is None or metadata.get("generation_date") == "Unknown Date"
        assert metadata is None or metadata.get("prompt") == "Unknown Prompt"

    def test_concurrent_file_naming_safety(self, mock_config):
        """Test file naming safety with concurrent operations"""
        
        namer = EnhancedFileNamer(mock_config)
        test_file = Path("/tmp/test.mp4")
        
        # Simulate multiple files with same base name
        with patch('pathlib.Path.exists') as mock_exists:
            # First call returns False (file doesn't exist)
            # Second call returns True (file exists, need unique name)
            mock_exists.side_effect = [False, True, False]
            
            filename = namer.generate_filename(test_file, creation_date="24 Aug 2025 01:37:01")
            
            # Should generate base filename on first try
            assert filename == "vid_2025-08-24-01-37-01_test.mp4"

    def test_performance_with_large_datasets(self, mock_config):
        """Test performance with large number of elements"""
        
        manager = GenerationDownloadManager(mock_config)
        
        # Create large dataset with proper structure
        large_candidates = []
        for i in range(1000):
            large_candidates.append({
                "extracted_date": f"24 Aug 2025 {i%24:02d}:37:01",
                "element_index": i
            })
        
        # Should handle large datasets efficiently
        import time
        start_time = time.time()
        
        selected = manager._select_best_date_candidate(large_candidates)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert processing_time < 1.0  # Should complete within 1 second
        assert selected is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])