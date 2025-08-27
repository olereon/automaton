#!/usr/bin/env python3
"""
Landmark Extraction Demo

This example demonstrates the enhanced landmark-based metadata extraction system
and shows how to integrate it with existing generation download workflows.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.enhanced_metadata_extractor import (
    EnhancedMetadataExtractor, 
    LegacyCompatibilityWrapper, 
    create_metadata_extractor,
    configure_enhanced_extraction
)
from utils.generation_download_manager import GenerationDownloadConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoConfig:
    """Demo configuration that mimics the real configuration"""
    
    def __init__(self):
        # Text-based landmark selectors
        self.image_to_video_text = "Image to video"
        self.creation_time_text = "Creation Time"
        self.prompt_ellipsis_pattern = "</span>..."
        self.download_no_watermark_text = "Download without Watermark"
        
        # CSS selector fallbacks
        self.generation_date_selector = ".sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)"
        self.prompt_selector = ".sc-jJRqov.cxtNJi span[aria-describedby]"
        
        # Enhanced extraction settings
        self.use_landmark_extraction = True
        self.fallback_to_legacy = True
        self.quality_threshold = 0.6
        
        # Folder settings
        self.downloads_folder = "/home/olereon/workspace/github.com/olereon/automaton/downloads/demo"
        self.logs_folder = "/home/olereon/workspace/github.com/olereon/automaton/logs"


class MockPage:
    """Mock page for demonstration purposes"""
    
    def __init__(self, scenario="success"):
        self.url = "https://wan.video/generate"
        self.scenario = scenario
        
    async def title(self):
        return "Generation Page Demo"
    
    async def query_selector_all(self, selector):
        """Mock different page scenarios"""
        if self.scenario == "success":
            return self._success_scenario_elements(selector)
        elif self.scenario == "partial_data":
            return self._partial_data_scenario_elements(selector)
        elif self.scenario == "no_landmarks":
            return self._no_landmarks_scenario_elements(selector)
        elif self.scenario == "malformed_data":
            return self._malformed_data_scenario_elements(selector)
        else:
            return []
    
    def _success_scenario_elements(self, selector):
        """Return elements for successful extraction scenario"""
        if "Image to video" in selector:
            element = MockElement()
            element._text_content = "Image to video"
            element._bounds = {'x': 100, 'y': 200, 'width': 120, 'height': 30}
            element._visible = True
            return [element]
        elif "Creation Time" in selector:
            parent = MockElement()
            date_element = MockElement()
            date_element._text_content = "2024-01-15 14:30:25"
            parent._children = [MockElement(text_content="Creation Time"), date_element]
            return [parent._children[0]]
        elif "[aria-describedby]" in selector:
            element = MockElement()
            element._text_content = "A majestic mountain landscape with snow-capped peaks under dramatic golden hour lighting, featuring a serene alpine lake reflecting the sky"
            element._attributes = {"aria-describedby": "tooltip-123"}
            element._visible = True
            return [element]
        return []
    
    def _partial_data_scenario_elements(self, selector):
        """Return elements for partial data scenario (only date available)"""
        if "Creation Time" in selector:
            parent = MockElement()
            date_element = MockElement()
            date_element._text_content = "2024-01-15 14:30:25"
            parent._children = [MockElement(text_content="Creation Time"), date_element]
            return [parent._children[0]]
        return []
    
    def _no_landmarks_scenario_elements(self, selector):
        """Return elements for no landmarks scenario (fallback to CSS)"""
        if ".sc-eJlwcH" in selector:  # CSS selector fallback
            element = MockElement()
            element._text_content = "2024-01-15"
            return [element]
        return []
    
    def _malformed_data_scenario_elements(self, selector):
        """Return elements with malformed/poor quality data"""
        if "Image to video" in selector:
            return [MockElement(text_content="Image to video")]
        elif "Creation Time" in selector:
            parent = MockElement()
            date_element = MockElement()
            date_element._text_content = "invalid-date-format"
            parent._children = [MockElement(text_content="Creation Time"), date_element]
            return [parent._children[0]]
        elif "[aria-describedby]" in selector:
            element = MockElement()
            element._text_content = "..."  # Truncated prompt
            return [element]
        return []
    
    async def wait_for_selector(self, selector, timeout=5000):
        elements = await self.query_selector_all(selector)
        return elements[0] if elements else None
    
    async def evaluate(self, script):
        return "Mock page evaluation result"


class MockElement:
    """Mock element for demonstration"""
    
    def __init__(self, text_content=None, bounds=None, visible=True, attributes=None):
        self._text_content = text_content
        self._bounds = bounds or {'x': 0, 'y': 0, 'width': 100, 'height': 20}
        self._visible = visible
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
            return "span"
        elif "attributes" in script:
            return self._attributes
        elif "children.length" in script:
            return len(self._children)
        elif "innerText" in script:
            return self._text_content
        return None
    
    async def query_selector_all(self, selector):
        return self._children
    
    async def evaluate_handle(self, script):
        return self._parent
    
    async def get_attribute(self, name):
        return self._attributes.get(name)


async def demo_basic_extraction():
    """Demonstrate basic landmark extraction"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Landmark Extraction")
    print("="*60)
    
    config = DemoConfig()
    page = MockPage(scenario="success")
    
    # Create extractor
    extractor = EnhancedMetadataExtractor(config)
    
    print("Extracting metadata using landmark-based system...")
    start_time = datetime.now()
    
    result = await extractor.extract_metadata_from_page(page)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\nExtraction completed in {duration:.2f} seconds")
    print(f"Extraction method: {result.get('extraction_method', 'unknown')}")
    print(f"Quality score: {result.get('quality_score', 'N/A'):.2f}")
    print(f"Validation passed: {result.get('validation_passed', 'N/A')}")
    
    print("\nExtracted metadata:")
    print(f"  Generation Date: {result.get('generation_date', 'N/A')}")
    print(f"  Prompt: {result.get('prompt', 'N/A')[:100]}...")
    
    # Show extraction stats
    stats = extractor.get_extraction_stats()
    print(f"\nExtraction Statistics:")
    print(f"  Landmark Success Rate: {stats.get('landmark_success_rate', 0):.1%}")
    print(f"  Fallback Rate: {stats.get('fallback_rate', 0):.1%}")
    

