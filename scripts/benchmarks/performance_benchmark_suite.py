#!/usr/bin/env python3
"""
Performance Benchmark Suite
Comprehensive benchmarking system for validating generation download optimizations.
Tests memory usage, DOM query performance, concurrent processing, and resource efficiency.
"""

import asyncio
import time
import json
import logging
import gc
import psutil
import tracemalloc
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.performance_optimized_generation_download_manager import (
    PerformanceOptimizedGenerationDownloadManager,
    OptimizedGenerationDownloadConfig,
    PerformanceMode
)
from utils.generation_download_manager_enhanced import (
    EnhancedGenerationDownloadManager,
    EnhancedGenerationDownloadConfig
)
from utils.performance_monitor import PerformanceMonitor, get_monitor, track_performance
from utils.download_manager import DownloadManager, DownloadConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Individual benchmark test result"""
    test_name: str
    implementation: str
    duration_seconds: float
    memory_peak_mb: float
    memory_average_mb: float
    cpu_average_percent: float
    throughput_items_per_second: float
    success_rate_percent: float
    error_count: int
    gc_collections: int
    cache_hit_rate: float = 0.0
    concurrent_workers: int = 0
    batch_size: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BenchmarkConfiguration:
    """Benchmark test configuration"""
    test_name: str
    description: str
    max_items: int
    batch_size: int
    concurrent_workers: int
    duration_limit_seconds: int
    memory_limit_mb: int
    expected_throughput_min: float = 0.0
    expected_memory_max_mb: float = 1000.0
    repeat_count: int = 3


class MockPage:
    """Mock Playwright page for testing"""
    
    def __init__(self, mock_items: int = 100):
        self.mock_items = mock_items
        self.query_calls = 0
        self.click_calls = 0
        self.evaluate_calls = 0
    
    async def query_selector_all(self, selector: str) -> List['MockElement']:
        """Mock query selector with artificial delay"""
        self.query_calls += 1
        await asyncio.sleep(0.01)  # Simulate DOM query delay
        
        if 'thumbnail' in selector.lower():
            return [MockElement(i) for i in range(min(self.mock_items, 20))]
        return []
    
    async def query_selector(self, selector: str) -> Optional['MockElement']:
        """Mock single element query"""
        self.query_calls += 1
        await asyncio.sleep(0.005)
        return MockElement(0) if self.mock_items > 0 else None
    
    async def evaluate(self, script: str, *args) -> Any:
        """Mock JavaScript evaluation"""
        self.evaluate_calls += 1
        await asyncio.sleep(0.02)  # Simulate JS execution delay
        
        if 'querySelectorAll' in script:
            return [{'index': i, 'visible': True, 'textContent': f'Item {i}'} for i in range(min(self.mock_items, 10))]
        elif 'download' in script.lower():
            return {
                'url': f'https://example.com/download/{time.time()}',
                'creationTime': '2024-01-01 12:00:00',
                'prompt': f'Test prompt {time.time()}'
            }
        
        return {}


class MockElement:
    """Mock Playwright element for testing"""
    
    def __init__(self, item_id: int):
        self.item_id = item_id
        self._click_count = 0
    
    async def click(self, timeout: int = 30000):
        """Mock element click"""
        self._click_count += 1
        await asyncio.sleep(0.05)  # Simulate click delay
        
        # Simulate occasional stale element errors
        if self._click_count > 2 and self.item_id % 10 == 0:
            raise Exception("Element is not attached to the DOM")
    
    async def get_attribute(self, name: str) -> Optional[str]:
        """Mock attribute getter"""
        await asyncio.sleep(0.001)
        
        if name == 'data-spm-anchor-id':
            return f'anchor-{self.item_id}-{int(time.time())}'
        elif name == 'src':
            return f'https://example.com/image/{self.item_id}.jpg'
        
        return None
    
    async def bounding_box(self) -> Dict:
        """Mock bounding box"""
        await asyncio.sleep(0.002)
        return {
            'x': self.item_id * 200,
            'y': 100,
            'width': 180,
            'height': 240
        }
    
    async def evaluate(self, script: str) -> Any:
        """Mock element evaluation"""
        await asyncio.sleep(0.01)
        return f"hash_{self.item_id}_{int(time.time())}"


class MockDownloadManager:
    """Mock download manager for testing"""
    
    def __init__(self, success_rate: float = 0.95, download_delay: float = 0.1):
        self.success_rate = success_rate
        self.download_delay = download_delay
        self.downloads_attempted = 0
        self.downloads_successful = 0
    
    async def download_file_streaming(self, url: str, filename: str, config: DownloadConfig) -> Tuple[bool, str, str]:
        """Mock streaming download"""
        self.downloads_attempted += 1
        await asyncio.sleep(self.download_delay)
        
        success = (self.downloads_attempted / 100) < self.success_rate or (self.downloads_attempted % 100) < (self.success_rate * 100)
        
        if success:
            self.downloads_successful += 1
            return True, f"/tmp/{filename}", ""
        else:
            return False, "", "Mock download failure"


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite"""
    
    def __init__(self, output_dir: str = "./benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.monitor = get_monitor()
        
        # Benchmark configurations
        self.benchmark_configs = [
            BenchmarkConfiguration(
                test_name="memory_efficiency_small_batch",
                description="Memory efficiency with small batch processing",
                max_items=25,
                batch_size=5,
                concurrent_workers=2,
                duration_limit_seconds=120,
                memory_limit_mb=200,
                expected_throughput_min=0.2,
                expected_memory_max_mb=150
            ),
            BenchmarkConfiguration(
                test_name="memory_efficiency_large_batch",
                description="Memory efficiency with large batch processing",
                max_items=100,
                batch_size=20,
                concurrent_workers=5,
                duration_limit_seconds=300,
                memory_limit_mb=400,
                expected_throughput_min=0.3,
                expected_memory_max_mb=350
            ),
            BenchmarkConfiguration(
                test_name="concurrent_processing_stress",
                description="Concurrent processing under stress",
                max_items=50,
                batch_size=10,
                concurrent_workers=8,
                duration_limit_seconds=180,
                memory_limit_mb=300,
                expected_throughput_min=0.25
            ),
            BenchmarkConfiguration(
                test_name="dom_query_optimization",
                description="DOM query caching and batching efficiency",
                max_items=200,
                batch_size=25,
                concurrent_workers=3,
                duration_limit_seconds=240,
                memory_limit_mb=250,
                expected_throughput_min=0.8
            ),
            BenchmarkConfiguration(
                test_name="resource_cleanup_validation",
                description="Resource cleanup and garbage collection",
                max_items=75,
                batch_size=15,
                concurrent_workers=4,
                duration_limit_seconds=300,
                memory_limit_mb=300,
                expected_throughput_min=0.2
            )
        ]
    
    async def run_all_benchmarks(self) -> Dict:
        """Run complete benchmark suite"""
        logger.info("Starting comprehensive performance benchmark suite")
        
        # Start performance monitoring
        await self.monitor.start_monitoring()
        
        try:
            # Run benchmarks for both implementations
            for config in self.benchmark_configs:
                logger.info(f"Running benchmark: {config.test_name}")
                
                # Test optimized implementation
                optimized_result = await self._run_benchmark_optimized(config)
                self.results.append(optimized_result)
                
                # Test enhanced (baseline) implementation
                enhanced_result = await self._run_benchmark_enhanced(config)
                self.results.append(enhanced_result)
                
                # Cool down period between benchmarks
                await asyncio.sleep(5)
                gc.collect()
            
            # Generate comprehensive report
            report = self._generate_benchmark_report()
            
            # Save results
            await self._save_results(report)
            
            return report
            
        finally:
            await self.monitor.stop_monitoring()
    
    async def _run_benchmark_optimized(self, config: BenchmarkConfiguration) -> BenchmarkResult:
        """Run benchmark on optimized implementation"""
        # Configure optimized manager
        opt_config = OptimizedGenerationDownloadConfig(
            max_downloads=config.max_items,
            batch_size=config.batch_size,
            max_concurrent_workers=config.concurrent_workers,
            memory_limit_mb=config.memory_limit_mb,
            performance_mode=PerformanceMode.PRODUCTION
        )
        
        manager = PerformanceOptimizedGenerationDownloadManager(opt_config)
        return await self._run_single_benchmark(
            manager, config, "optimized", 
            manager.process_generation_downloads_optimized
        )
    
    async def _run_benchmark_enhanced(self, config: BenchmarkConfiguration) -> BenchmarkResult:
        """Run benchmark on enhanced implementation (baseline)"""
        # Configure enhanced manager  
        enh_config = EnhancedGenerationDownloadConfig(
            max_downloads=config.max_items,
            batch_size=config.batch_size,
            max_concurrent_operations=config.concurrent_workers
        )
        
        manager = EnhancedGenerationDownloadManager(enh_config)
        return await self._run_single_benchmark(
            manager, config, "enhanced",
            manager.process_generation_downloads
        )
    
    async def _run_single_benchmark(
        self, 
        manager: Any,
        config: BenchmarkConfiguration,
        implementation: str,
        process_method: Callable
    ) -> BenchmarkResult:
        """Run a single benchmark test"""
        logger.info(f"Testing {implementation} implementation: {config.test_name}")
        
        # Setup monitoring
        tracemalloc.start()
        process = psutil.Process()
        
        # Memory tracking
        memory_samples = []
        cpu_samples = []
        
        # Mock objects
        mock_page = MockPage(config.max_items)
        mock_download_manager = MockDownloadManager()
        
        # Performance tracking
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024
        
        error_count = 0
        success_count = 0
        
        try:
            # Start background monitoring
            monitor_task = asyncio.create_task(
                self._monitor_resources(memory_samples, cpu_samples, process)
            )
            
            # Run the benchmark
            if implementation == "optimized":
                result = await process_method(
                    mock_page, mock_download_manager,
                    progress_callback=self._progress_callback
                )
            else:
                result = await process_method(
                    mock_page, mock_download_manager
                )
            
            # Stop monitoring
            monitor_task.cancel()
            
            # Calculate metrics
            end_time = time.time()
            duration = end_time - start_time
            
            # Memory metrics
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            peak_memory_mb = peak_memory / 1024 / 1024
            avg_memory_mb = statistics.mean(memory_samples) if memory_samples else start_memory
            
            # CPU metrics
            avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
            
            # Success metrics
            if result.get('success', False):
                success_count = result.get('processed_count', 0)
            else:
                error_count = 1
            
            # Throughput
            throughput = success_count / duration if duration > 0 else 0
            success_rate = (success_count / max(success_count + error_count, 1)) * 100
            
            # GC collections
            gc_collections = sum(gc.get_count())
            
            # Cache hit rate (for optimized implementation)
            cache_hit_rate = 0.0
            if hasattr(manager, 'dom_query_manager'):
                cache_stats = manager.dom_query_manager.get_cache_stats()
                cache_hit_rate = cache_stats.get('cache_stats', {}).get('hit_rate', 0.0)
            
            benchmark_result = BenchmarkResult(
                test_name=config.test_name,
                implementation=implementation,
                duration_seconds=duration,
                memory_peak_mb=peak_memory_mb,
                memory_average_mb=avg_memory_mb,
                cpu_average_percent=avg_cpu,
                throughput_items_per_second=throughput,
                success_rate_percent=success_rate,
                error_count=error_count,
                gc_collections=gc_collections,
                cache_hit_rate=cache_hit_rate,
                concurrent_workers=config.concurrent_workers,
                batch_size=config.batch_size
            )
            
            logger.info(
                f"{implementation} - {config.test_name}: "
                f"{throughput:.2f} items/sec, "
                f"{peak_memory_mb:.1f}MB peak memory, "
                f"{success_rate:.1f}% success rate"
            )
            
            return benchmark_result
            
        except Exception as e:
            logger.error(f"Benchmark failed for {implementation} - {config.test_name}: {e}")
            
            return BenchmarkResult(
                test_name=config.test_name,
                implementation=implementation,
                duration_seconds=time.time() - start_time,
                memory_peak_mb=0,
                memory_average_mb=0,
                cpu_average_percent=0,
                throughput_items_per_second=0,
                success_rate_percent=0,
                error_count=1,
                gc_collections=0,
                cache_hit_rate=0.0,
                concurrent_workers=config.concurrent_workers,
                batch_size=config.batch_size
            )
        
        finally:
            tracemalloc.stop()
    
    async def _monitor_resources(self, memory_samples: List[float], cpu_samples: List[float], process: psutil.Process):
        """Background resource monitoring"""
        try:
            while True:
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                
                memory_samples.append(memory_mb)
                cpu_samples.append(cpu_percent)
                
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    async def _progress_callback(self, progress_info: Dict):
        """Progress callback for monitoring"""
        # Log progress periodically
        processed = progress_info.get('processed', 0)
        if processed % 10 == 0:
            logger.debug(f"Progress: {processed} items processed")
    
    def _generate_benchmark_report(self) -> Dict:
        """Generate comprehensive benchmark report"""
        report = {
            'benchmark_suite': 'Performance Optimization Validation',
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'test_results': [result.to_dict() for result in self.results],
            'summary': {},
            'comparisons': {},
            'performance_improvements': {}
        }
        
        # Group results by test name
        test_groups = {}
        for result in self.results:
            if result.test_name not in test_groups:
                test_groups[result.test_name] = {}
            test_groups[result.test_name][result.implementation] = result
        
        # Generate comparisons
        for test_name, implementations in test_groups.items():
            if 'optimized' in implementations and 'enhanced' in implementations:
                opt = implementations['optimized']
                enh = implementations['enhanced']
                
                comparison = {
                    'throughput_improvement': self._calculate_improvement(
                        opt.throughput_items_per_second, enh.throughput_items_per_second
                    ),
                    'memory_reduction': self._calculate_reduction(
                        opt.memory_peak_mb, enh.memory_peak_mb
                    ),
                    'cpu_efficiency': self._calculate_reduction(
                        opt.cpu_average_percent, enh.cpu_average_percent
                    ),
                    'cache_hit_rate': opt.cache_hit_rate,
                    'success_rate_comparison': {
                        'optimized': opt.success_rate_percent,
                        'enhanced': enh.success_rate_percent
                    }
                }
                
                report['comparisons'][test_name] = comparison
        
        # Calculate overall performance improvements
        if report['comparisons']:
            throughput_improvements = [
                comp['throughput_improvement'] 
                for comp in report['comparisons'].values() 
                if comp['throughput_improvement'] is not None
            ]
            memory_reductions = [
                comp['memory_reduction']
                for comp in report['comparisons'].values()
                if comp['memory_reduction'] is not None
            ]
            
            report['performance_improvements'] = {
                'average_throughput_improvement_percent': statistics.mean(throughput_improvements) if throughput_improvements else 0,
                'average_memory_reduction_percent': statistics.mean(memory_reductions) if memory_reductions else 0,
                'tests_with_improvements': len([i for i in throughput_improvements if i > 0]),
                'total_comparisons': len(throughput_improvements)
            }
        
        # Summary statistics
        optimized_results = [r for r in self.results if r.implementation == 'optimized']
        enhanced_results = [r for r in self.results if r.implementation == 'enhanced']
        
        report['summary'] = {
            'optimized_implementation': {
                'average_throughput': statistics.mean([r.throughput_items_per_second for r in optimized_results]) if optimized_results else 0,
                'average_memory_mb': statistics.mean([r.memory_peak_mb for r in optimized_results]) if optimized_results else 0,
                'average_cache_hit_rate': statistics.mean([r.cache_hit_rate for r in optimized_results]) if optimized_results else 0,
                'total_success_rate': statistics.mean([r.success_rate_percent for r in optimized_results]) if optimized_results else 0
            },
            'enhanced_implementation': {
                'average_throughput': statistics.mean([r.throughput_items_per_second for r in enhanced_results]) if enhanced_results else 0,
                'average_memory_mb': statistics.mean([r.memory_peak_mb for r in enhanced_results]) if enhanced_results else 0,
                'total_success_rate': statistics.mean([r.success_rate_percent for r in enhanced_results]) if enhanced_results else 0
            }
        }
        
        return report
    
    def _calculate_improvement(self, optimized_value: float, baseline_value: float) -> Optional[float]:
        """Calculate percentage improvement"""
        if baseline_value == 0:
            return None
        return ((optimized_value - baseline_value) / baseline_value) * 100
    
    def _calculate_reduction(self, optimized_value: float, baseline_value: float) -> Optional[float]:
        """Calculate percentage reduction"""
        if baseline_value == 0:
            return None
        return ((baseline_value - optimized_value) / baseline_value) * 100
    
    async def _save_results(self, report: Dict):
        """Save benchmark results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON report
        json_file = self.output_dir / f"benchmark_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save CSV summary
        csv_file = self.output_dir / f"benchmark_summary_{timestamp}.csv"
        with open(csv_file, 'w') as f:
            f.write("test_name,implementation,throughput_items_per_sec,memory_peak_mb,cpu_avg_percent,success_rate_percent,cache_hit_rate\n")
            for result in self.results:
                f.write(f"{result.test_name},{result.implementation},{result.throughput_items_per_second:.3f},"
                       f"{result.memory_peak_mb:.1f},{result.cpu_average_percent:.1f},"
                       f"{result.success_rate_percent:.1f},{result.cache_hit_rate:.3f}\n")
        
        logger.info(f"Benchmark results saved to {json_file} and {csv_file}")


async def main():
    """Main benchmark execution"""
    print("🚀 Starting Performance Benchmark Suite")
    print("=" * 60)
    
    suite = PerformanceBenchmarkSuite()
    
    try:
        report = await suite.run_all_benchmarks()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        
        improvements = report.get('performance_improvements', {})
        if improvements:
            print(f"Average Throughput Improvement: {improvements.get('average_throughput_improvement_percent', 0):.1f}%")
            print(f"Average Memory Reduction: {improvements.get('average_memory_reduction_percent', 0):.1f}%")
            print(f"Tests Showing Improvement: {improvements.get('tests_with_improvements', 0)}/{improvements.get('total_comparisons', 0)}")
        
        # Print detailed results
        print("\n📈 DETAILED RESULTS")
        print("-" * 60)
        for result in suite.results:
            print(f"{result.implementation.upper()} - {result.test_name}:")
            print(f"  Throughput: {result.throughput_items_per_second:.2f} items/sec")
            print(f"  Peak Memory: {result.memory_peak_mb:.1f} MB")
            print(f"  Success Rate: {result.success_rate_percent:.1f}%")
            if result.cache_hit_rate > 0:
                print(f"  Cache Hit Rate: {result.cache_hit_rate:.2f}")
            print()
        
        print("✅ Benchmark suite completed successfully!")
        
    except Exception as e:
        print(f"❌ Benchmark suite failed: {e}")
        logger.exception("Benchmark execution failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))