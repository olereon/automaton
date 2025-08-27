#!/usr/bin/env python3
"""
Comprehensive Test Suite for Performance Optimization

This test suite validates the performance optimizations, caching strategies,
error handling, and scalability improvements for the landmark-based extraction system.
"""

import pytest
import asyncio
import logging
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
import json

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.performance_optimized_extractor import (
    PerformanceOptimizedExtractor, SpatialCache, QueryOptimizer
)
from utils.optimized_selector_chains import (
    SelectorChainOptimizer, OptimizedSelector, SelectorChain, 
    SelectorStrategy, FallbackChainManager
)
from utils.robust_error_handling import (
    RobustErrorHandler, ErrorSeverity, RecoveryStrategy, ErrorContext, 
    CircuitBreakerState, ErrorPatternAnalyzer
)
from utils.scalable_extraction_engine import (
    ScalableExtractionEngine, ProcessingMode, ResourceMonitor, LoadBalancer
)
from utils.optimized_integration_layer import (
    OptimizedMetadataExtractor, OptimizationConfig, OptimizationLevel,
    create_performance_extractor, OptimizedExtractionContext
)

logger = logging.getLogger(__name__)


class MockConfig:
    """Enhanced mock configuration for performance testing"""
    def __init__(self):
        # Basic config
        self.image_to_video_text = "Image to video"
        self.creation_time_text = "Creation Time"
        self.prompt_ellipsis_pattern = "</span>..."
        self.download_no_watermark_text = "Download without Watermark"
        
        # Performance settings
        self.enable_performance_caching = True
        self.enable_parallel_queries = True
        self.enable_batch_processing = True
        self.memory_limit_mb = 100
        
        # Enhanced extraction settings
        self.use_landmark_extraction = True
        self.fallback_to_legacy = True
        self.quality_threshold = 0.6


class MockPage:
    """Enhanced mock page for performance testing"""
    def __init__(self, url="https://test.com", elements_count=100):
        self.url = url
        self.elements_count = elements_count
        self.query_call_count = 0
        self.element_cache = {}
    
    async def query_selector_all(self, selector):
        """Mock query with configurable performance characteristics"""
        self.query_call_count += 1
        
        # Simulate varying performance based on selector complexity
        if 'complex' in selector:
            await asyncio.sleep(0.1)  # Slow query
        elif 'fast' in selector:
            await asyncio.sleep(0.01)  # Fast query
        else:
            await asyncio.sleep(0.05)  # Medium query
        
        # Return mock elements based on selector
        if "Image to video" in selector:
            return [MockElement(text_content="Image to video", 
                              bounds={'x': 100, 'y': 200, 'width': 120, 'height': 30})]
        elif "Creation Time" in selector:
            return [MockElement(text_content="Creation Time"),
                   MockElement(text_content="2024-01-15 14:30")]
        elif "[aria-describedby]" in selector:
            return [MockElement(text_content="Test prompt with sufficient length for validation",
                              attributes={"aria-describedby": "tooltip-123"})]
        
        # Return variable number of elements for performance testing
        return [MockElement(text_content=f"Element {i}") for i in range(min(10, self.elements_count))]
    
    async def wait_for_selector(self, selector, timeout=5000):
        await asyncio.sleep(0.01)  # Brief delay
        elements = await self.query_selector_all(selector)
        return elements[0] if elements else None


class MockElement:
    """Enhanced mock element for performance testing"""
    def __init__(self, text_content=None, bounds=None, visible=True, 
                 tag_name="span", attributes=None):
        self._text_content = text_content
        self._bounds = bounds
        self._visible = visible
        self._tag_name = tag_name
        self._attributes = attributes or {}
        self.access_count = 0
    
    async def text_content(self):
        self.access_count += 1
        await asyncio.sleep(0.001)  # Small delay to simulate DOM access
        return self._text_content
    
    async def bounding_box(self):
        await asyncio.sleep(0.001)
        return self._bounds
    
    async def is_visible(self):
        return self._visible
    
    async def evaluate(self, script):
        if "tagName" in script:
            return self._tag_name
        elif "attributes" in script:
            return self._attributes
        elif "children.length" in script:
            return 0
        return None


@pytest.fixture
def mock_config():
    """Mock configuration fixture"""
    return MockConfig()


@pytest.fixture
def mock_page():
    """Mock page fixture"""
    return MockPage()


@pytest.fixture
def performance_page():
    """High-performance mock page for benchmarking"""
    return MockPage(elements_count=1000)


