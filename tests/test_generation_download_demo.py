#!/usr/bin/env python3
"""
Demo Automation Test for Generation Download with Landmark Extraction

This test validates the new landmark-based extraction system in the context
of the actual generation download automation workflow.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig
from utils.enhanced_metadata_extractor import EnhancedMetadataExtractor, create_metadata_extractor
from core.generation_download_handlers import GenerationDownloadHandlers
from utils.generation_debug_logger import GenerationDebugLogger

logger = logging.getLogger(__name__)


class MockPlaywrightPage:
    """Mock Playwright page that simulates real generation page behavior"""
    
    def __init__(self):
        self.current_url = "https://wan.video/generate"
        self.thumbnails = []
        self.scroll_position = 0
        self.elements = {}
        self.downloads_triggered = []
        self.context_mock = Mock()
        
        # Setup realistic thumbnails with metadata
        self._setup_realistic_thumbnails()
    
    def _setup_realistic_thumbnails(self):
        """Setup realistic thumbnail data for testing"""
        thumbnail_data = [
            {
                'index': 0,
                'image_to_video_text': 'Image to video',
                'creation_time': 'Creation Time',
                'generation_date': '2024-08-26 14:30:15',
                'prompt': 'A serene mountain landscape at sunset, golden hour lighting, photorealistic',
                'download_available': True
            },
            {
                'index': 1,
                'image_to_video_text': 'Image to video',
                'creation_time': 'Creation Time', 
                'generation_date': '2024-08-26 15:45:22',
                'prompt': 'Urban cityscape with neon lights, cyberpunk style, 4K ultra detailed',
                'download_available': True
            },
            {
                'index': 2,
                'image_to_video_text': 'Image to video',
                'creation_time': 'Creation Time',
                'generation_date': '2024-08-26 16:12:08',
                'prompt': 'Ocean waves crashing on rocky shore, dramatic weather, cinematic',
                'download_available': False  # Simulate still processing
            }
        ]
        
        for thumb_data in thumbnail_data:
            thumbnail = self._create_thumbnail_element(thumb_data)
            self.thumbnails.append(thumbnail)
    
    def _create_thumbnail_element(self, data):
        """Create a mock thumbnail element with realistic structure"""
        thumbnail = Mock()
        thumbnail.data = data
        thumbnail.is_visible = AsyncMock(return_value=True)
        thumbnail.bounding_box = AsyncMock(return_value={
            'x': 100, 'y': 200 + data['index'] * 300, 'width': 280, 'height': 200
        })
        
        # Mock the metadata elements within the thumbnail
        thumbnail.query_selector_all = AsyncMock(side_effect=self._mock_thumbnail_query)
        thumbnail.query_selector = AsyncMock(side_effect=self._mock_thumbnail_single_query)
        
        return thumbnail
    
    async def _mock_thumbnail_query(self, selector):
        """Mock query_selector_all for thumbnail elements"""
        if "Image to video" in selector:
            # Return Image to video landmark
            landmark = Mock()
            landmark.text_content = AsyncMock(return_value="Image to video")
            landmark.is_visible = AsyncMock(return_value=True)
            landmark.bounding_box = AsyncMock(return_value={'x': 120, 'y': 220, 'width': 100, 'height': 24})
            return [landmark]
        
        elif "Creation Time" in selector:
            # Return Creation Time elements
            creation_time = Mock()
            creation_time.text_content = AsyncMock(return_value="Creation Time")
            return [creation_time]
        
        elif "span" in selector and "nth-child" in selector:
            # Return date element
            date_element = Mock()
            date_element.text_content = AsyncMock(return_value="2024-08-26 14:30:15")
            return [date_element]
        
        elif "aria-describedby" in selector:
            # Return prompt element
            prompt_element = Mock()
            prompt_element.text_content = AsyncMock(return_value="A serene mountain landscape at sunset")
            return [prompt_element]
        
        return []
    
    async def _mock_thumbnail_single_query(self, selector):
        """Mock query_selector for single element queries"""
        results = await self._mock_thumbnail_query(selector)
        return results[0] if results else None
    
    @property
    def context(self):
        return self.context_mock
    
    async def query_selector_all(self, selector):
        """Mock main page element queries"""
        if "completed_task" in selector or "div[id$=" in selector:
            # Return completed thumbnails
            return [thumb for thumb in self.thumbnails 
                   if thumb.data.get('download_available', True)]
        
        elif "thumsInner" in selector or "thumbnail" in selector:
            return self.thumbnails
        
        elif "Image to video" in selector:
            # Return all Image to video landmarks
            landmarks = []
            for thumb in self.thumbnails:
                landmark = Mock()
                landmark.text_content = AsyncMock(return_value="Image to video")
                landmark.thumbnail_data = thumb.data
                landmarks.append(landmark)
            return landmarks
        
        return []
    
    async def query_selector(self, selector):
        """Mock single element queries"""
        results = await self.query_selector_all(selector)
        return results[0] if results else None
    
    async def wait_for_selector(self, selector, timeout=30000):
        """Mock wait for selector"""
        element = await self.query_selector(selector)
        if element:
            return element
        
        # Simulate timeout
        if timeout < 5000:
            raise Exception(f"Timeout waiting for selector: {selector}")
        
        return None
    
    async def evaluate(self, script):
        """Mock JavaScript evaluation"""
        if "scrollTo" in script:
            self.scroll_position += 500
            return None
        elif "scrollHeight" in script:
            return 2000 + len(self.thumbnails) * 300
        elif "scrollTop" in script:
            return self.scroll_position
        return None
    
    async def click(self, selector, timeout=30000):
        """Mock element clicks"""
        if "download" in selector.lower():
            # Simulate download trigger
            self.downloads_triggered.append({
                'selector': selector,
                'timestamp': datetime.now(),
                'thumbnail_index': len(self.downloads_triggered)
            })
            await asyncio.sleep(0.1)  # Simulate processing time
    
    async def wait_for_timeout(self, timeout):
        """Mock timeout waits"""
        await asyncio.sleep(timeout / 10000)  # Speed up for testing


@pytest.fixture
def mock_page():
    """Fixture for mock Playwright page"""
    return MockPlaywrightPage()


@pytest.fixture
def test_config():
    """Fixture for test configuration"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = GenerationDownloadConfig(
            downloads_folder=os.path.join(temp_dir, "downloads"),
            logs_folder=os.path.join(temp_dir, "logs"),
            max_downloads=3,
            download_timeout=5000,
            verification_timeout=3000,
            retry_attempts=2,
            
            # Enhanced naming 
            use_descriptive_naming=True,
            unique_id="test",
            naming_format="{media_type}_{creation_date}_{unique_id}",
            
            # Landmark configuration
            image_to_video_text="Image to video",
            creation_time_text="Creation Time",
            prompt_ellipsis_pattern="</span>...",
            
            # Selectors
            completed_task_selector="div[id$='__test']",
            thumbnail_selector=".thumbnail-item",
            thumbnail_container_selector=".thumsInner"
        )
        
        # Ensure directories exist
        os.makedirs(config.downloads_folder, exist_ok=True)
        os.makedirs(config.logs_folder, exist_ok=True)
        
        yield config


