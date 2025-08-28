#!/usr/bin/env python3
"""
Memory Optimization Validator
Specialized testing script for validating memory usage optimizations
in the generation download system with detailed memory profiling.
"""

import asyncio
import sys
import os
import time
import gc
import tracemalloc
import psutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.performance_optimized_generation_download_manager import (
    PerformanceOptimizedGenerationDownloadManager,
    OptimizedGenerationDownloadConfig,
    PerformanceMode
)
from utils.performance_monitor import PerformanceMonitor, get_monitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Memory snapshot at a specific point in time"""
    timestamp: float
    rss_mb: float
    vms_mb: float
    heap_mb: float
    tracemalloc_current_mb: float
    tracemalloc_peak_mb: float
    gc_objects: int
    gc_collections: Tuple[int, int, int]
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'rss_mb': self.rss_mb,
            'vms_mb': self.vms_mb,
            'heap_mb': self.heap_mb,
            'tracemalloc_current_mb': self.tracemalloc_current_mb,
            'tracemalloc_peak_mb': self.tracemalloc_peak_mb,
            'gc_objects': self.gc_objects,
            'gc_collections': list(self.gc_collections)
        }


class MemoryOptimizationValidator:
    """Comprehensive memory optimization validation"""
    
    def __init__(self, output_dir: str = "./memory_validation_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.process = psutil.Process()
        self.snapshots = []
        self.test_results = {}
        
        # Start tracemalloc for detailed memory tracking
        tracemalloc.start()
        
    def take_memory_snapshot(self, label: str = "") -> MemorySnapshot:
        """Take detailed memory snapshot"""
        memory_info = self.process.memory_info()
        current_memory, peak_memory = tracemalloc.get_traced_memory()
        gc_stats = gc.get_stats()
        gc_counts = gc.get_count()
        
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            heap_mb=0,  # Will be calculated if available
            tracemalloc_current_mb=current_memory / 1024 / 1024,
            tracemalloc_peak_mb=peak_memory / 1024 / 1024,
            gc_objects=len(gc.get_objects()),
            gc_collections=(gc_counts[0], gc_counts[1], gc_counts[2])
        )
        
        if label:
            logger.info(f"Memory snapshot '{label}': RSS={snapshot.rss_mb:.1f}MB, Tracemalloc={snapshot.tracemalloc_current_mb:.1f}MB")
        
        self.snapshots.append(snapshot)
        return snapshot
    
    async def run_memory_validation_suite(self) -> Dict:
        """Run comprehensive memory validation tests"""
        logger.info("Starting memory optimization validation suite")
        
        # Test scenarios with different memory profiles
        test_scenarios = [
            {
                'name': 'memory_constrained',
                'description': 'Low memory limit test',
                'config': {
                    'performance_mode': PerformanceMode.MEMORY_OPTIMIZED,
                    'memory_limit_mb': 100,
                    'batch_size': 3,
                    'max_concurrent_workers': 2,
                    'max_downloads': 20,
                    'enable_gc_optimization': True,
                    'gc_threshold_mb': 50
                }
            },
            {
                'name': 'large_batch_memory',
                'description': 'Large batch memory efficiency test',
                'config': {
                    'performance_mode': PerformanceMode.PRODUCTION,
                    'memory_limit_mb': 300,
                    'batch_size': 15,
                    'max_concurrent_workers': 5,
                    'max_downloads': 75,
                    'enable_gc_optimization': True,
                    'gc_threshold_mb': 150
                }
            },
            {
                'name': 'long_running_stability',
                'description': 'Long-running memory stability test',
                'config': {
                    'performance_mode': PerformanceMode.BALANCED,
                    'memory_limit_mb': 400,
                    'batch_size': 10,
                    'max_concurrent_workers': 4,
                    'max_downloads': 100,
                    'enable_gc_optimization': True,
                    'gc_threshold_mb': 200,
                    'max_processing_time': 600  # 10 minutes
                }
            },
            {
                'name': 'cache_efficiency',
                'description': 'Cache memory usage efficiency test',
                'config': {
                    'performance_mode': PerformanceMode.PRODUCTION,
                    'memory_limit_mb': 250,
                    'batch_size': 8,
                    'max_concurrent_workers': 3,
                    'max_downloads': 50,
                    'cache_size_limit': 500,
                    'cache_ttl_seconds': 180
                }
            }
        ]
        
        # Run each test scenario
        for scenario in test_scenarios:
            logger.info(f"Running memory test: {scenario['name']}")
            
            # Clear memory before test
            gc.collect()
            tracemalloc.clear_traces()
            
            # Take baseline snapshot
            baseline = self.take_memory_snapshot(f"{scenario['name']}_baseline")
            
            try:
                result = await self._run_memory_test_scenario(scenario)
                self.test_results[scenario['name']] = result
                
            except Exception as e:
                logger.error(f"Memory test {scenario['name']} failed: {e}")
                self.test_results[scenario['name']] = {
                    'success': False,
                    'error': str(e),
                    'baseline_memory_mb': baseline.rss_mb
                }
            
            # Cool down between tests
            await asyncio.sleep(5)
            gc.collect()
        
        # Generate comprehensive report
        report = self._generate_memory_report()
        await self._save_memory_results(report)
        
        return report
    
    async def _run_memory_test_scenario(self, scenario: Dict) -> Dict:
        """Run individual memory test scenario"""
        start_time = time.time()
        config_dict = scenario['config']
        
        # Create optimized configuration
        config = OptimizedGenerationDownloadConfig(
            downloads_folder=str(self.output_dir / "downloads" / scenario['name']),
            **config_dict
        )
        
        # Initialize manager
        manager = PerformanceOptimizedGenerationDownloadManager(config)
        
        # Memory tracking
        memory_timeline = []
        monitoring_task = None
        
        try:
            # Start memory monitoring
            monitoring_task = asyncio.create_task(
                self._monitor_memory_continuously(memory_timeline, interval=2)
            )
            
            # Take pre-execution snapshot
            pre_exec = self.take_memory_snapshot(f"{scenario['name']}_pre_execution")
            
            # Create mock processing environment
            mock_page = MockPageForMemoryTest(config.max_downloads)
            mock_download_manager = MockDownloadManagerForMemoryTest()
            
            # Run the optimized process
            progress_data = []
            
            async def memory_progress_callback(progress_info):
                snapshot = self.take_memory_snapshot()
                progress_data.append({
                    'processed': progress_info.get('processed', 0),
                    'memory_snapshot': snapshot.to_dict(),
                    'performance_metrics': progress_info.get('performance_metrics', {})
                })
            
            result = await manager.process_generation_downloads_optimized(
                mock_page, mock_download_manager, memory_progress_callback
            )
            
            # Take post-execution snapshot
            post_exec = self.take_memory_snapshot(f"{scenario['name']}_post_execution")
            
            # Force garbage collection and take final snapshot
            gc.collect()
            final_snapshot = self.take_memory_snapshot(f"{scenario['name']}_final")
            
            # Stop monitoring
            monitoring_task.cancel()
            
            # Calculate memory metrics
            duration = time.time() - start_time
            peak_memory = max(snap.rss_mb for snap in memory_timeline) if memory_timeline else post_exec.rss_mb
            avg_memory = sum(snap.rss_mb for snap in memory_timeline) / len(memory_timeline) if memory_timeline else post_exec.rss_mb
            
            # Memory efficiency calculations
            memory_growth = post_exec.rss_mb - pre_exec.rss_mb
            memory_cleanup_efficiency = (post_exec.rss_mb - final_snapshot.rss_mb) / max(memory_growth, 1) * 100
            
            # GC efficiency
            gc_collections_during = (
                final_snapshot.gc_collections[2] - pre_exec.gc_collections[2]
            )
            
            scenario_result = {
                'scenario_name': scenario['name'],
                'success': result.get('success', False),
                'duration_seconds': duration,
                'processed_count': result.get('processed_count', 0),
                'memory_metrics': {
                    'baseline_mb': pre_exec.rss_mb,
                    'peak_mb': peak_memory,
                    'final_mb': final_snapshot.rss_mb,
                    'average_mb': avg_memory,
                    'growth_mb': memory_growth,
                    'cleanup_efficiency_percent': memory_cleanup_efficiency,
                    'tracemalloc_peak_mb': final_snapshot.tracemalloc_peak_mb
                },
                'gc_metrics': {
                    'collections_during_test': gc_collections_during,
                    'objects_growth': final_snapshot.gc_objects - pre_exec.gc_objects
                },
                'memory_timeline': [snap.to_dict() for snap in memory_timeline],
                'progress_data': progress_data,
                'configuration': config_dict,
                'performance_validation': self._validate_memory_performance(
                    scenario, peak_memory, memory_growth, memory_cleanup_efficiency
                )
            }
            
            logger.info(
                f"Memory test {scenario['name']}: "
                f"Peak={peak_memory:.1f}MB, Growth={memory_growth:.1f}MB, "
                f"Cleanup={memory_cleanup_efficiency:.1f}%"
            )
            
            return scenario_result
            
        except Exception as e:
            if monitoring_task:
                monitoring_task.cancel()
            raise e
    
    async def _monitor_memory_continuously(self, memory_timeline: List, interval: float = 2):
        """Continuously monitor memory usage"""
        try:
            while True:
                snapshot = self.take_memory_snapshot()
                memory_timeline.append(snapshot)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
    
    def _validate_memory_performance(self, scenario: Dict, peak_memory: float, memory_growth: float, cleanup_efficiency: float) -> Dict:
        """Validate memory performance against expectations"""
        validation = {
            'passes_memory_limit': True,
            'efficient_memory_usage': True,
            'good_cleanup_efficiency': True,
            'warnings': [],
            'recommendations': []
        }
        
        config = scenario['config']
        memory_limit = config.get('memory_limit_mb', 400)
        
        # Check memory limit compliance
        if peak_memory > memory_limit:
            validation['passes_memory_limit'] = False
            validation['warnings'].append(f"Peak memory ({peak_memory:.1f}MB) exceeded limit ({memory_limit}MB)")
        
        # Check memory efficiency
        if memory_growth > memory_limit * 0.8:
            validation['efficient_memory_usage'] = False
            validation['warnings'].append(f"High memory growth ({memory_growth:.1f}MB)")
        
        # Check cleanup efficiency
        if cleanup_efficiency < 50:
            validation['good_cleanup_efficiency'] = False
            validation['warnings'].append(f"Poor memory cleanup efficiency ({cleanup_efficiency:.1f}%)")
            validation['recommendations'].append("Consider reducing batch size or enabling more aggressive GC")
        
        # Generate specific recommendations
        if peak_memory > memory_limit * 0.9:
            validation['recommendations'].append("Consider using MEMORY_OPTIMIZED performance mode")
        
        if memory_growth > 100:
            validation['recommendations'].append("Reduce batch size or concurrent workers to lower memory footprint")
        
        return validation
    
    def _generate_memory_report(self) -> Dict:
        """Generate comprehensive memory validation report"""
        successful_tests = [r for r in self.test_results.values() if r.get('success', False)]
        
        # Overall statistics
        if successful_tests:
            peak_memories = [r['memory_metrics']['peak_mb'] for r in successful_tests]
            memory_growths = [r['memory_metrics']['growth_mb'] for r in successful_tests]
            cleanup_efficiencies = [r['memory_metrics']['cleanup_efficiency_percent'] for r in successful_tests]
            
            overall_stats = {
                'avg_peak_memory_mb': sum(peak_memories) / len(peak_memories),
                'max_peak_memory_mb': max(peak_memories),
                'avg_memory_growth_mb': sum(memory_growths) / len(memory_growths),
                'avg_cleanup_efficiency_percent': sum(cleanup_efficiencies) / len(cleanup_efficiencies)
            }
        else:
            overall_stats = {}
        
        # Validation summary
        validation_summary = {
            'total_tests': len(self.test_results),
            'successful_tests': len(successful_tests),
            'tests_within_memory_limits': len([
                r for r in successful_tests 
                if r.get('performance_validation', {}).get('passes_memory_limit', False)
            ]),
            'tests_with_efficient_usage': len([
                r for r in successful_tests
                if r.get('performance_validation', {}).get('efficient_memory_usage', False)  
            ]),
            'tests_with_good_cleanup': len([
                r for r in successful_tests
                if r.get('performance_validation', {}).get('good_cleanup_efficiency', False)
            ])
        }
        
        report = {
            'memory_validation_suite': 'Performance Optimized Generation Download Manager',
            'timestamp': datetime.now().isoformat(),
            'validation_summary': validation_summary,
            'overall_statistics': overall_stats,
            'detailed_results': self.test_results,
            'memory_snapshots': [snap.to_dict() for snap in self.snapshots],
            'optimization_effectiveness': self._calculate_optimization_effectiveness(),
            'recommendations': self._generate_optimization_recommendations()
        }
        
        return report
    
    def _calculate_optimization_effectiveness(self) -> Dict:
        """Calculate how effective the memory optimizations are"""
        successful_tests = [r for r in self.test_results.values() if r.get('success', False)]
        
        if not successful_tests:
            return {}
        
        # Memory efficiency metrics
        memory_efficiencies = []
        for test in successful_tests:
            processed = test.get('processed_count', 0)
            peak_memory = test['memory_metrics']['peak_mb']
            
            if processed > 0:
                memory_per_item = peak_memory / processed
                memory_efficiencies.append(memory_per_item)
        
        # GC effectiveness
        gc_effectiveness = []
        for test in successful_tests:
            cleanup_eff = test['memory_metrics']['cleanup_efficiency_percent']
            gc_effectiveness.append(cleanup_eff)
        
        return {
            'avg_memory_per_item_mb': sum(memory_efficiencies) / len(memory_efficiencies) if memory_efficiencies else 0,
            'avg_gc_effectiveness_percent': sum(gc_effectiveness) / len(gc_effectiveness) if gc_effectiveness else 0,
            'memory_optimization_score': self._calculate_memory_optimization_score(successful_tests)
        }
    
    def _calculate_memory_optimization_score(self, successful_tests: List) -> float:
        """Calculate overall memory optimization score (0-100)"""
        if not successful_tests:
            return 0
        
        score_components = []
        
        for test in successful_tests:
            config = test['configuration']
            memory_limit = config.get('memory_limit_mb', 400)
            peak_memory = test['memory_metrics']['peak_mb']
            cleanup_eff = test['memory_metrics']['cleanup_efficiency_percent']
            
            # Memory usage score (0-40 points)
            memory_usage_score = max(0, 40 * (1 - peak_memory / (memory_limit * 1.2)))
            
            # Cleanup efficiency score (0-30 points)  
            cleanup_score = min(30, cleanup_eff * 30 / 100)
            
            # Growth control score (0-30 points)
            growth = test['memory_metrics']['growth_mb']
            growth_score = max(0, 30 * (1 - growth / memory_limit))
            
            test_score = memory_usage_score + cleanup_score + growth_score
            score_components.append(test_score)
        
        return sum(score_components) / len(score_components)
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate memory optimization recommendations"""
        recommendations = []
        successful_tests = [r for r in self.test_results.values() if r.get('success', False)]
        
        if not successful_tests:
            recommendations.append("❌ No successful tests - check system configuration")
            return recommendations
        
        # Analyze memory patterns
        high_memory_tests = [
            test for test in successful_tests
            if test['memory_metrics']['peak_mb'] > test['configuration'].get('memory_limit_mb', 400) * 0.8
        ]
        
        poor_cleanup_tests = [
            test for test in successful_tests  
            if test['memory_metrics']['cleanup_efficiency_percent'] < 60
        ]
        
        if high_memory_tests:
            recommendations.append(
                f"⚠️ {len(high_memory_tests)} test(s) used >80% of memory limit. "
                "Consider reducing batch sizes or using MEMORY_OPTIMIZED mode."
            )
        
        if poor_cleanup_tests:
            recommendations.append(
                f"⚠️ {len(poor_cleanup_tests)} test(s) had poor memory cleanup. "
                "Enable more aggressive garbage collection or reduce gc_threshold_mb."
            )
        
        # Performance mode recommendations
        memory_optimized_tests = [
            test for test in successful_tests
            if test['configuration'].get('performance_mode') == PerformanceMode.MEMORY_OPTIMIZED
        ]
        
        if memory_optimized_tests:
            avg_efficiency = sum(
                test['memory_metrics']['cleanup_efficiency_percent'] 
                for test in memory_optimized_tests
            ) / len(memory_optimized_tests)
            
            if avg_efficiency > 70:
                recommendations.append("✅ MEMORY_OPTIMIZED mode shows good results - recommended for memory-constrained environments")
        
        return recommendations
    
    async def _save_memory_results(self, report: Dict):
        """Save memory validation results with visualizations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = self.output_dir / f"memory_validation_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate memory usage plots
        await self._generate_memory_plots(timestamp)
        
        # Save summary report
        summary_file = self.output_dir / f"memory_validation_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("MEMORY OPTIMIZATION VALIDATION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            validation = report['validation_summary']
            f.write(f"Total Tests: {validation['total_tests']}\n")
            f.write(f"Successful Tests: {validation['successful_tests']}\n")
            f.write(f"Within Memory Limits: {validation['tests_within_memory_limits']}\n")
            f.write(f"Efficient Memory Usage: {validation['tests_with_efficient_usage']}\n")
            f.write(f"Good Cleanup Efficiency: {validation['tests_with_good_cleanup']}\n\n")
            
            if 'overall_statistics' in report and report['overall_statistics']:
                stats = report['overall_statistics']
                f.write("MEMORY STATISTICS:\n")
                f.write(f"Average Peak Memory: {stats['avg_peak_memory_mb']:.1f} MB\n")
                f.write(f"Maximum Peak Memory: {stats['max_peak_memory_mb']:.1f} MB\n")
                f.write(f"Average Memory Growth: {stats['avg_memory_growth_mb']:.1f} MB\n")
                f.write(f"Average Cleanup Efficiency: {stats['avg_cleanup_efficiency_percent']:.1f}%\n\n")
            
            f.write("OPTIMIZATION EFFECTIVENESS:\n")
            effectiveness = report['optimization_effectiveness']
            if effectiveness:
                f.write(f"Memory per Item: {effectiveness['avg_memory_per_item_mb']:.2f} MB/item\n")
                f.write(f"GC Effectiveness: {effectiveness['avg_gc_effectiveness_percent']:.1f}%\n")
                f.write(f"Optimization Score: {effectiveness['memory_optimization_score']:.1f}/100\n\n")
            
            f.write("RECOMMENDATIONS:\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")
        
        logger.info(f"Memory validation results saved to {json_file} and {summary_file}")
    
    async def _generate_memory_plots(self, timestamp: str):
        """Generate memory usage visualization plots"""
        try:
            # Memory timeline plot for each test
            for test_name, test_data in self.test_results.items():
                if not test_data.get('success', False):
                    continue
                
                timeline = test_data.get('memory_timeline', [])
                if not timeline:
                    continue
                
                # Extract data
                times = [snap['timestamp'] - timeline[0]['timestamp'] for snap in timeline]
                rss_values = [snap['rss_mb'] for snap in timeline]
                tracemalloc_values = [snap['tracemalloc_current_mb'] for snap in timeline]
                
                # Create plot
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
                
                # RSS memory plot
                ax1.plot(times, rss_values, 'b-', label='RSS Memory', linewidth=2)
                ax1.set_xlabel('Time (seconds)')
                ax1.set_ylabel('Memory (MB)')
                ax1.set_title(f'Memory Usage Timeline - {test_name} (RSS)')
                ax1.grid(True, alpha=0.3)
                ax1.legend()
                
                # Tracemalloc plot
                ax2.plot(times, tracemalloc_values, 'r-', label='Tracemalloc Memory', linewidth=2)
                ax2.set_xlabel('Time (seconds)')
                ax2.set_ylabel('Memory (MB)')
                ax2.set_title(f'Memory Usage Timeline - {test_name} (Tracemalloc)')
                ax2.grid(True, alpha=0.3)
                ax2.legend()
                
                plt.tight_layout()
                plot_file = self.output_dir / f"memory_timeline_{test_name}_{timestamp}.png"
                plt.savefig(plot_file, dpi=150, bbox_inches='tight')
                plt.close()
                
                logger.info(f"Memory plot saved to {plot_file}")
        
        except Exception as e:
            logger.warning(f"Failed to generate memory plots: {e}")


class MockPageForMemoryTest:
    """Memory-optimized mock page for testing"""
    
    def __init__(self, item_count: int):
        self.item_count = item_count
        
    async def query_selector_all(self, selector: str):
        await asyncio.sleep(0.01)
        if 'thumbnail' in selector:
            return [MockElementForMemoryTest(i) for i in range(min(self.item_count, 10))]
        return []
    
    async def evaluate(self, script: str, *args):
        await asyncio.sleep(0.02)
        return {'url': 'https://test.com/download.mp4', 'creationTime': '2024-01-01', 'prompt': 'test'}


class MockElementForMemoryTest:
    """Lightweight mock element for memory testing"""
    
    def __init__(self, item_id: int):
        self.item_id = item_id
    
    async def click(self, **kwargs):
        await asyncio.sleep(0.05)
    
    async def get_attribute(self, name: str):
        return f"attr_{self.item_id}"
    
    async def bounding_box(self):
        return {'x': 0, 'y': 0, 'width': 100, 'height': 100}
    
    async def evaluate(self, script: str):
        return f"hash_{self.item_id}"


class MockDownloadManagerForMemoryTest:
    """Lightweight mock download manager"""
    
    async def download_file_streaming(self, url: str, filename: str, config):
        await asyncio.sleep(0.1)  # Simulate download
        return True, f"/tmp/{filename}", ""


async def main():
    """Main memory validation execution"""
    print("🧠 Starting Memory Optimization Validation")
    print("=" * 60)
    
    validator = MemoryOptimizationValidator()
    
    try:
        report = await validator.run_memory_validation_suite()
        
        # Print results summary
        print("\n" + "=" * 60)
        print("📊 MEMORY VALIDATION RESULTS")
        print("=" * 60)
        
        validation = report['validation_summary']
        print(f"✅ Successful Tests: {validation['successful_tests']}/{validation['total_tests']}")
        print(f"🎯 Within Memory Limits: {validation['tests_within_memory_limits']}")
        print(f"⚡ Efficient Memory Usage: {validation['tests_with_efficient_usage']}")
        print(f"🧹 Good Cleanup: {validation['tests_with_good_cleanup']}")
        
        if 'overall_statistics' in report and report['overall_statistics']:
            stats = report['overall_statistics']
            print(f"\n📈 MEMORY STATISTICS:")
            print(f"  Average Peak: {stats['avg_peak_memory_mb']:.1f} MB")
            print(f"  Maximum Peak: {stats['max_peak_memory_mb']:.1f} MB")
            print(f"  Average Growth: {stats['avg_memory_growth_mb']:.1f} MB")
            print(f"  Cleanup Efficiency: {stats['avg_cleanup_efficiency_percent']:.1f}%")
        
        effectiveness = report.get('optimization_effectiveness', {})
        if effectiveness:
            print(f"\n🎯 OPTIMIZATION EFFECTIVENESS:")
            print(f"  Memory per Item: {effectiveness['avg_memory_per_item_mb']:.2f} MB/item")
            print(f"  Optimization Score: {effectiveness['memory_optimization_score']:.1f}/100")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print("\n✅ Memory validation completed successfully!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Memory validation failed: {e}")
        logger.exception("Memory validation execution failed")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))