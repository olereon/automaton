#!/usr/bin/env python3
"""
Performance Comparison and Integration Tests

This test suite provides comprehensive performance analysis and 
integration validation for the landmark-based extraction system.
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
import json
import sys
import os
import time
from datetime import datetime, timedelta
import statistics
import tempfile
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.enhanced_metadata_extractor import EnhancedMetadataExtractor
from utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig
from core.engine import WebAutomationEngine
from utils.generation_debug_logger import GenerationDebugLogger

logger = logging.getLogger(__name__)


class PerformanceTestConfig:
    """Configuration optimized for performance testing"""
    def __init__(self):
        self.image_to_video_text = "Image to video"
        self.creation_time_text = "Creation Time"
        self.prompt_ellipsis_pattern = "</span>..."
        self.download_no_watermark_text = "Download without Watermark"
        self.generation_date_selector = ".sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)"
        self.prompt_selector = ".sc-jJRqov.cxtNJi span[aria-describedby]"
        self.use_landmark_extraction = True
        self.fallback_to_legacy = True
        self.quality_threshold = 0.6


class RealisticMockPage:
    """Mock page that closely simulates real-world performance characteristics"""
    
    def __init__(self, thumbnail_count=10, response_delay=0.01, error_rate=0.0):
        self.thumbnail_count = thumbnail_count
        self.response_delay = response_delay
        self.error_rate = error_rate
        self.query_count = 0
        self.thumbnails_data = self._generate_thumbnail_data()
    
    def _generate_thumbnail_data(self):
        """Generate realistic thumbnail data for testing"""
        thumbnails = []
        for i in range(self.thumbnail_count):
            thumbnails.append({
                'index': i,
                'image_to_video_text': 'Image to video',
                'creation_time': 'Creation Time',
                'generation_date': f'2024-08-{26 - i % 5:02d} {14 + i % 10}:{30 + i % 30:02d}:{15 + i % 45:02d}',
                'prompt': f'Realistic test prompt {i+1} with detailed description for video generation, including various artistic styles and technical parameters',
                'download_available': i % 8 != 0,  # Some not available
                'panel_type': ['completed', 'processing', 'failed'][i % 3]
            })
        return thumbnails
    
    async def query_selector_all(self, selector):
        """Simulate realistic query response times and occasional errors"""
        await asyncio.sleep(self.response_delay)
        self.query_count += 1
        
        # Simulate occasional errors
        if self.error_rate > 0 and (self.query_count * self.error_rate) % 1 == 0:
            raise Exception(f"Simulated network error on query {self.query_count}")
        
        if "Image to video" in selector:
            # Return landmark elements
            elements = []
            for thumb in self.thumbnails_data:
                element = Mock()
                element.text_content = AsyncMock(return_value="Image to video")
                element.bounding_box = AsyncMock(return_value={
                    'x': 100, 'y': 200 + thumb['index'] * 300, 'width': 120, 'height': 24
                })
                element.is_visible = AsyncMock(return_value=thumb['download_available'])
                element.thumbnail_data = thumb
                elements.append(element)
            return elements
        
        elif "Creation Time" in selector:
            # Return creation time elements
            elements = []
            for thumb in self.thumbnails_data:
                if thumb['download_available']:
                    element = Mock()
                    element.text_content = AsyncMock(return_value="Creation Time")
                    element.thumbnail_data = thumb
                    
                    # Mock parent structure
                    parent = Mock()
                    date_span = Mock()
                    date_span.text_content = AsyncMock(return_value=thumb['generation_date'])
                    parent.query_selector_all = AsyncMock(return_value=[element, date_span])
                    element.evaluate_handle = AsyncMock(return_value=parent)
                    
                    elements.append(element)
            return elements
        
        elif "aria-describedby" in selector:
            # Return prompt elements
            elements = []
            for thumb in self.thumbnails_data:
                if thumb['download_available']:
                    element = Mock()
                    element.text_content = AsyncMock(return_value=thumb['prompt'])
                    element.evaluate = AsyncMock(return_value=thumb['prompt'] + "</span>...")
                    elements.append(element)
            return elements
        
        return []
    
    async def query_selector(self, selector):
        results = await self.query_selector_all(selector)
        return results[0] if results else None
    
    async def wait_for_selector(self, selector, timeout=30000):
        await asyncio.sleep(min(self.response_delay * 2, timeout / 1000))
        return await self.query_selector(selector)
    
    async def evaluate(self, script):
        await asyncio.sleep(self.response_delay * 0.5)
        return None


class PerformanceBenchmark:
    """Utility class for performance benchmarking"""
    
    def __init__(self):
        self.measurements = []
    
    async def measure_async(self, func, *args, **kwargs):
        """Measure execution time of async function"""
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        self.measurements.append(duration)
        
        return result, duration
    
    def get_stats(self):
        """Get performance statistics"""
        if not self.measurements:
            return {}
        
        return {
            'count': len(self.measurements),
            'total_time': sum(self.measurements),
            'average': statistics.mean(self.measurements),
            'median': statistics.median(self.measurements),
            'min': min(self.measurements),
            'max': max(self.measurements),
            'std_dev': statistics.stdev(self.measurements) if len(self.measurements) > 1 else 0
        }
    
    def reset(self):
        """Reset measurements"""
        self.measurements = []


class TestPerformanceComparison:
    """Test suite for performance comparison between extraction methods"""
    
    @pytest.fixture
    def benchmark(self):
        return PerformanceBenchmark()
    
    @pytest.mark.asyncio
    async def test_landmark_vs_legacy_performance(self, benchmark):
        """Compare performance of landmark vs legacy extraction methods"""
        config = PerformanceTestConfig()
        page = RealisticMockPage(thumbnail_count=5, response_delay=0.01)
        debug_logger = Mock()
        
        extractor = EnhancedMetadataExtractor(config, debug_logger)
        
        # Benchmark landmark extraction
        landmark_results = []
        landmark_benchmark = PerformanceBenchmark()
        
        for i in range(10):  # Run 10 iterations
            result, duration = await landmark_benchmark.measure_async(
                extractor._extract_with_landmark_system, page
            )
            landmark_results.append(result)
        
        # Benchmark legacy extraction
        legacy_results = []
        legacy_benchmark = PerformanceBenchmark()
        
        for i in range(10):  # Run 10 iterations
            result, duration = await legacy_benchmark.measure_async(
                extractor._extract_with_legacy_system, page
            )
            legacy_results.append(result)
        
        # Analyze performance
        landmark_stats = landmark_benchmark.get_stats()
        legacy_stats = legacy_benchmark.get_stats()
        
        print("🚀 Performance Comparison Results:")
        print(f"Landmark Extraction:")
        print(f"  Average: {landmark_stats['average']*1000:.2f}ms")
        print(f"  Median: {landmark_stats['median']*1000:.2f}ms")
        print(f"  Std Dev: {landmark_stats['std_dev']*1000:.2f}ms")
        
        print(f"Legacy Extraction:")
        print(f"  Average: {legacy_stats['average']*1000:.2f}ms")
        print(f"  Median: {legacy_stats['median']*1000:.2f}ms")
        print(f"  Std Dev: {legacy_stats['std_dev']*1000:.2f}ms")
        
        # Calculate performance ratio
        performance_ratio = landmark_stats['average'] / legacy_stats['average']
        print(f"Performance Ratio: {performance_ratio:.2f}x")
        
        # Both methods should complete within reasonable time
        assert landmark_stats['average'] < 1.0  # Less than 1 second
        assert legacy_stats['average'] < 1.0
        
        # Success rate analysis
        landmark_successes = len([r for r in landmark_results if r and r.get('generation_date') != 'Unknown Date'])
        legacy_successes = len([r for r in legacy_results if r and r.get('generation_date') != 'Unknown Date'])
        
        print(f"Success Rates:")
        print(f"  Landmark: {landmark_successes}/10 ({landmark_successes*10}%)")
        print(f"  Legacy: {legacy_successes}/10 ({legacy_successes*10}%)")
        
        return {
            'landmark_stats': landmark_stats,
            'legacy_stats': legacy_stats,
            'performance_ratio': performance_ratio,
            'landmark_success_rate': landmark_successes / 10,
            'legacy_success_rate': legacy_successes / 10
        }
    
    @pytest.mark.asyncio
    async def test_scalability_with_increasing_thumbnails(self, benchmark):
        """Test how performance scales with increasing number of thumbnails"""
        config = PerformanceTestConfig()
        extractor = EnhancedMetadataExtractor(config, Mock())
        
        thumbnail_counts = [1, 5, 10, 25, 50]
        scalability_results = {}
        
        for count in thumbnail_counts:
            page = RealisticMockPage(thumbnail_count=count, response_delay=0.005)
            
            # Measure performance for this thumbnail count
            durations = []
            for i in range(5):  # 5 iterations per thumbnail count
                result, duration = await benchmark.measure_async(
                    extractor.extract_metadata_from_page, page
                )
                durations.append(duration)
            
            avg_duration = statistics.mean(durations)
            scalability_results[count] = {
                'average_duration': avg_duration,
                'queries_made': page.query_count / 5,  # Average queries per extraction
                'throughput': count / avg_duration  # Thumbnails processed per second
            }
            
            print(f"📊 {count} thumbnails: {avg_duration*1000:.2f}ms avg, {page.query_count/5:.1f} queries avg")
        
        # Verify scalability is reasonable (not exponential)
        durations = [scalability_results[count]['average_duration'] for count in thumbnail_counts]
        
        # Performance should not degrade exponentially
        max_duration = max(durations)
        min_duration = min(durations)
        degradation_factor = max_duration / min_duration
        
        print(f"📈 Scalability Analysis:")
        print(f"  Performance degradation factor: {degradation_factor:.2f}x")
        print(f"  Max throughput: {max(r['throughput'] for r in scalability_results.values()):.1f} thumbnails/sec")
        
        # Should scale reasonably (less than 10x degradation for 50x more thumbnails)
        assert degradation_factor < 10.0
        
        return scalability_results
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, benchmark):
        """Test performance impact of error recovery mechanisms"""
        config = PerformanceTestConfig()
        
        # Test with different error rates
        error_rates = [0.0, 0.1, 0.2, 0.5]  # 0%, 10%, 20%, 50% error rates
        error_recovery_results = {}
        
        for error_rate in error_rates:
            page = RealisticMockPage(thumbnail_count=10, response_delay=0.01, error_rate=error_rate)
            extractor = EnhancedMetadataExtractor(config, Mock())
            
            durations = []
            successes = 0
            
            for i in range(10):  # 10 attempts per error rate
                try:
                    result, duration = await benchmark.measure_async(
                        extractor.extract_metadata_from_page, page
                    )
                    durations.append(duration)
                    
                    if result and result.get('generation_date') != 'Unknown Date':
                        successes += 1
                        
                except Exception as e:
                    # Error recovery should handle this, but track if it doesn't
                    print(f"Unhandled error at {error_rate*100}% error rate: {e}")
            
            if durations:
                error_recovery_results[error_rate] = {
                    'average_duration': statistics.mean(durations),
                    'success_rate': successes / 10,
                    'attempts': len(durations),
                    'error_rate': error_rate
                }
            
            print(f"🔄 Error rate {error_rate*100:.0f}%: {statistics.mean(durations)*1000:.1f}ms avg, {successes*10}% success")
        
        # Verify error recovery doesn't cause excessive performance degradation
        no_error_perf = error_recovery_results[0.0]['average_duration']
        high_error_perf = error_recovery_results[0.5]['average_duration']
        
        performance_impact = high_error_perf / no_error_perf
        print(f"🛡️ Error recovery performance impact: {performance_impact:.2f}x")
        
        # Should maintain reasonable performance even with 50% errors
        assert performance_impact < 5.0  # Less than 5x performance degradation
        
        return error_recovery_results


class TestIntegrationValidation:
    """Test suite for comprehensive integration validation"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_download_workflow_integration(self):
        """Test complete integration with download workflow"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup realistic configuration
            config = GenerationDownloadConfig(
                downloads_folder=os.path.join(temp_dir, "downloads"),
                logs_folder=os.path.join(temp_dir, "logs"),
                max_downloads=5,
                download_timeout=3000,
                verification_timeout=2000,
                retry_attempts=2,
                
                # Enable landmark extraction
                use_landmark_extraction=True,
                use_descriptive_naming=True,
                unique_id="integration_test",
                
                # Landmark configuration
                image_to_video_text="Image to video",
                creation_time_text="Creation Time",
                prompt_ellipsis_pattern="</span>...",
                
                # Selectors
                completed_task_selector="div[id$='__test']",
                thumbnail_selector=".thumbnail-item"
            )
            
            # Ensure directories exist
            os.makedirs(config.downloads_folder, exist_ok=True)
            os.makedirs(config.logs_folder, exist_ok=True)
            
            # Create realistic page
            page = RealisticMockPage(thumbnail_count=5, response_delay=0.01)
            debug_logger = GenerationDebugLogger(config.logs_folder)
            
            # Initialize download manager
            manager = GenerationDownloadManager(config)
            manager.debug_logger = debug_logger
            
            # Mock file download operations
            downloaded_files = []
            
            async def mock_download_file(url, filepath):
                downloaded_files.append({
                    'url': url,
                    'filepath': filepath,
                    'timestamp': datetime.now()
                })
                # Simulate file creation
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                Path(filepath).touch()
                return True
            
            async def mock_verify_download(filepath):
                return Path(filepath).exists()
            
            # Patch download methods
            with patch.object(manager, '_download_file_from_url', side_effect=mock_download_file), \
                 patch.object(manager, '_verify_download', side_effect=mock_verify_download):
                
                # Test metadata extraction integration
                enhanced_extractor = EnhancedMetadataExtractor(config, debug_logger)
                
                integration_results = {
                    'metadata_extractions': [],
                    'file_downloads': [],
                    'naming_patterns': [],
                    'total_processing_time': 0
                }
                
                start_time = time.perf_counter()
                
                # Process thumbnails as the download manager would
                thumbnails = await page.query_selector_all("div[id$='__test']")
                
                for i, thumbnail in enumerate(thumbnails):
                    # Extract metadata
                    metadata = await enhanced_extractor.extract_metadata_from_page(page)
                    
                    if metadata:
                        integration_results['metadata_extractions'].append({
                            'thumbnail_index': i,
                            'extraction_method': metadata.get('extraction_method'),
                            'generation_date': metadata.get('generation_date'),
                            'prompt_length': len(metadata.get('prompt', '')),
                            'quality_score': metadata.get('quality_score', 0)
                        })
                        
                        # Generate filename
                        date_str = metadata.get('generation_date', 'unknown').replace(':', '-').replace(' ', '_')
                        filename = f"video_{date_str}_integration_test_{i:03d}.mp4"
                        filepath = os.path.join(config.downloads_folder, filename)
                        
                        # Simulate download
                        await mock_download_file(f"test_url_{i}", filepath)
                        
                        integration_results['file_downloads'].append({
                            'filename': filename,
                            'metadata_used': metadata,
                            'file_exists': Path(filepath).exists()
                        })
                        
                        integration_results['naming_patterns'].append(filename)
                
                end_time = time.perf_counter()
                integration_results['total_processing_time'] = end_time - start_time
                
                # Verify integration success
                print("🔗 End-to-End Integration Results:")
                print(f"  Thumbnails processed: {len(thumbnails)}")
                print(f"  Metadata extractions: {len(integration_results['metadata_extractions'])}")
                print(f"  Files downloaded: {len(integration_results['file_downloads'])}")
                print(f"  Total processing time: {integration_results['total_processing_time']*1000:.1f}ms")
                
                # Verify extraction success rate
                successful_extractions = len([e for e in integration_results['metadata_extractions'] 
                                            if e['generation_date'] != 'Unknown Date'])
                success_rate = successful_extractions / len(integration_results['metadata_extractions']) if integration_results['metadata_extractions'] else 0
                
                print(f"  Extraction success rate: {success_rate*100:.1f}%")
                
                # Verify file naming consistency
                naming_patterns_valid = all(
                    'video_' in name and 'integration_test' in name and name.endswith('.mp4')
                    for name in integration_results['naming_patterns']
                )
                
                print(f"  Naming patterns valid: {naming_patterns_valid}")
                
                # Verify files were created
                files_created = sum(1 for download in integration_results['file_downloads'] 
                                  if download['file_exists'])
                print(f"  Files created: {files_created}/{len(integration_results['file_downloads'])}")
                
                # Assertions
                assert success_rate >= 0.8  # At least 80% success rate
                assert naming_patterns_valid
                assert files_created == len(integration_results['file_downloads'])
                assert integration_results['total_processing_time'] < 5.0  # Should complete within 5 seconds
                
                return integration_results
    
    @pytest.mark.asyncio
    async def test_configuration_validation_and_fallbacks(self):
        """Test configuration validation and fallback mechanisms"""
        
        # Test various configuration scenarios
        test_scenarios = [
            {
                'name': 'optimal_config',
                'config_overrides': {
                    'use_landmark_extraction': True,
                    'fallback_to_legacy': True,
                    'quality_threshold': 0.6
                },
                'expected_method': 'landmark_based'
            },
            {
                'name': 'landmark_disabled',
                'config_overrides': {
                    'use_landmark_extraction': False,
                    'fallback_to_legacy': True,
                    'quality_threshold': 0.6
                },
                'expected_method': 'legacy'
            },
            {
                'name': 'high_quality_threshold',
                'config_overrides': {
                    'use_landmark_extraction': True,
                    'fallback_to_legacy': True,
                    'quality_threshold': 0.9  # Very high threshold
                },
                'expected_method': 'fallback'
            },
            {
                'name': 'no_fallback',
                'config_overrides': {
                    'use_landmark_extraction': True,
                    'fallback_to_legacy': False,
                    'quality_threshold': 0.6
                },
                'expected_method': 'landmark_only'
            }
        ]
        
        page = RealisticMockPage(thumbnail_count=3, response_delay=0.01)
        
        scenario_results = {}
        
        for scenario in test_scenarios:
            config = PerformanceTestConfig()
            
            # Apply configuration overrides
            for key, value in scenario['config_overrides'].items():
                setattr(config, key, value)
            
            extractor = EnhancedMetadataExtractor(config, Mock())
            
            # Test extraction with this configuration
            result = await extractor.extract_metadata_from_page(page)
            
            scenario_results[scenario['name']] = {
                'config': scenario['config_overrides'],
                'result': result,
                'extraction_method': result.get('extraction_method') if result else 'failed',
                'success': result is not None and result.get('generation_date') != 'Unknown Date'
            }
            
            print(f"📝 {scenario['name']}:")
            print(f"  Method used: {scenario_results[scenario['name']]['extraction_method']}")
            print(f"  Success: {scenario_results[scenario['name']]['success']}")
        
        # Verify all scenarios handled appropriately
        for scenario_name, result in scenario_results.items():
            assert result['result'] is not None, f"Scenario {scenario_name} returned None"
            assert result['extraction_method'] != 'failed', f"Scenario {scenario_name} failed completely"
        
        return scenario_results
    
    @pytest.mark.asyncio
    async def test_memory_usage_and_cleanup(self):
        """Test memory usage patterns and cleanup behavior"""
        import psutil
        import os
        
        config = PerformanceTestConfig()
        page = RealisticMockPage(thumbnail_count=20, response_delay=0.005)
        
        # Measure memory before
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple extractor instances and run extractions
        extractors = []
        results = []
        
        for i in range(10):
            extractor = EnhancedMetadataExtractor(config, Mock())
            extractors.append(extractor)
            
            result = await extractor.extract_metadata_from_page(page)
            results.append(result)
        
        # Measure memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        print(f"💾 Memory Usage Analysis:")
        print(f"  Memory before: {memory_before:.1f} MB")
        print(f"  Memory after: {memory_after:.1f} MB")
        print(f"  Memory increase: {memory_increase:.1f} MB")
        print(f"  Per extraction: {memory_increase/10:.1f} MB")
        
        # Clean up references
        extractors.clear()
        results.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Memory usage should be reasonable
        assert memory_increase < 100  # Should not use more than 100MB for 10 extractions
        
        return {
            'memory_before': memory_before,
            'memory_after': memory_after,
            'memory_increase': memory_increase,
            'per_extraction': memory_increase / 10
        }


# Test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])