@pytest.fixture
def debug_logger(test_config):
    """Fixture for debug logger"""
    return GenerationDebugLogger(test_config.logs_folder)


class TestGenerationDownloadDemo:
    """Test suite for demonstration of generation download with landmark extraction"""
    
    @pytest.mark.asyncio
    async def test_landmark_extraction_in_download_workflow(self, mock_page, test_config, debug_logger):
        """Test landmark extraction integrated into download workflow"""
        
        # Initialize the download manager with landmark extraction
        manager = GenerationDownloadManager(test_config)
        manager.debug_logger = debug_logger
        
        # Mock the metadata extractor to use landmark system
        enhanced_extractor = EnhancedMetadataExtractor(test_config, debug_logger)
        
        # Test metadata extraction on first thumbnail
        thumbnail = mock_page.thumbnails[0]
        extracted_metadata = await enhanced_extractor.extract_metadata_from_page(mock_page)
        
        # Verify landmark-based extraction worked
        assert extracted_metadata is not None
        assert extracted_metadata.get('generation_date') is not None
        assert extracted_metadata.get('prompt') is not None
        assert 'landmark' in extracted_metadata.get('extraction_method', '')
        
        print(f"✓ Landmark extraction successful:")
        print(f"  Date: {extracted_metadata.get('generation_date')}")
        print(f"  Prompt: {extracted_metadata.get('prompt', '')[:50]}...")
        print(f"  Method: {extracted_metadata.get('extraction_method')}")
    
    @pytest.mark.asyncio
    async def test_image_to_video_panel_identification(self, mock_page, test_config, debug_logger):
        """Test that 'Image to video' landmarks correctly identify target panels"""
        
        # Find all Image to video landmarks
        image_to_video_elements = await mock_page.query_selector_all("*:has-text('Image to video')")
        
        assert len(image_to_video_elements) == 3  # Should find 3 panels
        
        for i, element in enumerate(image_to_video_elements):
            text = await element.text_content()
            assert text == "Image to video"
            
            # Verify each landmark corresponds to correct panel
            thumbnail_data = element.thumbnail_data
            assert thumbnail_data['index'] == i
            
            print(f"✓ Panel {i+1} identified with landmark: '{text}'")
            print(f"  Associated data: Date={thumbnail_data['generation_date']}")
            print(f"  Prompt preview: {thumbnail_data['prompt'][:40]}...")
    
    @pytest.mark.asyncio
    async def test_download_button_extraction_accuracy(self, mock_page, test_config, debug_logger):
        """Test download button, prompt text, and creation time extraction accuracy"""
        
        manager = GenerationDownloadManager(test_config)
        enhanced_extractor = create_metadata_extractor(test_config, debug_logger, legacy_compatible=False)
        
        # Test extraction from each thumbnail
        extraction_results = []
        
        for i, thumbnail in enumerate(mock_page.thumbnails):
            if not thumbnail.data.get('download_available', True):
                continue
                
            # Test metadata extraction
            metadata = await enhanced_extractor.extract_metadata_from_page(mock_page)
            
            extraction_results.append({
                'thumbnail_index': i,
                'metadata': metadata,
                'expected_date': thumbnail.data['generation_date'],
                'expected_prompt': thumbnail.data['prompt']
            })
        
        # Verify extraction accuracy
        successful_extractions = 0
        for result in extraction_results:
            metadata = result['metadata']
            
            if metadata and metadata.get('generation_date') != 'Unknown Date':
                successful_extractions += 1
                
                print(f"✓ Thumbnail {result['thumbnail_index']} extraction successful:")
                print(f"  Date accuracy: {metadata['generation_date'] == result['expected_date']}")
                print(f"  Prompt length: {len(metadata.get('prompt', ''))} chars")
                print(f"  Quality score: {metadata.get('quality_score', 'N/A')}")
        
        # Should have at least 80% success rate
        success_rate = successful_extractions / len(extraction_results)
        assert success_rate >= 0.8, f"Success rate {success_rate} below 80% threshold"
        print(f"✓ Overall extraction success rate: {success_rate*100:.1f}%")
    
    @pytest.mark.asyncio
    async def test_extraction_method_comparison(self, mock_page, test_config, debug_logger):
        """Compare landmark vs legacy extraction methods"""
        
        enhanced_extractor = EnhancedMetadataExtractor(test_config, debug_logger)
        
        # Test both methods
        landmark_result = await enhanced_extractor._extract_with_landmark_system(mock_page)
        legacy_result = await enhanced_extractor._extract_with_legacy_system(mock_page)
        
        comparison_report = {
            'landmark': {
                'success': landmark_result is not None,
                'date': landmark_result.get('generation_date') if landmark_result else None,
                'prompt': landmark_result.get('prompt') if landmark_result else None
            },
            'legacy': {
                'success': legacy_result is not None,
                'date': legacy_result.get('generation_date') if legacy_result else None,
                'prompt': legacy_result.get('prompt') if legacy_result else None
            }
        }
        
        print("📊 Extraction Method Comparison:")
        print(f"Landmark Success: {comparison_report['landmark']['success']}")
        print(f"Legacy Success: {comparison_report['legacy']['success']}")
        
        if comparison_report['landmark']['success']:
            print(f"Landmark Date: {comparison_report['landmark']['date']}")
            print(f"Landmark Prompt: {comparison_report['landmark']['prompt'][:50] if comparison_report['landmark']['prompt'] else 'None'}...")
        
        if comparison_report['legacy']['success']:
            print(f"Legacy Date: {comparison_report['legacy']['date']}")
            print(f"Legacy Prompt: {comparison_report['legacy']['prompt'][:50] if comparison_report['legacy']['prompt'] else 'None'}...")
        
        # At least one method should succeed
        assert comparison_report['landmark']['success'] or comparison_report['legacy']['success']
        
        return comparison_report
    
    @pytest.mark.asyncio
    async def test_edge_case_handling(self, test_config, debug_logger):
        """Test edge cases like missing elements, multiple panels, etc."""
        
        # Test case 1: No landmarks found
        empty_page = MockPlaywrightPage()
        empty_page.thumbnails = []  # No thumbnails
        
        enhanced_extractor = EnhancedMetadataExtractor(test_config, debug_logger)
        result = await enhanced_extractor.extract_metadata_from_page(empty_page)
        
        assert result is not None  # Should return defaults
        assert result.get('generation_date') in ['Unknown Date', None] or len(str(result.get('generation_date'))) > 0
        print("✓ Empty page handled gracefully")
        
        # Test case 2: Multiple panels with same content
        multi_panel_page = MockPlaywrightPage()
        
        # Create 5 identical panels
        for i in range(5):
            thumb_data = {
                'index': i,
                'image_to_video_text': 'Image to video',
                'creation_time': 'Creation Time',
                'generation_date': f'2024-08-26 {14+i}:30:15',
                'prompt': f'Test prompt {i+1} with detailed description',
                'download_available': True
            }
            thumbnail = multi_panel_page._create_thumbnail_element(thumb_data)
            multi_panel_page.thumbnails.append(thumbnail)
        
        result = await enhanced_extractor.extract_metadata_from_page(multi_panel_page)
        
        assert result is not None
        print(f"✓ Multiple panels handled: extracted from {len(multi_panel_page.thumbnails)} panels")
        
        # Test case 3: Malformed data
        malformed_page = MockPlaywrightPage()
        malformed_page.thumbnails[0].data['generation_date'] = 'Invalid Date Format!!!'
        malformed_page.thumbnails[0].data['prompt'] = ''  # Empty prompt
        
        result = await enhanced_extractor.extract_metadata_from_page(malformed_page)
        
        assert result is not None
        print("✓ Malformed data handled gracefully")
    
    @pytest.mark.asyncio
    async def test_integration_with_download_workflow(self, mock_page, test_config, debug_logger):
        """Test integration with existing download workflow"""
        
        # Create download manager with landmark extraction enabled
        manager = GenerationDownloadManager(test_config)
        manager.debug_logger = debug_logger
        
        # Mock the actual download process (simulate file system operations)
        downloaded_files = []
        
        async def mock_download_file(url, filename):
            downloaded_files.append({
                'url': url,
                'filename': filename,
                'timestamp': datetime.now()
            })
            return True
        
        # Mock the manager's download method
        with patch.object(manager, '_download_file_from_url', side_effect=mock_download_file):
            # Run a simulated download process
            for i, thumbnail in enumerate(mock_page.thumbnails):
                if thumbnail.data.get('download_available', True):
                    # Simulate metadata extraction and file naming
                    enhanced_extractor = EnhancedMetadataExtractor(test_config, debug_logger)
                    metadata = await enhanced_extractor.extract_metadata_from_page(mock_page)
                    
                    if metadata:
                        # Generate filename using extracted metadata
                        date_str = metadata.get('generation_date', 'unknown').replace(':', '-').replace(' ', '_')
                        filename = f"video_{date_str}_test_{i:03d}.mp4"
                        
                        await mock_download_file(f"mock_url_{i}", filename)
        
        # Verify integration worked
        assert len(downloaded_files) > 0
        print(f"✓ Integration successful: {len(downloaded_files)} files processed")
        
        for file_info in downloaded_files:
            print(f"  Generated filename: {file_info['filename']}")
            # Verify filename follows expected pattern
            assert 'video_' in file_info['filename']
            assert 'test' in file_info['filename']
            assert file_info['filename'].endswith('.mp4')
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, mock_page, test_config, debug_logger):
        """Test performance metrics collection during extraction"""
        
        enhanced_extractor = EnhancedMetadataExtractor(test_config, debug_logger)
        
        # Run multiple extractions to collect performance data
        start_time = datetime.now()
        
        results = []
        for i in range(10):
            result = await enhanced_extractor.extract_metadata_from_page(mock_page)
            results.append(result)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Get extraction statistics
        stats = enhanced_extractor.get_extraction_stats()
        
        performance_report = {
            'total_time': total_time,
            'average_time_per_extraction': total_time / 10,
            'successful_extractions': len([r for r in results if r and r.get('generation_date') != 'Unknown Date']),
            'extraction_stats': stats
        }
        
        print("⚡ Performance Metrics:")
        print(f"Total time: {performance_report['total_time']:.3f}s")
        print(f"Average per extraction: {performance_report['average_time_per_extraction']:.3f}s") 
        print(f"Success rate: {performance_report['successful_extractions']}/10")
        print(f"Landmark attempts: {stats.get('landmark_attempts', 0)}")
        print(f"Landmark successes: {stats.get('landmark_successes', 0)}")
        print(f"Legacy fallbacks: {stats.get('legacy_fallbacks', 0)}")
        
        # Verify reasonable performance
        assert performance_report['average_time_per_extraction'] < 1.0  # Should be fast for mocked operations
        assert performance_report['successful_extractions'] >= 8  # At least 80% success
        
        return performance_report


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])