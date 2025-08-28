#!/usr/bin/env python3
"""
Production Performance Test
Real-world performance validation for the optimized generation download system.
Tests with actual browser automation and production-like scenarios.
"""

import asyncio
import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from playwright.async_api import async_playwright
from utils.performance_optimized_generation_download_manager import (
    PerformanceOptimizedGenerationDownloadManager,
    OptimizedGenerationDownloadConfig,
    PerformanceMode
)
from utils.download_manager import DownloadManager, DownloadConfig
from utils.performance_monitor import PerformanceMonitor, get_monitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProductionPerformanceTest:
    """Production-grade performance test with real browser automation"""
    
    def __init__(self, test_url: str = None, output_dir: str = "./production_test_results"):
        self.test_url = test_url or "https://example.com"  # Replace with actual test URL
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.monitor = get_monitor()
        self.test_results = {}
        
    async def run_production_test(self) -> Dict:
        """Run comprehensive production test suite"""
        logger.info("Starting production performance test")
        
        # Start performance monitoring
        await self.monitor.start_monitoring()
        
        try:
            async with async_playwright() as p:
                # Test different browser configurations
                test_scenarios = [
                    {
                        'name': 'chrome_headless_optimized',
                        'browser': 'chromium',
                        'headless': True,
                        'performance_mode': PerformanceMode.PRODUCTION,
                        'batch_size': 10,
                        'max_downloads': 50
                    },
                    {
                        'name': 'chrome_headed_balanced',
                        'browser': 'chromium', 
                        'headless': False,
                        'performance_mode': PerformanceMode.BALANCED,
                        'batch_size': 8,
                        'max_downloads': 30
                    },
                    {
                        'name': 'firefox_headless_memory_optimized',
                        'browser': 'firefox',
                        'headless': True,
                        'performance_mode': PerformanceMode.MEMORY_OPTIMIZED,
                        'batch_size': 5,
                        'max_downloads': 25
                    }
                ]
                
                for scenario in test_scenarios:
                    logger.info(f"Running scenario: {scenario['name']}")
                    
                    result = await self._run_scenario(p, scenario)
                    self.test_results[scenario['name']] = result
                    
                    # Cool down between scenarios
                    await asyncio.sleep(10)
            
            # Generate final report
            report = self._generate_production_report()
            await self._save_production_results(report)
            
            return report
            
        finally:
            await self.monitor.stop_monitoring()
    
    async def _run_scenario(self, playwright, scenario: Dict) -> Dict:
        """Run individual test scenario"""
        start_time = time.time()
        
        # Browser setup
        browser_type = getattr(playwright, scenario['browser'])
        browser = await browser_type.launch(
            headless=scenario['headless'],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu'
            ] if scenario['headless'] else []
        )
        
        try:
            # Create page with performance optimizations
            page = await browser.new_page()
            
            # Performance optimizations
            await page.route('**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}', self._block_resources)
            
            # Configure optimized manager
            config = OptimizedGenerationDownloadConfig(
                max_downloads=scenario['max_downloads'],
                batch_size=scenario['batch_size'],
                performance_mode=scenario['performance_mode'],
                memory_limit_mb=400,
                max_concurrent_workers=6,
                downloads_folder=str(self.output_dir / "downloads" / scenario['name'])
            )
            
            manager = PerformanceOptimizedGenerationDownloadManager(config)
            
            # Setup download manager
            download_config = DownloadConfig(
                download_dir=str(self.output_dir / "downloads" / scenario['name']),
                timeout=120
            )
            download_manager = DownloadManager(download_config)
            
            # Navigate to test page (if using real URL)
            if self.test_url != "https://example.com":
                logger.info(f"Navigating to {self.test_url}")
                await page.goto(self.test_url, timeout=60000)
                await page.wait_for_load_state('networkidle')
            else:
                # Create mock test page
                await self._setup_mock_test_page(page)
            
            # Track performance metrics
            performance_start = await self._capture_performance_snapshot()
            
            # Run the optimized download process
            progress_data = []
            
            async def progress_callback(progress_info):
                progress_data.append({
                    'timestamp': time.time(),
                    'processed': progress_info.get('processed', 0),
                    'performance_metrics': progress_info.get('performance_metrics', {})
                })
            
            result = await manager.process_generation_downloads_optimized(
                page, download_manager, progress_callback
            )
            
            # Capture final performance metrics
            performance_end = await self._capture_performance_snapshot()
            
            # Calculate scenario results
            duration = time.time() - start_time
            
            scenario_result = {
                'scenario_name': scenario['name'],
                'success': result.get('success', False),
                'duration_seconds': duration,
                'processed_count': result.get('processed_count', 0),
                'throughput_items_per_second': result.get('processed_count', 0) / duration if duration > 0 else 0,
                'download_stats': result.get('download_stats', {}),
                'performance_metrics': result.get('performance_metrics', {}),
                'cache_stats': result.get('cache_stats', {}),
                'performance_snapshots': {
                    'start': performance_start,
                    'end': performance_end
                },
                'progress_data': progress_data,
                'browser_info': {
                    'browser': scenario['browser'],
                    'headless': scenario['headless'],
                    'version': await self._get_browser_version(browser)
                },
                'configuration': scenario
            }
            
            logger.info(
                f"Scenario {scenario['name']} completed: "
                f"{scenario_result['processed_count']} items in {duration:.1f}s "
                f"({scenario_result['throughput_items_per_second']:.2f} items/sec)"
            )
            
            return scenario_result
            
        except Exception as e:
            logger.error(f"Scenario {scenario['name']} failed: {e}")
            return {
                'scenario_name': scenario['name'],
                'success': False,
                'error': str(e),
                'duration_seconds': time.time() - start_time,
                'processed_count': 0
            }
        
        finally:
            await browser.close()
    
    async def _block_resources(self, route):
        """Block unnecessary resources to improve performance"""
        if route.request.resource_type in ['image', 'stylesheet', 'font']:
            await route.abort()
        else:
            await route.continue_()
    
    async def _setup_mock_test_page(self, page):
        """Setup mock test page for testing without real URL"""
        mock_html = """
        <html>
        <head><title>Mock Test Page</title></head>
        <body>
            <div class="thumsInner">
                <div class="thumsItem" data-spm-anchor-id="item-1">Item 1</div>
                <div class="thumsItem" data-spm-anchor-id="item-2">Item 2</div>
                <div class="thumsItem" data-spm-anchor-id="item-3">Item 3</div>
                <div class="thumsItem" data-spm-anchor-id="item-4">Item 4</div>
                <div class="thumsItem" data-spm-anchor-id="item-5">Item 5</div>
            </div>
            <div id="download-area">
                <a href="/download/test.mp4">Download</a>
                <div class="creation-time">2024-01-01 12:00:00</div>
                <div class="prompt">Test prompt content</div>
            </div>
        </body>
        </html>
        """
        
        await page.set_content(mock_html)
        logger.info("Mock test page setup completed")
    
    async def _capture_performance_snapshot(self) -> Dict:
        """Capture current performance snapshot"""
        try:
            return self.monitor.get_performance_report(window_seconds=60)
        except Exception as e:
            logger.error(f"Failed to capture performance snapshot: {e}")
            return {}
    
    async def _get_browser_version(self, browser) -> str:
        """Get browser version information"""
        try:
            return browser.version
        except Exception:
            return "unknown"
    
    def _generate_production_report(self) -> Dict:
        """Generate comprehensive production test report"""
        successful_tests = [r for r in self.test_results.values() if r.get('success', False)]
        failed_tests = [r for r in self.test_results.values() if not r.get('success', False)]
        
        # Calculate overall statistics
        total_processed = sum(r.get('processed_count', 0) for r in successful_tests)
        total_duration = sum(r.get('duration_seconds', 0) for r in successful_tests)
        
        # Best performing scenario
        best_scenario = None
        if successful_tests:
            best_scenario = max(successful_tests, key=lambda x: x.get('throughput_items_per_second', 0))
        
        report = {
            'production_test_suite': 'Optimized Generation Download System',
            'timestamp': datetime.now().isoformat(),
            'test_summary': {
                'total_scenarios': len(self.test_results),
                'successful_scenarios': len(successful_tests),
                'failed_scenarios': len(failed_tests),
                'success_rate_percent': (len(successful_tests) / len(self.test_results)) * 100 if self.test_results else 0
            },
            'performance_summary': {
                'total_items_processed': total_processed,
                'total_processing_time_seconds': total_duration,
                'average_throughput_items_per_second': total_processed / total_duration if total_duration > 0 else 0,
                'best_performing_scenario': best_scenario.get('scenario_name') if best_scenario else None,
                'best_throughput_items_per_second': best_scenario.get('throughput_items_per_second', 0) if best_scenario else 0
            },
            'detailed_results': self.test_results,
            'recommendations': self._generate_recommendations(),
            'browser_compatibility': self._analyze_browser_compatibility()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on test results"""
        recommendations = []
        
        successful_tests = [r for r in self.test_results.values() if r.get('success', False)]
        
        if not successful_tests:
            recommendations.append("❌ All test scenarios failed. Check system configuration and browser setup.")
            return recommendations
        
        # Analyze performance patterns
        throughputs = [r.get('throughput_items_per_second', 0) for r in successful_tests]
        avg_throughput = sum(throughputs) / len(throughputs)
        
        if avg_throughput > 0.5:
            recommendations.append("✅ Excellent throughput performance achieved (>0.5 items/sec)")
        elif avg_throughput > 0.3:
            recommendations.append("⚠️ Good throughput performance (0.3-0.5 items/sec)")
        else:
            recommendations.append("⚠️ Consider increasing batch size or worker count for better throughput")
        
        # Memory usage analysis
        memory_usages = []
        for test in successful_tests:
            perf_metrics = test.get('performance_metrics', {})
            if isinstance(perf_metrics, dict) and 'memory_usage_mb' in perf_metrics:
                memory_usages.append(perf_metrics['memory_usage_mb'])
        
        if memory_usages:
            avg_memory = sum(memory_usages) / len(memory_usages)
            if avg_memory < 200:
                recommendations.append("✅ Excellent memory efficiency (<200MB average)")
            elif avg_memory < 400:
                recommendations.append("✅ Good memory usage (200-400MB average)")
            else:
                recommendations.append("⚠️ Consider enabling memory optimization mode for large batches")
        
        # Browser-specific recommendations
        headless_tests = [r for r in successful_tests if r.get('browser_info', {}).get('headless', False)]
        headed_tests = [r for r in successful_tests if not r.get('browser_info', {}).get('headless', True)]
        
        if headless_tests and headed_tests:
            headless_avg = sum(r.get('throughput_items_per_second', 0) for r in headless_tests) / len(headless_tests)
            headed_avg = sum(r.get('throughput_items_per_second', 0) for r in headed_tests) / len(headed_tests)
            
            if headless_avg > headed_avg * 1.2:
                recommendations.append("💡 Headless mode shows 20%+ better performance - recommended for production")
        
        return recommendations
    
    def _analyze_browser_compatibility(self) -> Dict:
        """Analyze browser compatibility and performance"""
        compatibility = {}
        
        for scenario_name, result in self.test_results.items():
            browser_info = result.get('browser_info', {})
            browser = browser_info.get('browser', 'unknown')
            
            if browser not in compatibility:
                compatibility[browser] = {
                    'tests_run': 0,
                    'tests_successful': 0,
                    'avg_throughput': 0,
                    'best_throughput': 0
                }
            
            compatibility[browser]['tests_run'] += 1
            
            if result.get('success', False):
                compatibility[browser]['tests_successful'] += 1
                throughput = result.get('throughput_items_per_second', 0)
                compatibility[browser]['avg_throughput'] += throughput
                compatibility[browser]['best_throughput'] = max(
                    compatibility[browser]['best_throughput'], throughput
                )
        
        # Calculate final averages
        for browser_stats in compatibility.values():
            if browser_stats['tests_successful'] > 0:
                browser_stats['avg_throughput'] /= browser_stats['tests_successful']
        
        return compatibility
    
    async def _save_production_results(self, report: Dict):
        """Save production test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON report
        json_file = self.output_dir / f"production_test_report_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save summary report
        summary_file = self.output_dir / f"production_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("PRODUCTION PERFORMANCE TEST SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Timestamp: {report['timestamp']}\n")
            f.write(f"Total Scenarios: {report['test_summary']['total_scenarios']}\n")
            f.write(f"Successful: {report['test_summary']['successful_scenarios']}\n")
            f.write(f"Success Rate: {report['test_summary']['success_rate_percent']:.1f}%\n\n")
            
            f.write("PERFORMANCE METRICS:\n")
            f.write(f"Total Items Processed: {report['performance_summary']['total_items_processed']}\n")
            f.write(f"Average Throughput: {report['performance_summary']['average_throughput_items_per_second']:.3f} items/sec\n")
            f.write(f"Best Scenario: {report['performance_summary']['best_performing_scenario']}\n")
            f.write(f"Best Throughput: {report['performance_summary']['best_throughput_items_per_second']:.3f} items/sec\n\n")
            
            f.write("RECOMMENDATIONS:\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")
            
            f.write("\nBROWSER COMPATIBILITY:\n")
            for browser, stats in report['browser_compatibility'].items():
                f.write(f"{browser.upper()}:\n")
                f.write(f"  Success Rate: {stats['tests_successful']}/{stats['tests_run']}\n")
                f.write(f"  Avg Throughput: {stats['avg_throughput']:.3f} items/sec\n")
                f.write(f"  Best Throughput: {stats['best_throughput']:.3f} items/sec\n\n")
        
        logger.info(f"Production test results saved to {json_file} and {summary_file}")


async def main():
    """Main production test execution"""
    print("🏭 Starting Production Performance Test")
    print("=" * 60)
    
    # You can specify a real test URL here
    test_url = os.environ.get('TEST_URL', 'https://example.com')
    
    test = ProductionPerformanceTest(test_url)
    
    try:
        report = await test.run_production_test()
        
        # Print results summary
        print("\n" + "=" * 60)
        print("📊 PRODUCTION TEST RESULTS")
        print("=" * 60)
        
        summary = report['test_summary']
        perf_summary = report['performance_summary']
        
        print(f"✅ Successful Scenarios: {summary['successful_scenarios']}/{summary['total_scenarios']}")
        print(f"📈 Success Rate: {summary['success_rate_percent']:.1f}%")
        print(f"🚀 Total Items Processed: {perf_summary['total_items_processed']}")
        print(f"⚡ Average Throughput: {perf_summary['average_throughput_items_per_second']:.3f} items/sec")
        print(f"🏆 Best Performing: {perf_summary['best_performing_scenario']} ({perf_summary['best_throughput_items_per_second']:.3f} items/sec)")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print("\n🌐 BROWSER COMPATIBILITY:")
        for browser, stats in report['browser_compatibility'].items():
            print(f"  {browser.upper()}: {stats['tests_successful']}/{stats['tests_run']} success, {stats['avg_throughput']:.3f} avg items/sec")
        
        print("\n✅ Production performance test completed successfully!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Production test failed: {e}")
        logger.exception("Production test execution failed")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))