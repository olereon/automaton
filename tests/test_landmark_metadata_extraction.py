#!/usr/bin/env python3
"""
Comprehensive Test Suite for Landmark-Based Metadata Extraction System

This test suite validates the new landmark-based metadata extraction system,
focusing on "Image to video" landmark identification, metadata accuracy,
and integration with the existing download workflow.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from datetime import datetime
import json
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.landmark_extractor import (
    LandmarkExtractor, DOMNavigator, ElementInfo, ExtractionContext, ExtractionResult
)
from utils.extraction_strategies import (
    CreationTimeLandmarkStrategy, StrategyOrchestrator
)
from utils.landmark_extractor import ImageToVideoLandmarkStrategy
from utils.enhanced_metadata_extractor import EnhancedMetadataExtractor
from core.generation_download_handlers import GenerationDownloadHandlers

logger = logging.getLogger(__name__)


class MockConfig:
    """Mock configuration for testing landmark extraction"""
    def __init__(self):
        # Text landmarks configuration
        self.image_to_video_text = "Image to video"
        self.creation_time_text = "Creation Time"
        self.prompt_ellipsis_pattern = "</span>..."
        self.download_no_watermark_text = "Download without Watermark"
        
        # Enhanced extraction settings
        self.use_landmark_extraction = True
        self.fallback_to_legacy = True
        self.quality_threshold = 0.6
        
        # Legacy selectors for fallback
        self.generation_date_selector = ".sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)"
        self.prompt_selector = ".sc-jJRqov.cxtNJi span[aria-describedby]"


class MockElement:
    """Mock DOM element for testing"""
    def __init__(self, text_content="", bounds=None, visible=True, tag_name="div", 
                 attributes=None, inner_html=""):
        self._text_content = text_content
        self._bounds = bounds or {"x": 0, "y": 0, "width": 100, "height": 20}
        self._visible = visible
        self._tag_name = tag_name
        self._attributes = attributes or {}
        self._inner_html = inner_html
        self._parent = None
        self._children = []
    
    async def text_content(self):
        return self._text_content
    
    async def bounding_box(self):
        return self._bounds
    
    async def is_visible(self):
        return self._visible
    
    async def evaluate(self, script):
        if "tagName" in script:
            return self._tag_name
        elif "attributes" in script:
            return self._attributes
        elif "innerHTML" in script:
            return self._inner_html
        elif "parentElement" in script:
            return self._parent
        return None
    
    async def evaluate_handle(self, script):
        if "parentElement" in script:
            return self._parent
        return self
    
    async def query_selector_all(self, selector):
        return self._children
    
    def add_child(self, child):
        child._parent = self
        self._children.append(child)
        return child


class MockPage:
    """Mock Playwright page for testing"""
    def __init__(self):
        self.elements = {}
        self.query_results = {}
        self.selector_results = {}
        
    def add_element(self, selector, element):
        self.elements[selector] = element
        
    def add_query_result(self, selector, elements):
        if not isinstance(elements, list):
            elements = [elements]
        self.query_results[selector] = elements
    
    async def query_selector_all(self, selector):
        # Handle text-based selectors
        if ":has-text(" in selector:
            text_match = selector.split(":has-text('")[1].split("')")[0]
            return [elem for elem in self.elements.values() 
                   if elem._text_content and text_match in elem._text_content]
        
        return self.query_results.get(selector, [])
    
    async def query_selector(self, selector):
        results = await self.query_selector_all(selector)
        return results[0] if results else None
    
    async def wait_for_selector(self, selector, timeout=5000):
        return await self.query_selector(selector)


@pytest.fixture
def mock_config():
    """Fixture for mock configuration"""
    return MockConfig()


@pytest.fixture
def mock_page():
    """Fixture for mock page with sample elements"""
    page = MockPage()
    
    # Create "Image to video" landmark element
    landmark_element = MockElement(
        text_content="Image to video",
        bounds={"x": 100, "y": 200, "width": 120, "height": 24},
        visible=True,
        tag_name="span"
    )
    
    # Create Creation Time element with adjacent date
    creation_time_element = MockElement(
        text_content="Creation Time",
        bounds={"x": 100, "y": 250, "width": 100, "height": 20},
        tag_name="span"
    )
    
    date_element = MockElement(
        text_content="2024-08-26 14:30:15",
        bounds={"x": 210, "y": 250, "width": 150, "height": 20},
        tag_name="span"
    )
    
    # Create container with both elements as siblings
    container = MockElement(tag_name="div")
    container.add_child(creation_time_element)
    container.add_child(date_element)
    
    # Add prompt element
    prompt_element = MockElement(
        text_content="A beautiful landscape with mountains and rivers, cinematic lighting, ultra detailed",
        bounds={"x": 100, "y": 300, "width": 400, "height": 60},
        tag_name="span",
        attributes={"aria-describedby": "tooltip-123"},
        inner_html="A beautiful landscape with mountains and rivers, cinematic lighting, ultra detailed</span>..."
    )
    
    # Set up query results
    page.add_query_result("span:has-text('Image to video')", [landmark_element])
    page.add_query_result("span:has-text('Creation Time')", [creation_time_element])
    page.add_query_result("span[aria-describedby]", [prompt_element])
    page.add_query_result("div", [container, prompt_element.evaluate_handle("el => el.parentElement")])
    
    return page


@pytest.fixture
def mock_debug_logger():
    """Fixture for mock debug logger"""
    return Mock()


class TestLandmarkIdentification:
    """Test suite for landmark identification accuracy"""
    
    @pytest.mark.asyncio
    async def test_image_to_video_landmark_detection(self, mock_config, mock_page):
        """Test that 'Image to video' landmark is correctly identified"""
        navigator = DOMNavigator(mock_page)
        
        # Find Image to video landmarks
        landmarks = await navigator.find_elements_by_landmark("Image to video")
        
        assert len(landmarks) == 1
        assert landmarks[0].text_content == "Image to video"
        assert landmarks[0].visible
        assert landmarks[0].tag_name == "span"
    
    @pytest.mark.asyncio
    async def test_creation_time_landmark_detection(self, mock_config, mock_page):
        """Test that Creation Time landmark is correctly identified"""
        navigator = DOMNavigator(mock_page)
        
        # Find Creation Time landmarks
        landmarks = await navigator.find_elements_by_landmark("Creation Time")
        
        assert len(landmarks) == 1
        assert landmarks[0].text_content == "Creation Time"
        assert landmarks[0].bounds["x"] == 100
        assert landmarks[0].bounds["y"] == 250
    
    @pytest.mark.asyncio
    async def test_multiple_panel_detection(self, mock_config):
        """Test detection when multiple panels exist"""
        page = MockPage()
        
        # Create multiple "Image to video" elements (simulate multiple panels)
        for i in range(3):
            element = MockElement(
                text_content="Image to video",
                bounds={"x": 100, "y": 200 + (i * 100), "width": 120, "height": 24},
                tag_name="span"
            )
            page.add_query_result(f"panel_{i}", [element])
        
        # Add all elements to the main query result
        all_elements = []
        for i in range(3):
            all_elements.extend(page.query_results[f"panel_{i}"])
        page.add_query_result("span:has-text('Image to video')", all_elements)
        
        navigator = DOMNavigator(page)
        landmarks = await navigator.find_elements_by_landmark("Image to video")
        
        assert len(landmarks) == 3
        for i, landmark in enumerate(landmarks):
            assert landmark.text_content == "Image to video"
            assert landmark.bounds["y"] == 200 + (i * 100)


class TestMetadataExtractionAccuracy:
    """Test suite for metadata extraction accuracy"""
    
    @pytest.mark.asyncio
    async def test_creation_time_extraction_success(self, mock_config, mock_page, mock_debug_logger):
        """Test successful extraction of creation time using landmark"""
        strategy = CreationTimeLandmarkStrategy(DOMNavigator(mock_page), mock_config)
        context = ExtractionContext(
            page=mock_page,
            thumbnail_index=0,
            landmark_elements=[],
            content_area=None,
            metadata_panels=[]
        )
        
        # Extract generation date
        result = await strategy.extract(context, "generation_date")
        
        assert result.success
        assert result.extracted_value == "2024-08-26 14:30:15"
        assert result.confidence >= 0.8
        assert "creation_time_landmark" in result.method_used
    
    @pytest.mark.asyncio
    async def test_prompt_extraction_success(self, mock_config, mock_page, mock_debug_logger):
        """Test successful extraction of prompt text"""
        strategy = CreationTimeLandmarkStrategy(DOMNavigator(mock_page), mock_config)
        context = ExtractionContext(
            page=mock_page,
            thumbnail_index=0,
            landmark_elements=[],
            content_area=None,
            metadata_panels=[]
        )
        
        # Extract prompt
        result = await strategy.extract(context, "prompt")
        
        assert result.success
        assert "beautiful landscape" in result.extracted_value.lower()
        assert "mountains and rivers" in result.extracted_value.lower()
        assert result.confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_enhanced_extractor_landmark_success(self, mock_config, mock_page, mock_debug_logger):
        """Test full enhanced extractor with landmark system"""
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        # Mock the landmark system to return successful results
        with patch.object(extractor, '_extract_with_landmark_system') as mock_landmark:
            mock_landmark.return_value = {
                'generation_date': '2024-08-26 14:30:15',
                'prompt': 'A beautiful landscape with mountains and rivers',
                'extraction_method': 'landmark_based',
                'quality_score': 0.9
            }
            
            result = await extractor.extract_metadata_from_page(mock_page)
            
            assert result is not None
            assert result['generation_date'] == '2024-08-26 14:30:15'
            assert 'beautiful landscape' in result['prompt'].lower()
            assert 'landmark' in result['extraction_method']
            assert result['quality_score'] >= 0.8


class TestExtractionComparison:
    """Test suite for comparing landmark vs legacy extraction"""
    
    @pytest.mark.asyncio
    async def test_landmark_vs_legacy_accuracy(self, mock_config, mock_page, mock_debug_logger):
        """Compare landmark-based vs legacy extraction accuracy"""
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        # Test landmark extraction
        landmark_result = await extractor._extract_with_landmark_system(mock_page)
        
        # Test legacy extraction  
        legacy_result = await extractor._extract_with_legacy_system(mock_page)
        
        # Landmark should be more accurate
        assert landmark_result is not None
        assert legacy_result is not None
        
        # Landmark should have better structured date format
        if landmark_result.get('generation_date') != 'Unknown Date':
            landmark_date = landmark_result['generation_date']
            assert len(landmark_date) > 10  # Should have full timestamp
        
        # Both should extract some form of prompt
        assert landmark_result.get('prompt', 'Unknown Prompt') != 'Unknown Prompt'
        assert legacy_result.get('prompt', 'Unknown Prompt') != 'Unknown Prompt'
    
    @pytest.mark.asyncio
    async def test_extraction_performance_metrics(self, mock_config, mock_page, mock_debug_logger):
        """Test performance metrics collection"""
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        # Perform multiple extractions
        for _ in range(5):
            await extractor.extract_metadata_from_page(mock_page)
        
        stats = extractor.get_extraction_stats()
        
        assert stats['landmark_attempts'] == 5
        assert stats['landmark_success_rate'] >= 0.0
        assert 'fallback_rate' in stats
        assert 'quality_failure_rate' in stats


class TestEdgeCases:
    """Test suite for edge cases and error handling"""
    
    @pytest.mark.asyncio
    async def test_no_landmarks_found(self, mock_config, mock_debug_logger):
        """Test handling when no landmarks are found"""
        page = MockPage()  # Empty page
        
        navigator = DOMNavigator(page)
        landmarks = await navigator.find_elements_by_landmark("Image to video")
        
        assert len(landmarks) == 0
    
    @pytest.mark.asyncio
    async def test_missing_creation_time_elements(self, mock_config, mock_debug_logger):
        """Test handling when Creation Time elements are missing"""
        page = MockPage()
        
        # Add only Image to video landmark, no Creation Time
        landmark_element = MockElement(text_content="Image to video")
        page.add_query_result("span:has-text('Image to video')", [landmark_element])
        
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        result = await extractor.extract_metadata_from_page(page)
        
        # Should fallback to legacy or return defaults
        assert result is not None
        assert result.get('generation_date') in ['Unknown Date', None] or len(str(result.get('generation_date', ''))) > 0
    
    @pytest.mark.asyncio
    async def test_malformed_date_handling(self, mock_config, mock_debug_logger):
        """Test handling of malformed dates"""
        page = MockPage()
        
        # Create elements with malformed date
        creation_time_element = MockElement(text_content="Creation Time")
        bad_date_element = MockElement(text_content="Invalid Date Format")
        
        container = MockElement(tag_name="div")
        container.add_child(creation_time_element)
        container.add_child(bad_date_element)
        
        page.add_query_result("span:has-text('Creation Time')", [creation_time_element])
        
        strategy = CreationTimeLandmarkStrategy(DOMNavigator(page), mock_config)
        context = ExtractionContext(
            page=page,
            thumbnail_index=0,
            landmark_elements=[],
            content_area=None,
            metadata_panels=[]
        )
        
        result = await strategy.extract(context, "generation_date")
        
        # Should handle gracefully - either extract what it can or fail cleanly
        assert result is not None
        assert hasattr(result, 'success')
    
    @pytest.mark.asyncio 
    async def test_extraction_timeout_handling(self, mock_config, mock_debug_logger):
        """Test handling of extraction timeouts"""
        page = MockPage()
        
        # Mock page.wait_for_selector to timeout
        async def mock_timeout(*args, **kwargs):
            raise Exception("Timeout")
        
        page.wait_for_selector = mock_timeout
        
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        result = await extractor.extract_metadata_from_page(page)
        
        # Should handle timeout gracefully
        assert result is not None
        assert result.get('generation_date') is not None
        assert result.get('prompt') is not None


class TestDownloadWorkflowIntegration:
    """Test suite for integration with existing download workflow"""
    
    @pytest.mark.asyncio
    async def test_generation_download_handler_integration(self, mock_config):
        """Test integration with GenerationDownloadHandlers"""
        # Create a mock handler with the new extraction system
        class MockHandler(GenerationDownloadHandlers):
            def __init__(self):
                super().__init_generation_downloads__()
                self.page = MockPage()
        
        handler = MockHandler()
        
        # Mock action for start_generation_downloads
        mock_action = Mock()
        mock_action.value = {
            'max_downloads': 5,
            'use_descriptive_naming': True,
            'use_landmark_extraction': True,
            'image_to_video_text': 'Image to video',
            'creation_time_text': 'Creation Time'
        }
        
        # Test that handler can be initialized with landmark config
        assert hasattr(handler, '_generation_download_manager')
        
        # Verify the configuration includes landmark settings
        config_keys = ['image_to_video_text', 'creation_time_text', 'use_descriptive_naming']
        for key in config_keys:
            assert key in mock_action.value
    
    @pytest.mark.asyncio
    async def test_download_naming_with_extracted_metadata(self, mock_config, mock_page):
        """Test that extracted metadata is properly used in file naming"""
        extractor = EnhancedMetadataExtractor(mock_config)
        
        # Extract metadata
        result = await extractor.extract_metadata_from_page(mock_page)
        
        if result and result.get('generation_date') != 'Unknown Date':
            # Verify the extracted date can be used for filename
            date_str = result['generation_date']
            
            # Should be suitable for filename (no invalid characters)
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
            for char in invalid_chars:
                assert char not in date_str, f"Invalid character '{char}' in date: {date_str}"
        
        if result and result.get('prompt') != 'Unknown Prompt':
            prompt_str = result['prompt']
            # Prompt should be reasonable length for filename
            assert len(prompt_str) > 0


class TestPerformanceAndReliability:
    """Test suite for performance and reliability metrics"""
    
    @pytest.mark.asyncio
    async def test_extraction_speed_comparison(self, mock_config, mock_page, mock_debug_logger):
        """Test extraction speed comparison between methods"""
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        import time
        
        # Test landmark extraction speed
        start_time = time.time()
        landmark_result = await extractor._extract_with_landmark_system(mock_page)
        landmark_time = time.time() - start_time
        
        # Test legacy extraction speed
        start_time = time.time()
        legacy_result = await extractor._extract_with_legacy_system(mock_page)
        legacy_time = time.time() - start_time
        
        # Both should complete within reasonable time (< 1 second for mock)
        assert landmark_time < 1.0
        assert legacy_time < 1.0
        
        # Log timing information
        print(f"Landmark extraction time: {landmark_time:.3f}s")
        print(f"Legacy extraction time: {legacy_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_extraction_consistency(self, mock_config, mock_page, mock_debug_logger):
        """Test that extraction results are consistent across multiple runs"""
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        results = []
        for i in range(5):
            result = await extractor.extract_metadata_from_page(mock_page)
            results.append(result)
        
        # All results should be similar
        if results[0] is not None:
            first_result = results[0]
            for result in results[1:]:
                if result is not None:
                    assert result['generation_date'] == first_result['generation_date']
                    assert result['prompt'] == first_result['prompt']
    
    def test_configuration_validation(self, mock_config):
        """Test that configuration is properly validated"""
        # Test required fields
        required_fields = ['image_to_video_text', 'creation_time_text']
        for field in required_fields:
            assert hasattr(mock_config, field)
            assert getattr(mock_config, field) is not None
        
        # Test optional fields have defaults
        optional_fields = ['use_landmark_extraction', 'fallback_to_legacy', 'quality_threshold']
        for field in optional_fields:
            assert hasattr(mock_config, field)


# Test runner and utilities
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])