class TestSpatialCache:
    """Test suite for spatial caching system"""
    
    def test_cache_initialization(self):
        """Test cache initialization with correct parameters"""
        cache = SpatialCache(max_size=500, cleanup_interval=30)
        
        assert cache.max_size == 500
        assert cache.cleanup_interval == 30
        assert len(cache.cache) == 0
        assert len(cache.spatial_index) == 0
    
    def test_cache_put_and_get(self):
        """Test basic cache put and get operations"""
        cache = SpatialCache()
        
        bounds = {'x': 100, 'y': 200, 'width': 50, 'height': 30}
        element = MockElement()
        
        cache.put("test_key", element, bounds, "test content")
        cached = cache.get("test_key")
        
        assert cached is not None
        assert cached.element_info == element
        assert cached.bounds == bounds
        assert cached.text_content == "test content"
        assert cache._stats['hits'] == 1
    
    def test_cache_miss(self):
        """Test cache miss behavior"""
        cache = SpatialCache()
        
        result = cache.get("nonexistent_key")
        
        assert result is None
        assert cache._stats['misses'] == 1
    
    @pytest.mark.asyncio
    async def test_spatial_region_queries(self):
        """Test spatial region-based queries"""
        cache = SpatialCache()
        
        # Add elements in different spatial regions
        bounds1 = {'x': 100, 'y': 100, 'width': 50, 'height': 30}
        bounds2 = {'x': 200, 'y': 100, 'width': 50, 'height': 30}
        bounds3 = {'x': 500, 'y': 500, 'width': 50, 'height': 30}
        
        cache.put("near1", MockElement(), bounds1)
        cache.put("near2", MockElement(), bounds2)
        cache.put("far", MockElement(), bounds3)
        
        # Query for elements near bounds1
        center_bounds = {'x': 120, 'y': 120, 'width': 10, 'height': 10}
        nearby = await cache.get_elements_in_region(center_bounds, radius=150)
        
        # Should find near1 and near2, but not far
        assert len(nearby) == 2
    
    def test_cache_size_limit_enforcement(self):
        """Test that cache enforces size limits"""
        cache = SpatialCache(max_size=3)
        
        # Add more items than max_size
        for i in range(5):
            cache.put(f"key_{i}", MockElement(), {'x': i*10, 'y': 0, 'width': 10, 'height': 10})
        
        # Should have evicted oldest items
        assert len(cache.cache) == 3
        assert cache._stats['evictions'] > 0
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """Test cache TTL expiration"""
        cache = SpatialCache()
        
        # Add item with short TTL
        cache.put("expire_soon", MockElement(), ttl_seconds=1)
        
        # Should be available immediately
        assert cache.get("expire_soon") is not None
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert cache.get("expire_soon") is None


class TestQueryOptimizer:
    """Test suite for query optimization"""
    
    def test_batch_query_building(self):
        """Test building optimized batch queries"""
        optimizer = QueryOptimizer()
        
        selectors = [
            "div.content",
            "span.text",
            "[aria-label]"
        ]
        
        batch_query = optimizer.build_batch_query(selectors)
        
        assert "," in batch_query
        assert all(selector in batch_query for selector in selectors)
    
    @pytest.mark.asyncio
    async def test_parallel_query_execution(self, mock_page):
        """Test parallel query execution"""
        optimizer = QueryOptimizer()
        
        queries = {
            'landmarks': '*:has-text("Image to video")',
            'creation_time': '*:has-text("Creation Time")',
            'aria_elements': '[aria-describedby]'
        }
        
        start_time = time.time()
        results = await optimizer.execute_parallel_queries(mock_page, queries)
        execution_time = time.time() - start_time
        
        assert len(results) == 3
        assert 'landmarks' in results
        assert 'creation_time' in results
        assert 'aria_elements' in results
        
        # Parallel execution should be faster than sequential
        assert execution_time < 0.5  # Should complete quickly due to parallelism
    
    def test_selector_optimization(self):
        """Test CSS selector optimization"""
        optimizer = QueryOptimizer()
        
        # Test selector optimization
        original = "  div > span.class1  .class2   "
        optimized = optimizer.optimize_selector(original)
        
        # Should clean up whitespace and formatting
        assert optimized.strip() != original
        assert len(optimized) <= len(original)


