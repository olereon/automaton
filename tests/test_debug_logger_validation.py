#!/usr/bin/env python3
"""
Debug Logger Validation Tests

Tests the comprehensive debug logging system for generation downloads.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, patch

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_debug_logger import (
    GenerationDebugLogger,
    ElementDebugInfo,
    DateExtractionDebug,
    PromptExtractionDebug
)


class MockPlaywrightElement:
    """Mock Playwright element for testing debug logger"""
    
    def __init__(self, tag_name="div", text_content="", inner_text="", 
                 inner_html="", is_visible=True, is_enabled=True,
                 attributes=None, bounding_box=None):
        self.tag_name_value = tag_name
        self.text_content_value = text_content
        self.inner_text_value = inner_text
        self.inner_html_value = inner_html
        self.is_visible_value = is_visible
        self.is_enabled_value = is_enabled
        self.attributes_dict = attributes or {}
        self.bounding_box_value = bounding_box or {"x": 0, "y": 0, "width": 100, "height": 20}
    
    async def evaluate(self, script):
        if "tagName" in script:
            return self.tag_name_value
        elif "innerText" in script:
            return self.inner_text_value
        elif "textContent" in script:
            return self.text_content_value
        elif "attributes" in script:
            return self.attributes_dict
        elif "getComputedStyle" in script:
            return {
                "display": "block",
                "visibility": "visible",
                "opacity": "1",
                "position": "static",
                "width": "100px",
                "height": "20px",
                "overflow": "visible",
                "textOverflow": "clip",
                "whiteSpace": "normal",
                "color": "rgb(0, 0, 0)",
                "fontSize": "14px",
                "fontWeight": "normal"
            }
        elif "parentElement" in script:
            return {
                "tag_name": "div",
                "class_name": "parent-class",
                "id": "parent-id",
                "text_content": "Parent content"
            }
        elif "children.length" in script:
            return 2
        return ""
    
    async def text_content(self):
        return self.text_content_value
    
    async def inner_html(self):
        return self.inner_html_value
    
    async def is_visible(self):
        return self.is_visible_value
    
    async def is_enabled(self):
        return self.is_enabled_value
    
    async def get_attribute(self, name):
        return self.attributes_dict.get(name)
    
    async def bounding_box(self):
        return self.bounding_box_value


class MockPlaywrightPage:
    """Mock Playwright page for debug logger testing"""
    
    def __init__(self, elements_by_selector=None):
        self.elements_by_selector = elements_by_selector or {}
        self.url = "https://test-site.com/debug"
    
    async def query_selector_all(self, selector):
        return self.elements_by_selector.get(selector, [])
    
    async def title(self):
        return "Debug Test Page"
    
    async def evaluate(self, script):
        if "innerWidth" in script:
            return {"width": 1920, "height": 1080}
        return "Mock page content for debugging"
    
    async def screenshot(self, path, full_page=True):
        # Simulate screenshot creation
        Path(path).touch()
        return True


class TestGenerationDebugLogger:
    """Test suite for the debug logging system"""

    @pytest.fixture
    def temp_logs_dir(self):
        """Create temporary directory for logs"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def debug_logger(self, temp_logs_dir):
        """Create debug logger instance"""
        return GenerationDebugLogger(temp_logs_dir)

    def test_debug_logger_initialization(self, debug_logger, temp_logs_dir):
        """Test debug logger initializes correctly"""
        assert debug_logger.logs_folder.exists()
        assert debug_logger.debug_log_file.exists() or debug_logger.debug_log_file.parent.exists()
        
        # Check initial data structure
        assert "session_info" in debug_logger.debug_data
        assert "configuration" in debug_logger.debug_data
        assert "steps" in debug_logger.debug_data
        assert isinstance(debug_logger.debug_data["steps"], list)

    def test_configuration_logging(self, debug_logger):
        """Test configuration logging functionality"""
        test_config = {
            "use_descriptive_naming": True,
            "unique_id": "test",
            "max_downloads": 50,
            "creation_time_text": "Creation Time"
        }
        
        debug_logger.log_configuration(test_config)
        
        assert debug_logger.debug_data["configuration"] == test_config

    def test_step_logging(self, debug_logger):
        """Test general step logging"""
        debug_logger.log_step(
            thumbnail_index=1,
            step_type="TEST_STEP",
            data={"test": "value", "number": 42},
            success=True
        )
        
        steps = debug_logger.debug_data["steps"]
        assert len(steps) == 1
        
        step = steps[0]
        assert step["thumbnail_index"] == 1
        assert step["step_type"] == "TEST_STEP"
        assert step["data"]["test"] == "value"
        assert step["success"] is True
        assert step["error"] is None
        assert "timestamp" in step

    def test_step_logging_with_error(self, debug_logger):
        """Test step logging with error information"""
        debug_logger.log_step(
            thumbnail_index=2,
            step_type="ERROR_STEP",
            data={"attempted_action": "click_thumbnail"},
            success=False,
            error="Element not found"
        )
        
        steps = debug_logger.debug_data["steps"]
        assert len(steps) == 1
        
        step = steps[0]
        assert step["success"] is False
        assert step["error"] == "Element not found"

    @pytest.mark.asyncio
    async def test_element_info_extraction(self, debug_logger):
        """Test comprehensive element information extraction"""
        mock_element = MockPlaywrightElement(
            tag_name="span",
            text_content="24 Aug 2025 01:37:01",
            inner_text="24 Aug 2025 01:37:01",
            inner_html="<span>24 Aug 2025 01:37:01</span>",
            attributes={"class": "date-element", "data-date": "2025-08-24"},
            bounding_box={"x": 100, "y": 200, "width": 150, "height": 30}
        )
        
        element_info = await debug_logger._extract_element_info(mock_element, "test-selector")
        
        assert element_info.tag_name == "span"
        assert element_info.text_content == "24 Aug 2025 01:37:01"
        assert element_info.is_visible is True
        assert element_info.is_enabled is True
        assert element_info.attributes["class"] == "date-element"
        assert element_info.bounding_box["width"] == 150

    @pytest.mark.asyncio
    async def test_page_elements_logging(self, debug_logger):
        """Test comprehensive page element logging"""
        # Create mock elements for different selectors
        mock_elements = {
            "*:has-text('Creation Time')": [
                MockPlaywrightElement(text_content="Creation Time", tag_name="span"),
                MockPlaywrightElement(text_content="Creation Time Label", tag_name="div")
            ],
            "span[aria-describedby]": [
                MockPlaywrightElement(
                    text_content="A detailed prompt about giant cameras...",
                    attributes={"aria-describedby": "tooltip-123"}
                )
            ],
            "span:contains('2025')": [
                MockPlaywrightElement(text_content="24 Aug 2025 01:37:01")
            ]
        }
        
        mock_page = MockPlaywrightPage(mock_elements)
        
        elements_info, date_candidates = await debug_logger.log_page_elements(
            mock_page, 
            thumbnail_index=1, 
            search_patterns=["Creation Time", "2025"]
        )
        
        assert len(elements_info) > 0
        assert len(date_candidates) > 0
        assert len(debug_logger.debug_data["element_snapshots"]) == 1
        
        snapshot = debug_logger.debug_data["element_snapshots"][0]
        assert snapshot["thumbnail_index"] == 1
        assert snapshot["total_elements_found"] == len(elements_info)

    def test_date_candidate_analysis(self, debug_logger):
        """Test date candidate analysis and confidence scoring"""
        mock_elements_info = [
            {
                "element_index": 0,
                "selector": "span:has-text('Creation Time')",
                "text_content": "Creation Time: 24 Aug 2025 01:37:01",
                "is_visible": True,
                "tag_name": "span",
                "attributes": {"class": "date-element"}
            },
            {
                "element_index": 1,
                "selector": "div.metadata",
                "text_content": "Generated on 2025-08-24",
                "is_visible": False,
                "tag_name": "div",
                "attributes": {"data-date": "2025-08-24"}
            },
            {
                "element_index": 2,
                "selector": "span.time",
                "text_content": "Invalid content",
                "is_visible": True,
                "tag_name": "span",
                "attributes": {}
            }
        ]
        
        date_candidates = debug_logger._analyze_date_candidates(mock_elements_info)
        
        assert len(date_candidates) > 0
        
        # Check that candidates are sorted by confidence
        confidences = [candidate["confidence"] for candidate in date_candidates]
        assert confidences == sorted(confidences, reverse=True)
        
        # Check that visible elements with "Creation Time" get higher confidence
        creation_time_candidates = [c for c in date_candidates if "Creation Time" in c["pattern_matched"]]
        assert len(creation_time_candidates) > 0
        assert creation_time_candidates[0]["confidence"] > 0.8

    def test_confidence_calculation(self, debug_logger):
        """Test confidence calculation for date candidates"""
        # High confidence case
        high_conf_element = {
            "is_visible": True,
            "attributes": {"data-date": "2025-08-24", "class": "creation-time"}
        }
        
        confidence = debug_logger._calculate_date_confidence(
            pattern="Creation Time",
            matches=["24 Aug 2025 01:37:01"],
            text="Creation Time: 24 Aug 2025 01:37:01",
            element=high_conf_element
        )
        
        assert confidence > 0.8
        
        # Low confidence case
        low_conf_element = {
            "is_visible": False,
            "attributes": {}
        }
        
        confidence = debug_logger._calculate_date_confidence(
            pattern=r"20\d{2}",
            matches=["2025"],
            text="Some random text with 2025 in it",
            element=low_conf_element
        )
        
        assert confidence < 0.5

    def test_date_extraction_logging(self, debug_logger):
        """Test date extraction logging"""
        candidates = [
            {"extracted_date": "24 Aug 2025 01:37:01", "confidence": 0.9},
            {"extracted_date": "23 Aug 2025 15:42:13", "confidence": 0.7}
        ]
        
        debug_logger.log_date_extraction(
            thumbnail_index=1,
            method="text_landmarks",
            landmark_text="Creation Time",
            elements_found=5,
            candidates=candidates,
            selected_date="24 Aug 2025 01:37:01",
            selection_reason="highest_confidence",
            success=True
        )
        
        assert len(debug_logger.debug_data["date_extractions"]) == 1
        
        extraction = debug_logger.debug_data["date_extractions"][0]
        assert extraction["thumbnail_index"] == 1
        assert extraction["method"] == "text_landmarks"
        assert extraction["selected_date"] == "24 Aug 2025 01:37:01"
        assert extraction["success"] is True

    def test_prompt_extraction_logging(self, debug_logger):
        """Test prompt extraction logging"""
        candidates = [
            {"text": "A detailed prompt...", "method": "aria_describedby", "length": 100},
            {"text": "Short prompt", "method": "title_attribute", "length": 12}
        ]
        
        debug_logger.log_prompt_extraction(
            thumbnail_index=1,
            method="ellipsis_pattern",
            pattern="</span>...",
            elements_searched=25,
            candidates=candidates,
            selected_prompt="A detailed prompt about giant frost cameras...",
            selection_reason="longest_text",
            success=True
        )
        
        assert len(debug_logger.debug_data["prompt_extractions"]) == 1
        
        extraction = debug_logger.debug_data["prompt_extractions"][0]
        assert extraction["method"] == "ellipsis_pattern"
        assert extraction["elements_searched"] == 25
        assert "A detailed prompt" in extraction["selected_prompt"]

    def test_thumbnail_click_logging(self, debug_logger):
        """Test thumbnail click logging"""
        debug_logger.log_thumbnail_click(
            thumbnail_index=2,
            thumbnail_selector=".thumsItem:nth-child(3)",
            click_success=True
        )
        
        assert len(debug_logger.debug_data["thumbnail_clicks"]) == 1
        
        click_data = debug_logger.debug_data["thumbnail_clicks"][0]
        assert click_data["thumbnail_index"] == 2
        assert click_data["selector"] == ".thumsItem:nth-child(3)"
        assert click_data["success"] is True

    def test_metadata_extraction_logging(self, debug_logger):
        """Test metadata extraction result logging"""
        extracted_data = {
            "generation_date": "24 Aug 2025 01:37:01",
            "prompt": "A majestic giant frost camera in a mystical forest setting"
        }
        
        debug_logger.log_metadata_extraction(
            thumbnail_index=3,
            extraction_method="text_landmarks",
            extracted_data=extracted_data,
            success=True
        )
        
        # Should be logged in steps
        metadata_steps = [s for s in debug_logger.debug_data["steps"] 
                         if s["step_type"] == "METADATA_EXTRACTION"]
        assert len(metadata_steps) == 1
        
        step = metadata_steps[0]
        assert step["data"]["extracted_data"] == extracted_data
        assert step["data"]["data_quality"]["quality_score"] == 1.0  # Perfect data

    def test_file_naming_logging(self, debug_logger):
        """Test file naming process logging"""
        naming_data = {
            "use_descriptive_naming": True,
            "unique_id": "test",
            "creation_date": "24 Aug 2025 01:37:01",
            "naming_format": "{media_type}_{creation_date}_{unique_id}"
        }
        
        debug_logger.log_file_naming(
            thumbnail_index=3,
            original_filename="temp_download.mp4",
            new_filename="vid_2025-08-24-01-37-01_test.mp4",
            naming_data=naming_data,
            success=True
        )
        
        assert len(debug_logger.debug_data["file_naming"]) == 1
        
        naming_log = debug_logger.debug_data["file_naming"][0]
        assert naming_log["original_filename"] == "temp_download.mp4"
        assert naming_log["new_filename"] == "vid_2025-08-24-01-37-01_test.mp4"
        assert naming_log["success"] is True

    def test_metadata_quality_assessment(self, debug_logger):
        """Test metadata quality assessment"""
        # Perfect metadata
        perfect_metadata = {
            "generation_date": "24 Aug 2025 01:37:01",
            "prompt": "A detailed prompt with sufficient content for analysis"
        }
        
        quality = debug_logger._assess_metadata_quality(perfect_metadata)
        assert quality["quality_score"] == 1.0
        assert len(quality["issues"]) == 0
        
        # Poor metadata
        poor_metadata = {
            "generation_date": "Unknown Date",
            "prompt": "Short"
        }
        
        quality = debug_logger._assess_metadata_quality(poor_metadata)
        assert quality["quality_score"] < 0.5
        assert "Date not extracted" in quality["issues"]
        assert "Prompt too short" in quality["issues"]
        
        # Truncated prompt
        truncated_metadata = {
            "generation_date": "24 Aug 2025 01:37:01",
            "prompt": "A prompt that appears to be truncated..."
        }
        
        quality = debug_logger._assess_metadata_quality(truncated_metadata)
        assert quality["quality_score"] == 0.8  # Good date, truncated prompt
        assert "Prompt appears truncated" in quality["issues"]

    @pytest.mark.asyncio
    async def test_visual_debug_report(self, debug_logger, temp_logs_dir):
        """Test visual debug report creation"""
        mock_page = MockPlaywrightPage()
        
        screenshot_path = await debug_logger.create_visual_debug_report(mock_page, thumbnail_index=1)
        
        assert screenshot_path != ""
        assert Path(screenshot_path).exists()
        assert len(debug_logger.debug_data["page_states"]) == 1
        
        page_state = debug_logger.debug_data["page_states"][0]
        assert page_state["thumbnail_index"] == 1
        assert page_state["url"] == "https://test-site.com/debug"
        assert "screenshot_path" in page_state

    def test_debug_file_persistence(self, debug_logger):
        """Test debug file saving and loading"""
        # Add some test data
        debug_logger.log_step(0, "TEST", {"data": "value"})
        debug_logger.log_configuration({"test": True})
        
        # Save should happen automatically
        assert debug_logger.debug_log_file.exists()
        
        # Load and verify content
        with open(debug_logger.debug_log_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "session_info" in saved_data
        assert "configuration" in saved_data
        assert saved_data["configuration"]["test"] is True
        assert len(saved_data["steps"]) == 1

    def test_debug_summary_generation(self, debug_logger):
        """Test debug summary generation"""
        # Add various types of debug data
        debug_logger.log_step(0, "TEST_STEP", {"data": "value"})
        debug_logger.log_date_extraction(0, "method", "landmark", 5, [], "date", "reason")
        debug_logger.log_prompt_extraction(0, "method", "pattern", 10, [], "prompt", "reason")
        debug_logger.log_thumbnail_click(0, "selector", True)
        
        summary = debug_logger.get_debug_summary()
        
        assert summary["total_steps"] == 1
        assert summary["date_extractions"] == 1
        assert summary["prompt_extractions"] == 1
        assert summary["thumbnail_clicks"] == 1
        assert "session_id" in summary
        assert "debug_log_file" in summary

    def test_debug_session_finalization(self, debug_logger):
        """Test debug session finalization"""
        # Add some test data
        debug_logger.log_step(0, "FINAL_TEST", {"final": True})
        
        # Finalize session
        summary = debug_logger.finalize_debug_session()
        
        # Check that end_time was added
        assert "end_time" in debug_logger.debug_data["session_info"]
        
        # Verify summary contains expected data
        assert isinstance(summary, dict)
        assert "session_id" in summary
        assert summary["total_steps"] >= 1

    def test_large_data_handling(self, debug_logger):
        """Test handling of large debug datasets"""
        # Add a large number of debug entries
        for i in range(100):
            debug_logger.log_step(
                thumbnail_index=i,
                step_type=f"BULK_TEST_{i}",
                data={"iteration": i, "large_data": "x" * 1000}
            )
        
        assert len(debug_logger.debug_data["steps"]) == 100
        
        # Ensure file can still be saved
        debug_logger._save_debug_file()
        assert debug_logger.debug_log_file.exists()
        
        # Check file size is reasonable (should compress JSON)
        file_size = debug_logger.debug_log_file.stat().st_size
        assert file_size > 1000  # Should have substantial content
        assert file_size < 10 * 1024 * 1024  # But not too large (< 10MB)

    def test_concurrent_logging_safety(self, debug_logger):
        """Test thread safety of logging operations"""
        import threading
        import time
        
        def log_worker(worker_id):
            for i in range(10):
                debug_logger.log_step(
                    thumbnail_index=worker_id * 10 + i,
                    step_type=f"WORKER_{worker_id}",
                    data={"worker": worker_id, "iteration": i}
                )
                time.sleep(0.001)  # Small delay
        
        # Create multiple threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=log_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all entries were logged
        assert len(debug_logger.debug_data["steps"]) == 50
        
        # Verify entries from different workers exist
        worker_ids = {step["data"]["worker"] for step in debug_logger.debug_data["steps"]}
        assert len(worker_ids) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])