async def demo_fallback_scenarios():
    """Demonstrate fallback scenarios"""
    print("\n" + "="*60)
    print("DEMO 2: Fallback Scenarios")
    print("="*60)
    
    config = DemoConfig()
    
    scenarios = [
        ("success", "All landmarks available"),
        ("partial_data", "Only date landmark available"),
        ("no_landmarks", "No landmarks, CSS fallback"),
        ("malformed_data", "Poor quality data")
    ]
    
    for scenario, description in scenarios:
        print(f"\nScenario: {description}")
        print("-" * 40)
        
        page = MockPage(scenario=scenario)
        extractor = EnhancedMetadataExtractor(config)
        
        result = await extractor.extract_metadata_from_page(page)
        
        print(f"Method: {result.get('extraction_method', 'unknown')}")
        print(f"Quality: {result.get('quality_score', 0):.2f}")
        print(f"Date: {result.get('generation_date', 'N/A')}")
        print(f"Prompt: {result.get('prompt', 'N/A')[:50]}...")


async def demo_quality_assessment():
    """Demonstrate quality assessment and validation"""
    print("\n" + "="*60)
    print("DEMO 3: Quality Assessment and Validation")
    print("="*60)
    
    config = DemoConfig()
    page = MockPage(scenario="success")
    
    extractor = EnhancedMetadataExtractor(config)
    result = await extractor.extract_metadata_from_page(page)
    
    # Perform detailed validation
    validation_result = await extractor.validate_extraction_result(result)
    
    print("Validation Results:")
    print(f"  Valid: {validation_result['is_valid']}")
    print(f"  Confidence: {validation_result['confidence_score']:.2f}")
    
    if validation_result['issues']:
        print("\nIssues found:")
        for issue in validation_result['issues']:
            print(f"  • {issue}")
    
    if validation_result['suggestions']:
        print("\nSuggestions:")
        for suggestion in validation_result['suggestions']:
            print(f"  • {suggestion}")
    
    print(f"\nQuality Metrics:")
    for metric, score in validation_result.get('quality_metrics', {}).items():
        status = "✅" if score > 0.7 else "⚠️" if score > 0.4 else "❌"
        print(f"  {status} {metric}: {score:.2f}")


async def demo_legacy_compatibility():
    """Demonstrate legacy compatibility wrapper"""
    print("\n" + "="*60)
    print("DEMO 4: Legacy Compatibility")
    print("="*60)
    
    config = DemoConfig()
    page = MockPage(scenario="success")
    
    # Create legacy-compatible wrapper
    wrapper = LegacyCompatibilityWrapper(config)
    
    print("Using legacy compatibility wrapper...")
    result = await wrapper.extract_metadata_from_page(page)
    
    print("Legacy-compatible result:")
    print(f"  Fields returned: {list(result.keys())}")
    print(f"  Generation Date: {result.get('generation_date', 'N/A')}")
    print(f"  Prompt: {result.get('prompt', 'N/A')[:50]}...")
    
    # Show internal stats
    stats = wrapper.get_extraction_stats()
    print(f"\nInternal Statistics:")
    print(f"  Landmark attempts: {stats['landmark_attempts']}")
    print(f"  Landmark successes: {stats['landmark_successes']}")
    print(f"  Legacy fallbacks: {stats['legacy_fallbacks']}")