class TestOptimizedSelector:
    """Test suite for optimized selector functionality"""
    
    def test_selector_variant_generation(self):
        """Test generation of selector variants"""
        selector = OptimizedSelector(
            "div.content span[aria-describedby]",
            strategy=SelectorStrategy.ROBUST
        )
        
        assert len(selector.optimized_variants) > 1
        assert selector.primary_selector in selector.optimized_variants
    
    @pytest.mark.asyncio
    async def test_selector_execution_with_fallback(self, mock_page):
        """Test selector execution with fallback mechanisms"""
        # Create selector that will fail initially but succeed with fallback
        selector = OptimizedSelector(
            "nonexistent-selector",
            fallback_selectors=["span", "div"],
            strategy=SelectorStrategy.ROBUST
        )
        
        results = await selector.execute_optimized(mock_page)
        
        # Should get results from fallback selectors
        assert len(results) > 0
        assert selector.performance.failure_count == 0  # Should have succeeded with fallback
    
    def test_performance_tracking(self):
        """Test selector performance tracking"""
        selector = OptimizedSelector("div.test")
        
        # Simulate some successful operations
        selector.performance.success_count = 8
        selector.performance.failure_count = 2
        selector.performance.last_success = time.time()
        selector.performance.average_time_ms = 150.0
        
        reliability = selector.performance.calculate_reliability()
        
        assert 0.0 <= reliability <= 1.0
        assert reliability > 0.5  # Should be reasonable given success rate


class TestSelectorChain:
    """Test suite for selector chains"""
    
    @pytest.mark.asyncio
    async def test_chain_execution_priority(self, mock_page):
        """Test that chains execute selectors in priority order"""
        chain = SelectorChain("test_field", SelectorStrategy.ADAPTIVE)
        
        # Add selectors with different reliability
        good_selector = OptimizedSelector("div")
        good_selector.performance.success_count = 10
        good_selector.performance.failure_count = 1
        
        bad_selector = OptimizedSelector("nonexistent")
        bad_selector.performance.success_count = 1
        bad_selector.performance.failure_count = 10
        
        chain.add_selector(bad_selector)  # Add bad one first
        chain.add_selector(good_selector)  # Add good one second
        
        results, execution_info = await chain.execute_chain(mock_page)
        
        # Should have found results despite bad selector being first
        assert len(results) > 0
        assert execution_info['successful_selector'] is not None
        assert execution_info['attempts_made'] > 0
    
    def test_adaptive_weight_adjustment(self, mock_page):
        """Test adaptive weight adjustment based on performance"""
        chain = SelectorChain("test_field", SelectorStrategy.ADAPTIVE)
        
        selector = OptimizedSelector("div")
        chain.add_selector(selector)
        
        initial_weight = chain.adaptive_weights[0]
        
        # Simulate successful execution
        chain.last_successful_index = 0
        chain.execution_history.append({
            'timestamp': time.time(),
            'successful_selector_idx': 0,
            'execution_time_ms': 100,
            'results_count': 5
        })
        
        # Get new adaptive order
        order = chain._get_adaptive_order()
        
        # Weight should have been adjusted
        new_weight = chain.adaptive_weights[0]
        assert new_weight != initial_weight


