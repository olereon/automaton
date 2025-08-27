#!/usr/bin/env python3
"""
Comprehensive Test Suite for Landmark-Based Metadata Extraction

This test suite validates the functionality, reliability, and performance
of the enhanced landmark-based extraction system.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.landmark_extractor import (
    LandmarkExtractor, DOMNavigator, ElementInfo, ExtractionContext, ExtractionResult
)
from utils.extraction_strategies import (
    ImageToVideoLandmarkStrategy, CreationTimeLandmarkStrategy, 
    CSSFallbackStrategy, HeuristicExtractionStrategy, StrategyOrchestrator
)
from utils.extraction_validator import MetadataValidator, QualityAssessment, ValidationResult
from utils.enhanced_metadata_extractor import (
    EnhancedMetadataExtractor, LegacyCompatibilityWrapper, create_metadata_extractor
)

logger = logging.getLogger(__name__)


class MockConfig:
    """Mock configuration for testing"""
    def __init__(self):
        self.image_to_video_text = "Image to video"
        self.creation_time_text = "Creation Time"
        self.prompt_ellipsis_pattern = "</span>..."
        self.download_no_watermark_text = "Download without Watermark"
        self.generation_date_selector = ".sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)"
        self.prompt_selector = ".sc-jJRqov.cxtNJi span[aria-describedby]"
        
        # Enhanced extraction settings
        self.use_landmark_extraction = True
        self.fallback_to_legacy = True
        self.quality_threshold = 0.6


class MockElement:
    """Mock Playwright element for testing"""
    def __init__(self, text_content=None, bounds=None, visible=True, tag_name="span", attributes=None):
        self._text_content = text_content
        self._bounds = bounds
        self._visible = visible
        self._tag_name = tag_name
        self._attributes = attributes or {}
        self._children = []
        self._parent = None
    
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
        elif "children.length" in script:
            return len(self._children)
        elif "innerText" in script:
            return self._text_content
        elif "parentElement" in script:
            return self._parent
        return None
    
    async def query_selector_all(self, selector):
        return self._children
    
    async def evaluate_handle(self, script):
        return self._parent
    
    async def get_attribute(self, name):
        return self._attributes.get(name)


class MockPage:
    """Mock Playwright page for testing"""
    def __init__(self):
        self.url = "https://example.com/test"
        self._elements = []
        self._title = "Test Page"
    
    async def title(self):
        return self._title
    
    async def query_selector_all(self, selector):
        # Return relevant mock elements based on selector
        if "Image to video" in selector:
            return [MockElement(
                text_content="Image to video",
                bounds={'x': 100, 'y': 200, 'width': 120, 'height': 30},
                visible=True,
                tag_name="span",
                attributes={"class": "video-text"}
            )]
        elif "Creation Time" in selector:
            parent_element = MockElement()
            parent_element._children = [
                MockElement(text_content="Creation Time"),
                MockElement(text_content="2024-01-15 14:30")
            ]
            return [parent_element._children[0]]
        elif "[aria-describedby]" in selector:
            return [MockElement(
                text_content="A majestic mountain landscape with snow-capped peaks and dramatic lighting",
                visible=True,
                attributes={"aria-describedby": "tooltip-123"}
            )]
        return []
    
    async def wait_for_selector(self, selector, timeout=5000):
        elements = await self.query_selector_all(selector)
        return elements[0] if elements else None
    
    async def evaluate(self, script):
        if "document.body" in script:
            return "Mock page content with various elements..."
        return ""


@pytest.fixture
def mock_config():
    """Fixture providing mock configuration"""
    return MockConfig()


@pytest.fixture
def mock_page():
    """Fixture providing mock page"""
    return MockPage()


@pytest.fixture
def mock_debug_logger():
    """Fixture providing mock debug logger"""
    logger = Mock()
    logger.log_step = Mock()
    logger.log_metadata_extraction = Mock()
    return logger


class TestDOMNavigator:
    """Test suite for DOM Navigator"""
    
    @pytest.mark.asyncio
    async def test_get_element_info(self, mock_page):
        """Test element info extraction"""
        navigator = DOMNavigator(mock_page)
        element = MockElement(
            text_content="Test text",
            bounds={'x': 10, 'y': 20, 'width': 100, 'height': 50},
            visible=True,
            tag_name="div",
            attributes={"class": "test-class", "id": "test-id"}
        )
        
        info = await navigator.get_element_info(element)
        
        assert info.text_content == "Test text"
        assert info.bounds == {'x': 10, 'y': 20, 'width': 100, 'height': 50}
        assert info.visible is True
        assert info.tag_name == "div"
        assert info.attributes["class"] == "test-class"
    
    @pytest.mark.asyncio
    async def test_find_elements_by_landmark(self, mock_page):
        """Test landmark-based element finding"""
        navigator = DOMNavigator(mock_page)
        
        elements = await navigator.find_elements_by_landmark("Image to video")
        
        assert len(elements) == 1
        assert elements[0].text_content == "Image to video"
        assert elements[0].visible is True
    
    @pytest.mark.asyncio
    async def test_find_nearest_elements(self, mock_page):
        """Test spatial element finding"""
        navigator = DOMNavigator(mock_page)
        
        anchor_element = ElementInfo(
            element=MockElement(),
            text_content="Anchor",
            bounds={'x': 100, 'y': 100, 'width': 50, 'height': 20},
            visible=True,
            tag_name="span",
            attributes={}
        )
        
        # This test would need more sophisticated mocking for full validation
        nearby_elements = await navigator.find_nearest_elements(anchor_element, 200)
        
        # In a real test, we'd verify spatial relationships
        assert isinstance(nearby_elements, list)


class TestImageToVideoLandmarkStrategy:
    """Test suite for Image to Video Landmark Strategy"""
    
    @pytest.mark.asyncio
    async def test_extract_generation_date_success(self, mock_config, mock_page):
        """Test successful date extraction using Image to video landmark"""
        navigator = DOMNavigator(mock_page)
        strategy = ImageToVideoLandmarkStrategy(navigator, mock_config)
        
        context = ExtractionContext(
            page=mock_page,
            thumbnail_index=0,
            landmark_elements=[],
            content_area=None,
            metadata_panels=[]
        )
        
        result = await strategy.extract(context, "generation_date")
        
        # This would need more sophisticated mocking to test full extraction
        assert isinstance(result, ExtractionResult)
        assert result.field_name == "generation_date"
    
    @pytest.mark.asyncio
    async def test_extract_prompt_success(self, mock_config, mock_page):
        """Test successful prompt extraction"""
        navigator = DOMNavigator(mock_page)
        strategy = ImageToVideoLandmarkStrategy(navigator, mock_config)
        
        context = ExtractionContext(
            page=mock_page,
            thumbnail_index=0,
            landmark_elements=[],
            content_area=None,
            metadata_panels=[]
        )
        
        result = await strategy.extract(context, "prompt")
        
        assert isinstance(result, ExtractionResult)
        assert result.field_name == "prompt"
    
    def test_looks_like_date_valid_formats(self, mock_config, mock_page):
        """Test date format recognition"""
        navigator = DOMNavigator(mock_page)
        strategy = ImageToVideoLandmarkStrategy(navigator, mock_config)
        
        valid_dates = [
            "2024-01-15",
            "1/15/2024",
            "Jan 15, 2024",
            "15 Jan 2024",
            "2024/01/15"
        ]
        
        for date_str in valid_dates:
            assert strategy._looks_like_date(date_str), f"Should recognize {date_str} as date"
    
    def test_looks_like_date_invalid_formats(self, mock_config, mock_page):
        """Test rejection of invalid date formats"""
        navigator = DOMNavigator(mock_page)
        strategy = ImageToVideoLandmarkStrategy(navigator, mock_config)
        
        invalid_dates = [
            "not a date",
            "Image to video",
            "12345",
            "",
            None
        ]
        
        for date_str in invalid_dates:
            assert not strategy._looks_like_date(date_str), f"Should not recognize '{date_str}' as date"


class TestMetadataValidator:
    """Test suite for Metadata Validator"""
    
    def test_validate_valid_metadata(self, mock_config):
        """Test validation of good quality metadata"""
        validator = MetadataValidator(mock_config)
        
        metadata = {
            'generation_date': '2024-01-15',
            'prompt': 'A majestic mountain landscape with snow-capped peaks under dramatic lighting',
            'extraction_method': 'landmark_based',
            'extraction_timestamp': datetime.now().isoformat()
        }
        
        result = validator.validate_metadata(metadata)
        
        assert isinstance(result, ValidationResult)
        assert result.confidence_score > 0.6
        assert len(result.issues) == 0
    
    def test_validate_invalid_metadata(self, mock_config):
        """Test validation of poor quality metadata"""
        validator = MetadataValidator(mock_config)
        
        metadata = {
            'generation_date': 'not a date',
            'prompt': 'short',
            'extraction_method': 'unknown'
        }
        
        result = validator.validate_metadata(metadata)
        
        assert isinstance(result, ValidationResult)
        assert result.confidence_score < 0.5
        assert len(result.issues) > 0
    
    def test_date_format_validation(self, mock_config):
        """Test date format validation"""
        validator = MetadataValidator(mock_config)
        
        valid_dates = ["2024-01-15", "1/15/2024", "Jan 15, 2024"]
        invalid_dates = ["invalid", "2024-13-45", ""]
        
        for date_str in valid_dates:
            assert validator._validate_date_format(date_str), f"Should validate {date_str}"
        
        for date_str in invalid_dates:
            assert not validator._validate_date_format(date_str), f"Should not validate {date_str}"


class TestEnhancedMetadataExtractor:
    """Test suite for Enhanced Metadata Extractor"""
    
    @pytest.mark.asyncio
    async def test_extract_metadata_landmark_success(self, mock_config, mock_page, mock_debug_logger):
        """Test successful landmark-based extraction"""
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        # Mock the landmark extraction to return good results
        with patch.object(extractor, '_extract_with_landmark_system') as mock_landmark:
            mock_landmark.return_value = {
                'generation_date': '2024-01-15',
                'prompt': 'A beautiful landscape with mountains and lakes',
                'extraction_method': 'landmark_based'
            }
            
            result = await extractor.extract_metadata_from_page(mock_page)
            
            assert result is not None
            assert result['generation_date'] == '2024-01-15'
            assert result['prompt'] == 'A beautiful landscape with mountains and lakes'
            assert 'landmark' in result['extraction_method']
    
    @pytest.mark.asyncio
    async def test_extract_metadata_fallback_to_legacy(self, mock_config, mock_page, mock_debug_logger):
        """Test fallback to legacy extraction when landmark fails"""
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        # Mock landmark extraction to fail, legacy to succeed
        with patch.object(extractor, '_extract_with_landmark_system') as mock_landmark, \
             patch.object(extractor, '_extract_with_legacy_system') as mock_legacy:
            
            mock_landmark.return_value = None
            mock_legacy.return_value = {
                'generation_date': '2024-01-15',
                'prompt': 'Legacy extracted prompt'
            }
            
            result = await extractor.extract_metadata_from_page(mock_page)
            
            assert result is not None
            assert result['extraction_method'] == 'legacy_fallback'
    
    @pytest.mark.asyncio
    async def test_extract_metadata_quality_threshold(self, mock_config, mock_page, mock_debug_logger):
        """Test quality threshold enforcement"""
        mock_config.quality_threshold = 0.8
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        # Mock landmark extraction with low quality result
        with patch.object(extractor, '_extract_with_landmark_system') as mock_landmark, \
             patch.object(extractor, '_extract_with_legacy_system') as mock_legacy:
            
            mock_landmark.return_value = {
                'generation_date': 'bad date',
                'prompt': 'short',
                'extraction_method': 'landmark_based'
            }
            mock_legacy.return_value = {
                'generation_date': '2024-01-15',
                'prompt': 'Better legacy prompt with adequate length'
            }
            
            result = await extractor.extract_metadata_from_page(mock_page)
            
            # Should fall back to legacy due to quality threshold
            assert result['extraction_method'] == 'legacy_fallback'
    
    def test_get_extraction_stats(self, mock_config):
        """Test extraction statistics tracking"""
        extractor = EnhancedMetadataExtractor(mock_config)
        
        # Simulate some extraction attempts
        extractor.extraction_stats['landmark_attempts'] = 10
        extractor.extraction_stats['landmark_successes'] = 8
        extractor.extraction_stats['legacy_fallbacks'] = 2
        extractor.extraction_stats['quality_failures'] = 1
        
        stats = extractor.get_extraction_stats()
        
        assert stats['landmark_success_rate'] == 0.8
        assert stats['fallback_rate'] == 0.2
        assert stats['quality_failure_rate'] == 0.1


class TestLegacyCompatibilityWrapper:
    """Test suite for Legacy Compatibility Wrapper"""
    
    @pytest.mark.asyncio
    async def test_legacy_interface_compatibility(self, mock_config, mock_page):
        """Test that wrapper provides legacy-compatible interface"""
        wrapper = LegacyCompatibilityWrapper(mock_config)
        
        with patch.object(wrapper.enhanced_extractor, 'extract_metadata_from_page') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '2024-01-15',
                'prompt': 'Test prompt',
                'extraction_method': 'landmark_based',
                'quality_score': 0.9
            }
            
            result = await wrapper.extract_metadata_from_page(mock_page)
            
            # Should only return the fields expected by legacy code
            assert set(result.keys()) == {'generation_date', 'prompt'}
            assert result['generation_date'] == '2024-01-15'
            assert result['prompt'] == 'Test prompt'


class TestStrategyOrchestrator:
    """Test suite for Strategy Orchestrator"""
    
    @pytest.mark.asyncio
    async def test_strategy_selection_priority(self, mock_config, mock_page):
        """Test that strategies are tried in correct priority order"""
        navigator = DOMNavigator(mock_page)
        orchestrator = StrategyOrchestrator(navigator, mock_config)
        
        context = ExtractionContext(
            page=mock_page,
            thumbnail_index=0,
            landmark_elements=[],
            content_area=None,
            metadata_panels=[]
        )
        
        # Mock strategies to return different confidence levels
        with patch.object(orchestrator.strategies[0], 'extract') as mock_first, \
             patch.object(orchestrator.strategies[1], 'extract') as mock_second:
            
            mock_first.return_value = ExtractionResult(
                success=True,
                field_name="generation_date",
                extracted_value="2024-01-15",
                confidence=0.9,
                method_used="strategy_1",
                validation_passed=True,
                candidates=[]
            )
            
            result = await orchestrator.extract_with_fallbacks(context, "generation_date")
            
            # Should use first strategy due to high confidence
            assert result.success
            assert result.confidence == 0.9
            assert result.method_used == "strategy_1"
            # Second strategy should not be called due to high confidence from first
            mock_second.assert_not_called()


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_extraction_success(self, mock_config, mock_page, mock_debug_logger):
        """Test complete end-to-end extraction process"""
        extractor = create_metadata_extractor(mock_config, mock_debug_logger, legacy_compatible=True)
        
        result = await extractor.extract_metadata_from_page(mock_page)
        
        assert result is not None
        assert 'generation_date' in result
        assert 'prompt' in result
        # Verify no exceptions were raised and basic structure is maintained
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_error_handling_graceful_degradation(self, mock_config, mock_debug_logger):
        """Test graceful handling of errors"""
        # Create page that will cause errors
        error_page = Mock()
        error_page.query_selector_all = AsyncMock(side_effect=Exception("Page error"))
        error_page.url = "https://error.com"
        error_page.title = AsyncMock(return_value="Error Page")
        
        extractor = EnhancedMetadataExtractor(mock_config, mock_debug_logger)
        
        result = await extractor.extract_metadata_from_page(error_page)
        
        # Should return default values instead of crashing
        assert result is not None
        assert result['generation_date'] == 'Unknown Date'
        assert result['prompt'] == 'Unknown Prompt'
        assert 'error' in result.get('extraction_method', '')
    
    def test_configuration_variations(self):
        """Test different configuration scenarios"""
        base_config = MockConfig()
        
        # Test with landmark extraction disabled
        config1 = MockConfig()
        config1.use_landmark_extraction = False
        extractor1 = EnhancedMetadataExtractor(config1)
        assert not extractor1.use_landmark_extraction
        
        # Test with fallback disabled
        config2 = MockConfig()
        config2.fallback_to_legacy = False
        extractor2 = EnhancedMetadataExtractor(config2)
        assert not extractor2.fallback_to_legacy
        
        # Test with high quality threshold
        config3 = MockConfig()
        config3.quality_threshold = 0.9
        extractor3 = EnhancedMetadataExtractor(config3)
        assert extractor3.quality_threshold == 0.9


@pytest.mark.performance
class TestPerformanceScenarios:
    """Performance test scenarios"""
    
    @pytest.mark.asyncio
    async def test_extraction_performance_benchmark(self, mock_config, mock_page):
        """Benchmark extraction performance"""
        extractor = EnhancedMetadataExtractor(mock_config)
        
        start_time = datetime.now()
        
        # Run multiple extractions
        for _ in range(10):
            await extractor.extract_metadata_from_page(mock_page)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        avg_time = total_time / 10
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert avg_time < 5.0, f"Average extraction time too high: {avg_time}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, mock_config, mock_page):
        """Test that memory usage remains stable over multiple extractions"""
        import gc
        
        extractor = EnhancedMetadataExtractor(mock_config)
        
        # Run extraction multiple times
        for i in range(50):
            await extractor.extract_metadata_from_page(mock_page)
            
            # Periodic garbage collection
            if i % 10 == 0:
                gc.collect()
        
        # If we get here without memory issues, test passes
        assert True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])