async def demo_configuration_options():
    """Demonstrate different configuration options"""
    print("\n" + "="*60)
    print("DEMO 5: Configuration Options")
    print("="*60)
    
    page = MockPage(scenario="success")
    
    configurations = [
        ("Default Settings", lambda c: c),
        ("Landmark Only", lambda c: setattr(c, 'fallback_to_legacy', False) or c),
        ("High Quality Threshold", lambda c: setattr(c, 'quality_threshold', 0.9) or c),
        ("Legacy Only", lambda c: setattr(c, 'use_landmark_extraction', False) or c)
    ]
    
    for name, config_modifier in configurations:
        print(f"\nConfiguration: {name}")
        print("-" * 30)
        
        config = DemoConfig()
        config = config_modifier(config)
        
        extractor = EnhancedMetadataExtractor(config)
        result = await extractor.extract_metadata_from_page(page)
        
        print(f"Method: {result.get('extraction_method', 'unknown')}")
        print(f"Quality: {result.get('quality_score', 0):.2f}")
        print(f"Success: {'✅' if result.get('generation_date') != 'Unknown Date' else '❌'}")


async def demo_performance_comparison():
    """Demonstrate performance comparison between methods"""
    print("\n" + "="*60)
    print("DEMO 6: Performance Comparison")
    print("="*60)
    
    config = DemoConfig()
    page = MockPage(scenario="success")
    
    # Test landmark-based extraction
    config.use_landmark_extraction = True
    config.fallback_to_legacy = False
    extractor_landmark = EnhancedMetadataExtractor(config)
    
    start_time = datetime.now()
    for _ in range(10):
        await extractor_landmark.extract_metadata_from_page(page)
    landmark_time = (datetime.now() - start_time).total_seconds()
    
    # Test legacy extraction
    config.use_landmark_extraction = False
    config.fallback_to_legacy = True
    extractor_legacy = EnhancedMetadataExtractor(config)
    
    start_time = datetime.now()
    for _ in range(10):
        await extractor_legacy.extract_metadata_from_page(page)
    legacy_time = (datetime.now() - start_time).total_seconds()
    
    print(f"Performance Comparison (10 extractions):")
    print(f"  Landmark-based: {landmark_time:.2f}s (avg: {landmark_time/10:.3f}s)")
    print(f"  Legacy method:  {legacy_time:.2f}s (avg: {legacy_time/10:.3f}s)")
    print(f"  Performance improvement: {((legacy_time - landmark_time) / legacy_time * 100):.1f}%")


async def demo_integration_example():
    """Show how to integrate with existing generation download manager"""
    print("\n" + "="*60)
    print("DEMO 7: Integration Example")
    print("="*60)
    
    print("Creating GenerationDownloadConfig with enhanced extraction...")
    
    # Create a config compatible with generation download manager
    config = GenerationDownloadConfig(
        downloads_folder="/home/olereon/workspace/github.com/olereon/automaton/downloads/demo",
        logs_folder="/home/olereon/workspace/github.com/olereon/automaton/logs",
        max_downloads=5,
        
        # Enhanced extraction settings
        use_descriptive_naming=True,
        
        # Text-based landmarks
        image_to_video_text="Image to video",
        creation_time_text="Creation Time",
        prompt_ellipsis_pattern="</span>..."
    )
    
    # Configure enhanced extraction
    config = configure_enhanced_extraction(
        config, 
        enable_landmark=True, 
        enable_fallback=True, 
        quality_threshold=0.6
    )
    
    print("✅ Configuration created with enhanced extraction enabled")
    print(f"   Landmark extraction: {config.use_landmark_extraction}")
    print(f"   Legacy fallback: {config.fallback_to_legacy}")
    print(f"   Quality threshold: {config.quality_threshold}")
    
    # Create extractor compatible with existing code
    extractor = create_metadata_extractor(config, legacy_compatible=True)
    
    print("\n✅ Extractor created with legacy compatibility")
    print("   This extractor can be used as drop-in replacement")
    print("   in existing generation download workflows.")


async def main():
    """Run all demonstrations"""
    print("🚀 Enhanced Landmark-Based Metadata Extraction Demo")
    print("This demo showcases the new extraction system capabilities")
    
    try:
        await demo_basic_extraction()
        await demo_fallback_scenarios()
        await demo_quality_assessment()
        await demo_legacy_compatibility()
        await demo_configuration_options()
        await demo_performance_comparison()
        await demo_integration_example()
        
        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60)
        
        print("\nNext Steps:")
        print("1. Review the test suite: tests/test_landmark_extraction.py")
        print("2. Check integration documentation: docs/LANDMARK_EXTRACTION_ANALYSIS.md")
        print("3. Try the system with real web pages")
        print("4. Configure quality thresholds for your use case")
        print("5. Monitor extraction statistics for performance optimization")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())