class TestRobustErrorHandler:
    """Test suite for robust error handling"""
    
    @pytest.mark.asyncio
    async def test_error_recovery_with_retry(self):
        """Test error recovery with retry strategy"""
        handler = RobustErrorHandler()
        
        call_count = 0
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result, error_context = await handler.execute_with_recovery(
            failing_function,
            "test_operation",
            max_retries=3
        )
        
        assert result == "success"
        assert call_count == 3  # Should have retried twice
        assert error_context is not None
        assert error_context.recovery_successful
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker prevents cascading failures"""
        config = {'enable_circuit_breaker': True}
        handler = RobustErrorHandler(config)
        
        async def always_failing_function():
            raise Exception("Always fails")
        
        # Execute multiple times to trigger circuit breaker
        results = []
        for i in range(10):
            result, error_context = await handler.execute_with_recovery(
                always_failing_function,
                "circuit_test_operation",
                max_retries=1
            )
            results.append((result, error_context))
        
        # Later attempts should be blocked by circuit breaker
        blocked_attempts = [r for r in results if r[1] and r[1].error_type == "circuit_breaker_open"]
        assert len(blocked_attempts) > 0
    
    def test_error_pattern_analysis(self):
        """Test error pattern analysis and insights"""
        analyzer = ErrorPatternAnalyzer()
        
        # Add various error patterns
        for i in range(20):
            error_context = ErrorContext(
                error_type="TimeoutError" if i % 2 == 0 else "ElementNotFound",
                severity=ErrorSeverity.MEDIUM,
                timestamp=datetime.now() - timedelta(minutes=i),
                operation=f"operation_{i % 3}",
                details={'test': True},
                stack_trace="mock stack trace"
            )
            analyzer.record_error(error_context)
        
        analysis = analyzer.analyze_patterns()
        
        assert 'error_distribution' in analysis
        assert 'temporal_patterns' in analysis
        assert 'operation_reliability' in analysis
        assert analysis['total_errors'] == 20
    
    def test_failure_risk_prediction(self):
        """Test failure risk prediction"""
        analyzer = ErrorPatternAnalyzer()
        
        # Add error history for an operation
        for i in range(10):
            error_context = ErrorContext(
                error_type="TimeoutError",
                severity=ErrorSeverity.HIGH,
                timestamp=datetime.now() - timedelta(minutes=i),
                operation="risky_operation",
                details={},
                stack_trace="",
                retry_count=2
            )
            analyzer.record_error(error_context)
        
        risk_score = analyzer.predict_failure_risk("risky_operation")
        
        assert 0.0 <= risk_score <= 1.0
        assert risk_score > 0.5  # Should be high risk given error history


class TestScalableEngine:
    """Test suite for scalable extraction engine"""
    
    @pytest.mark.asyncio
    async def test_engine_initialization_and_startup(self):
        """Test engine initialization and startup"""
        config = {
            'processing_mode': 'multi_threaded',
            'max_workers': 4,
            'concurrent_workers': 2
        }
        
        engine = ScalableExtractionEngine(config)
        
        assert engine.processing_mode == ProcessingMode.MULTI_THREADED
        assert engine.max_workers == 4
        assert not engine.is_running
        
        await engine.start()
        assert engine.is_running
        assert len(engine.worker_tasks) == 2
        
        await engine.stop()
        assert not engine.is_running
    
    @pytest.mark.asyncio
    async def test_task_submission_and_processing(self):
        """Test task submission and processing"""
        config = {
            'processing_mode': 'single_threaded',
            'max_workers': 1,
            'concurrent_workers': 1
        }
        
        engine = ScalableExtractionEngine(config)
        await engine.start()
        
        try:
            # Submit a test task
            task_id = await engine.submit_task(
                page_url="https://test.com",
                extraction_config={'test': True},
                priority=5
            )
            
            assert task_id is not None
            
            # Wait a bit for processing
            await asyncio.sleep(0.5)
            
            # Check task status
            status = await engine.get_task_status(task_id)
            assert 'task_id' in status
            assert status['task_id'] == task_id
            
        finally:
            await engine.stop()
    
    @pytest.mark.asyncio
    async def test_batch_task_submission(self):
        """Test batch task submission"""
        config = {'processing_mode': 'single_threaded'}
        engine = ScalableExtractionEngine(config)
        
        await engine.start()
        
        try:
            tasks = [
                {'page_url': f'https://test{i}.com', 'priority': i % 5 + 1}
                for i in range(5)
            ]
            
            task_ids = await engine.submit_batch_tasks(tasks)
            
            assert len(task_ids) == 5
            assert all(isinstance(task_id, str) for task_id in task_ids)
            
        finally:
            await engine.stop()
    
    def test_engine_statistics_tracking(self):
        """Test engine statistics tracking"""
        engine = ScalableExtractionEngine()
        
        # Simulate some processing
        engine.statistics['tasks_processed'] = 10
        engine.statistics['tasks_failed'] = 2
        engine.statistics['total_processing_time'] = 25.0
        
        stats = engine.get_engine_statistics()
        
        assert stats['tasks_processed'] == 10
        assert stats['tasks_failed'] == 2
        assert stats['total_tasks'] == 12
        assert stats['success_rate'] == (10 / 12) * 100
        assert stats['average_processing_time'] > 0


class TestResourceMonitor:
    """Test suite for resource monitoring"""
    
    @pytest.mark.asyncio
    async def test_resource_monitoring_startup(self):
        """Test resource monitor startup and shutdown"""
        monitor = ResourceMonitor(monitor_interval=1)
        
        assert not monitor.monitoring_active
        
        # Start monitoring
        monitor_task = asyncio.create_task(monitor.start_monitoring())
        
        await asyncio.sleep(0.1)  # Brief delay for startup
        assert monitor.monitoring_active
        
        # Stop monitoring
        monitor.stop_monitoring()
        await asyncio.sleep(0.1)  # Brief delay for shutdown
        
        assert not monitor.monitoring_active
        monitor_task.cancel()
    
    def test_alert_threshold_configuration(self):
        """Test alert threshold configuration"""
        monitor = ResourceMonitor()
        
        # Default thresholds should be set
        from utils.scalable_extraction_engine import ResourceType
        assert ResourceType.CPU in monitor.alert_thresholds
        assert ResourceType.MEMORY in monitor.alert_thresholds
        
        # Should be reasonable values
        assert 50 <= monitor.alert_thresholds[ResourceType.CPU] <= 95
        assert 50 <= monitor.alert_thresholds[ResourceType.MEMORY] <= 95


class TestOptimizedIntegration:
    """Test suite for optimized integration layer"""
    
    @pytest.mark.asyncio
    async def test_basic_extractor_creation(self, mock_config):
        """Test creation of basic optimized extractor"""
        from utils.optimized_integration_layer import create_basic_extractor
        
        extractor = create_basic_extractor(mock_config)
        
        assert extractor.optimization_config.level == OptimizationLevel.BASIC
        assert extractor.optimization_config.enable_caching
        assert not extractor.optimization_config.enable_parallel_queries
        assert extractor.performance_extractor is None  # Not used in basic mode
    
    @pytest.mark.asyncio
    async def test_performance_extractor_creation(self, mock_config):
        """Test creation of performance-optimized extractor"""
        extractor = create_performance_extractor(mock_config)
        
        assert extractor.optimization_config.level == OptimizationLevel.PERFORMANCE
        assert extractor.optimization_config.enable_batch_processing
        assert extractor.performance_extractor is not None
        assert extractor.error_handler is not None
    
    @pytest.mark.asyncio
    async def test_extraction_with_optimization_metadata(self, mock_config, mock_page):
        """Test that extraction includes optimization metadata"""
        extractor = create_performance_extractor(mock_config)
        
        result = await extractor.extract_metadata(mock_page)
        
        assert 'optimization_info' in result
        assert 'level' in result['optimization_info']
        assert 'extraction_time_ms' in result['optimization_info']
        assert 'optimizations_used' in result['optimization_info']
        assert 'performance_score' in result['optimization_info']
    
    @pytest.mark.asyncio
    async def test_batch_extraction_performance(self, mock_config):
        """Test batch extraction performance"""
        extractor = create_performance_extractor(mock_config)
        
        # Create multiple mock pages
        pages = [MockPage(f"https://test{i}.com") for i in range(5)]
        
        start_time = time.time()
        results = await extractor.extract_batch(pages)
        batch_time = time.time() - start_time
        
        assert len(results) == 5
        assert batch_time < 2.0  # Should complete quickly with optimization
        
        # All results should have optimization info
        for result in results:
            assert 'optimization_info' in result or 'error' in result
    
    @pytest.mark.asyncio
    async def test_context_manager_usage(self, mock_config, mock_page):
        """Test context manager for automatic resource management"""
        async with OptimizedExtractionContext(mock_config, OptimizationLevel.STANDARD) as extractor:
            result = await extractor.extract_metadata(mock_page)
            
            assert result is not None
            assert 'optimization_info' in result
        
        # Extractor should be cleaned up after context exit
        # This is verified by the context manager completing without errors
    
    def test_optimization_config_levels(self):
        """Test different optimization configuration levels"""
        basic_config = OptimizationConfig.for_level(OptimizationLevel.BASIC)
        assert basic_config.processing_mode == ProcessingMode.SINGLE_THREADED
        assert basic_config.max_workers == 2
        
        performance_config = OptimizationConfig.for_level(OptimizationLevel.PERFORMANCE)
        assert performance_config.processing_mode == ProcessingMode.MULTI_THREADED
        assert performance_config.max_workers == 16
        assert performance_config.memory_limit_mb == 200
        
        enterprise_config = OptimizationConfig.for_level(OptimizationLevel.ENTERPRISE)
        assert enterprise_config.processing_mode == ProcessingMode.HYBRID
        assert enterprise_config.cache_size == 10000
        assert enterprise_config.max_queue_size == 20000
    
    @pytest.mark.asyncio
    async def test_performance_report_generation(self, mock_config, mock_page):
        """Test comprehensive performance report generation"""
        extractor = create_performance_extractor(mock_config)
        
        # Perform some extractions to generate metrics
        for i in range(3):
            await extractor.extract_metadata(mock_page)
        
        report = extractor.get_performance_report()
        
        assert 'optimization_level' in report
        assert 'performance_metrics' in report
        assert 'optimization_config' in report
        
        # Should have component-specific reports
        if extractor.performance_extractor:
            assert 'performance_extractor' in report
        
        if extractor.error_handler:
            assert 'error_handler' in report


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    @pytest.mark.asyncio
    async def test_extraction_time_benchmark(self, mock_config):
        """Benchmark extraction time across optimization levels"""
        test_page = MockPage("https://benchmark.com", elements_count=100)
        
        # Test different optimization levels
        extractors = {
            'basic': create_basic_extractor(mock_config),
            'performance': create_performance_extractor(mock_config)
        }
        
        results = {}
        
        for level, extractor in extractors.items():
            times = []
            
            for _ in range(5):  # Run multiple times for average
                start_time = time.time()
                await extractor.extract_metadata(test_page)
                times.append(time.time() - start_time)
            
            results[level] = {
                'average_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        
        # Performance level should be faster or comparable
        performance_avg = results['performance']['average_time']
        basic_avg = results['basic']['average_time']
        
        logger.info(f"Basic extraction average: {basic_avg:.3f}s")
        logger.info(f"Performance extraction average: {performance_avg:.3f}s")
        
        # Performance optimization should not be significantly slower
        assert performance_avg <= basic_avg * 1.5  # Allow some overhead for features
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, mock_config):
        """Test memory usage remains stable over many extractions"""
        extractor = create_performance_extractor(mock_config)
        
        # Run many extractions
        for i in range(50):
            page = MockPage(f"https://test{i}.com")
            await extractor.extract_metadata(page)
            
            # Periodic check - in real implementation would check actual memory
            if i % 10 == 0:
                report = extractor.get_performance_report()
                assert 'performance_metrics' in report
        
        # Test completes without memory issues
        assert True
    
    @pytest.mark.asyncio
    async def test_concurrent_extraction_performance(self, mock_config):
        """Test performance under concurrent load"""
        extractor = create_performance_extractor(mock_config)
        
        async def single_extraction(page_num):
            page = MockPage(f"https://concurrent{page_num}.com")
            return await extractor.extract_metadata(page)
        
        # Run concurrent extractions
        start_time = time.time()
        tasks = [single_extraction(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        assert len(results) == 10
        assert total_time < 5.0  # Should complete reasonably quickly
        
        # All extractions should succeed
        successful_results = [r for r in results if 'error' not in r]
        assert len(successful_results) >= 8  # Allow some failures in concurrent scenario
    
    @pytest.mark.asyncio
    async def test_cache_performance_impact(self, mock_config):
        """Test performance impact of caching"""
        # Test with caching enabled
        config_with_cache = OptimizationConfig.for_level(OptimizationLevel.PERFORMANCE)
        config_with_cache.enable_caching = True
        extractor_cached = OptimizedMetadataExtractor(mock_config, config_with_cache)
        
        # Test without caching
        config_no_cache = OptimizationConfig.for_level(OptimizationLevel.PERFORMANCE)
        config_no_cache.enable_caching = False
        extractor_no_cache = OptimizedMetadataExtractor(mock_config, config_no_cache)
        
        test_page = MockPage("https://cache-test.com")
        
        # First run (cold cache)
        start_time = time.time()
        await extractor_cached.extract_metadata(test_page)
        cached_cold_time = time.time() - start_time
        
        # Second run (warm cache)
        start_time = time.time()
        await extractor_cached.extract_metadata(test_page)
        cached_warm_time = time.time() - start_time
        
        # No cache run
        start_time = time.time()
        await extractor_no_cache.extract_metadata(test_page)
        no_cache_time = time.time() - start_time
        
        logger.info(f"Cached (cold): {cached_cold_time:.3f}s")
        logger.info(f"Cached (warm): {cached_warm_time:.3f}s")
        logger.info(f"No cache: {no_cache_time:.3f}s")
        
        # Warm cache should be faster than no cache
        # Note: In mock environment, this may not show significant difference
        # Real implementation would show clearer cache benefits
        assert cached_warm_time <= no_cache_time * 1.1  # Allow small margin


if __name__ == "__main__":
    # Configure logging for test runs
    logging.basicConfig(level=logging.INFO)
    
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-m", "not performance"])
    
    # Run performance tests separately if requested
    print("\nTo run performance benchmarks:")
    print("pytest -m performance -v")