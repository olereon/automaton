#!/usr/bin/env python3.11
"""
Simplified Workflow Integration Test

This test validates the complete simplified container-based workflow from container detection
through metadata extraction to final output processing. It demonstrates the integration
of all simplified components working together.

Integration Components:
- Simplified container detection
- Fast metadata extraction
- Error handling and recovery
- Batch processing capabilities
- Performance monitoring

Workflow Steps Tested:
1. Container Discovery: Finding and identifying containers
2. Content Extraction: Getting text content from containers
3. Metadata Processing: Extracting creation time and prompt
4. Quality Validation: Ensuring extracted data meets standards
5. Error Recovery: Handling failures gracefully
6. Batch Coordination: Processing multiple containers efficiently
"""

import pytest
import asyncio
import time
import tempfile
import json
import os
from unittest.mock import AsyncMock, Mock, patch
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import modules to test
from src.utils.simplified_container_extractor import (
    SimplifiedContainerExtractor,
    SimplifiedExtractionConfig,
    create_optimized_extractor,
    create_debug_extractor
)


class MockContainerDetector:
    """Mock container detector for testing workflow integration"""
    
    def __init__(self):
        self.container_data = []
        self.detection_delay = 0.1  # Simulate realistic detection time
    
    async def discover_containers(self, page) -> List[Dict[str, Any]]:
        """Simulate container discovery process"""
        
        await asyncio.sleep(self.detection_delay)
        
        # Return mock container data
        containers = []
        for i, data in enumerate(self.container_data):
            containers.append({
                'id': f'container_{i}',
                'element': self._create_mock_element(data['content']),
                'content': data['content'],
                'metadata': data.get('metadata', {})
            })
        
        return containers
    
    def _create_mock_element(self, content: str):
        """Create mock DOM element"""
        mock_element = AsyncMock()
        mock_element.text_content.return_value = content
        mock_element.get_attribute.return_value = "container"
        return mock_element
    
    def add_container(self, content: str, metadata: Optional[Dict] = None):
        """Add container data for testing"""
        self.container_data.append({
            'content': content,
            'metadata': metadata or {}
        })
    
    def clear_containers(self):
        """Clear all container data"""
        self.container_data.clear()


class SimplifiedWorkflowOrchestrator:
    """Orchestrates the simplified container-based extraction workflow"""
    
    def __init__(self, extractor: SimplifiedContainerExtractor = None, detector: MockContainerDetector = None):
        self.extractor = extractor or create_optimized_extractor()
        self.detector = detector or MockContainerDetector()
        self.metrics = {
            'containers_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_processing_time': 0,
            'discovery_time': 0,
            'extraction_time': 0
        }
    
    async def run_workflow(self, page, max_containers: int = 50) -> Dict[str, Any]:
        """Run the complete simplified extraction workflow"""
        
        workflow_start = time.perf_counter()
        results = []
        
        try:
            # Step 1: Container Discovery
            discovery_start = time.perf_counter()
            containers = await self.detector.discover_containers(page)
            discovery_end = time.perf_counter()
            
            self.metrics['discovery_time'] = discovery_end - discovery_start
            
            # Limit containers if specified
            if max_containers:
                containers = containers[:max_containers]
            
            # Step 2: Batch Metadata Extraction
            extraction_start = time.perf_counter()
            
            for container in containers:
                container_result = await self._process_single_container(container)
                results.append(container_result)
            
            extraction_end = time.perf_counter()
            self.metrics['extraction_time'] = extraction_end - extraction_start
            
            # Step 3: Results Compilation
            successful_results = [r for r in results if r['success']]
            failed_results = [r for r in results if not r['success']]
            
            self.metrics['containers_processed'] = len(containers)
            self.metrics['successful_extractions'] = len(successful_results)
            self.metrics['failed_extractions'] = len(failed_results)
            self.metrics['total_processing_time'] = time.perf_counter() - workflow_start
            
            workflow_result = {
                'success': True,
                'results': results,
                'successful_results': successful_results,
                'failed_results': failed_results,
                'metrics': self.metrics.copy(),
                'summary': {
                    'containers_processed': len(containers),
                    'success_rate': len(successful_results) / len(containers) if containers else 0,
                    'avg_processing_time': self.metrics['extraction_time'] / len(containers) if containers else 0,
                    'total_workflow_time': self.metrics['total_processing_time']
                }
            }
            
            return workflow_result
            
        except Exception as e:
            workflow_end = time.perf_counter()
            
            return {
                'success': False,
                'error': str(e),
                'metrics': self.metrics.copy(),
                'partial_results': results,
                'workflow_time': workflow_end - workflow_start
            }
    
    async def _process_single_container(self, container: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single container through the extraction pipeline"""
        
        container_start = time.perf_counter()
        
        try:
            # Extract content from container
            content = container['content']
            
            # Run metadata extraction
            extraction_result = self.extractor.extract_metadata(content)
            
            container_end = time.perf_counter()
            processing_time = container_end - container_start
            
            if extraction_result:
                return {
                    'success': True,
                    'container_id': container['id'],
                    'creation_time': extraction_result['creation_time'],
                    'prompt': extraction_result['prompt'],
                    'processing_time': processing_time,
                    'content_length': len(content),
                    'original_content': content[:100] + "..." if len(content) > 100 else content
                }
            else:
                return {
                    'success': False,
                    'container_id': container['id'],
                    'error': 'Extraction failed',
                    'processing_time': processing_time,
                    'content_length': len(content),
                    'original_content': content[:100] + "..." if len(content) > 100 else content
                }
                
        except Exception as e:
            container_end = time.perf_counter()
            
            return {
                'success': False,
                'container_id': container.get('id', 'unknown'),
                'error': str(e),
                'processing_time': container_end - container_start,
                'content_length': len(container.get('content', '')),
                'exception_type': type(e).__name__
            }


class TestSimplifiedWorkflowIntegration:
    """Integration tests for the complete simplified workflow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = create_optimized_extractor()
        self.detector = MockContainerDetector()
        self.orchestrator = SimplifiedWorkflowOrchestrator(self.extractor, self.detector)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_workflow_success_scenario(self):
        """Test complete workflow with successful container processing"""
        
        # Set up test containers with valid data
        test_containers = [
            'Creation Time 25 Aug 2025 02:30:47\nThe camera captures a bustling marketplace with vendors and customers.',
            'Creation Time 24 Aug 2025 15:22:33\nA serene lake surrounded by mountains and forest.',
            'Creation Time 23 Aug 2025 09:15:00\nUrban street photography with dynamic lighting and shadows.',
            'Creation Time 22 Aug 2025 20:45:12\nNight scene showing city lights and reflections.'
        ]
        
        for container_content in test_containers:
            self.detector.add_container(container_content)
        
        # Run workflow
        mock_page = AsyncMock()
        result = await self.orchestrator.run_workflow(mock_page)
        
        # Validate workflow success
        assert result['success'] is True, "Workflow should complete successfully"
        
        # Validate results
        summary = result['summary']
        assert summary['containers_processed'] == len(test_containers), f"Should process all {len(test_containers)} containers"
        assert summary['success_rate'] >= 0.95, f"Success rate should be ≥95%, got {summary['success_rate']:.2%}"
        assert summary['avg_processing_time'] < 0.1, f"Average processing time should be <100ms, got {summary['avg_processing_time']*1000:.1f}ms"
        
        # Validate successful extractions
        successful_results = result['successful_results']
        assert len(successful_results) >= 3, f"Should have at least 3 successful extractions, got {len(successful_results)}"
        
        for success_result in successful_results:
            assert 'creation_time' in success_result, "Should have creation_time"
            assert 'prompt' in success_result, "Should have prompt"
            assert len(success_result['prompt']) > 10, "Prompt should have substantial content"
        
        print(f"✅ Complete workflow success test passed:")
        print(f"   Containers processed: {summary['containers_processed']}")
        print(f"   Success rate: {summary['success_rate']:.2%}")
        print(f"   Average processing time: {summary['avg_processing_time']*1000:.1f}ms")
        print(f"   Total workflow time: {summary['total_workflow_time']:.3f}s")
    
    @pytest.mark.asyncio
    async def test_workflow_with_mixed_container_types(self):
        """Test workflow with mix of valid, invalid, and edge case containers"""
        
        # Set up mixed test containers
        mixed_containers = [
            # Valid containers
            'Creation Time 25 Aug 2025 02:30:47\nSuccessful extraction test with detailed prompt content.',
            'Creation Time 24 Aug 2025 15:22:33\nAnother valid container with proper metadata.',
            
            # Invalid containers
            'Invalid container without proper creation time format.',
            '',  # Empty container
            'Creation Time\nMalformed time data without proper format.',
            
            # Edge cases
            'Creation Time 23 Aug 2025 09:15:00\nShort prompt.',  # Minimal valid content
            'Creation Time 22 Aug 2025 20:45:12\n' + 'Very long prompt content. ' * 50,  # Very long prompt
        ]
        
        for container_content in mixed_containers:
            self.detector.add_container(container_content)
        
        # Run workflow
        mock_page = AsyncMock()
        result = await self.orchestrator.run_workflow(mock_page)
        
        # Validate workflow handles mixed types gracefully
        assert result['success'] is True, "Workflow should handle mixed containers successfully"
        
        summary = result['summary']
        successful_results = result['successful_results']
        failed_results = result['failed_results']
        
        # Should have some successes and some failures
        assert len(successful_results) >= 3, f"Should have at least 3 successful extractions, got {len(successful_results)}"
        assert len(failed_results) >= 2, f"Should have at least 2 failed extractions, got {len(failed_results)}"
        
        # Overall success rate should be reasonable
        success_rate = len(successful_results) / len(mixed_containers)
        assert 0.4 <= success_rate <= 0.8, f"Success rate should be 40-80% for mixed data, got {success_rate:.2%}"
        
        # Validate error handling
        for failed_result in failed_results:
            assert 'error' in failed_result, "Failed results should have error information"
            assert 'processing_time' in failed_result, "Should track processing time even for failures"
        
        print(f"✅ Mixed container types test passed:")
        print(f"   Successful extractions: {len(successful_results)}")
        print(f"   Failed extractions: {len(failed_results)}")
        print(f"   Success rate: {success_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_workflow_performance_under_load(self):
        """Test workflow performance with larger number of containers"""
        
        # Generate larger test dataset
        container_count = 100
        
        for i in range(container_count):
            if i % 4 == 0:  # 25% invalid containers
                content = f"Invalid container {i} without proper format."
            else:  # 75% valid containers
                content = f"Creation Time {20 + (i % 10)} Aug 2025 {10 + (i % 12):02d}:{15 + (i % 45):02d}:{(i % 60):02d}\nTest prompt {i}: Various scenes and descriptions for load testing."
            
            self.detector.add_container(content)
        
        # Run workflow with performance monitoring
        mock_page = AsyncMock()
        
        start_time = time.perf_counter()
        result = await self.orchestrator.run_workflow(mock_page)
        end_time = time.perf_counter()
        
        total_workflow_time = end_time - start_time
        
        # Validate performance under load
        assert result['success'] is True, "Workflow should handle large loads successfully"
        
        summary = result['summary']
        
        # Performance validations
        assert summary['total_workflow_time'] < 5.0, f"Total workflow time should be <5s, got {summary['total_workflow_time']:.3f}s"
        assert summary['avg_processing_time'] < 0.05, f"Average processing time should be <50ms, got {summary['avg_processing_time']*1000:.1f}ms"
        
        # Quality validations
        success_rate = summary['success_rate']
        assert success_rate >= 0.7, f"Success rate should be ≥70% under load, got {success_rate:.2%}"
        
        # Throughput calculation
        throughput = summary['containers_processed'] / summary['total_workflow_time']
        assert throughput >= 20, f"Should process ≥20 containers/second, got {throughput:.1f}/s"
        
        print(f"✅ Performance under load test passed:")
        print(f"   Containers processed: {summary['containers_processed']}")
        print(f"   Total workflow time: {summary['total_workflow_time']:.3f}s")
        print(f"   Throughput: {throughput:.1f} containers/second")
        print(f"   Success rate: {success_rate:.2%}")
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self):
        """Test workflow error recovery and resilience"""
        
        # Set up containers that will cause various types of errors
        problematic_containers = [
            'Creation Time 25 Aug 2025 02:30:47\nValid container before errors.',
            None,  # Will cause exception in container processing
            'Creation Time 24 Aug 2025 15:22:33\nAnother valid container.',
            '',  # Empty container
            'Creation Time 23 Aug 2025 09:15:00\nValid container after errors.'
        ]
        
        # Add containers, handling None case
        for i, container_content in enumerate(problematic_containers):
            if container_content is None:
                # Add a container that will cause processing error
                self.detector.add_container("This will cause an error")
                # Patch the extractor to raise an exception for this specific content
                original_extract = self.extractor.extract_metadata
                def error_extract(content):
                    if "cause an error" in content:
                        raise ValueError("Simulated processing error")
                    return original_extract(content)
                self.extractor.extract_metadata = error_extract
            else:
                self.detector.add_container(container_content)
        
        # Run workflow
        mock_page = AsyncMock()
        result = await self.orchestrator.run_workflow(mock_page)
        
        # Workflow should still succeed overall despite errors
        assert result['success'] is True, "Workflow should recover from individual container errors"
        
        successful_results = result['successful_results']
        failed_results = result['failed_results']
        
        # Should have some successes despite errors
        assert len(successful_results) >= 3, f"Should have successful extractions despite errors, got {len(successful_results)}"
        assert len(failed_results) >= 1, f"Should have some failed extractions, got {len(failed_results)}"
        
        # Validate error information is captured
        for failed_result in failed_results:
            assert 'error' in failed_result or 'exception_type' in failed_result, "Failed results should have error details"
        
        print(f"✅ Error recovery test passed:")
        print(f"   Successful recoveries: {len(successful_results)}")
        print(f"   Handled errors: {len(failed_results)}")
    
    @pytest.mark.asyncio
    async def test_workflow_metrics_and_monitoring(self):
        """Test workflow metrics collection and monitoring capabilities"""
        
        # Set up test containers
        test_containers = [
            'Creation Time 25 Aug 2025 02:30:47\nDetailed monitoring test prompt with comprehensive content.',
            'Creation Time 24 Aug 2025 15:22:33\nAnother test container for metrics validation.',
            'Invalid container for metrics testing.',
            'Creation Time 23 Aug 2025 09:15:00\nFinal valid container for completeness.'
        ]
        
        for container_content in test_containers:
            self.detector.add_container(container_content)
        
        # Run workflow
        mock_page = AsyncMock()
        result = await self.orchestrator.run_workflow(mock_page)
        
        # Validate metrics collection
        metrics = result['metrics']
        
        # Check all expected metrics are present
        expected_metrics = [
            'containers_processed', 'successful_extractions', 'failed_extractions',
            'total_processing_time', 'discovery_time', 'extraction_time'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics, f"Metric '{metric}' should be present"
            assert isinstance(metrics[metric], (int, float)), f"Metric '{metric}' should be numeric"
        
        # Validate metric relationships
        assert metrics['containers_processed'] == len(test_containers), "Containers processed metric should match input"
        assert metrics['successful_extractions'] + metrics['failed_extractions'] == metrics['containers_processed'], "Success + failure should equal total"
        assert metrics['total_processing_time'] > 0, "Total processing time should be positive"
        assert metrics['discovery_time'] >= 0, "Discovery time should be non-negative"
        assert metrics['extraction_time'] >= 0, "Extraction time should be non-negative"
        
        # Validate summary metrics
        summary = result['summary']
        assert 'success_rate' in summary, "Summary should include success rate"
        assert 'avg_processing_time' in summary, "Summary should include average processing time"
        assert 'total_workflow_time' in summary, "Summary should include total workflow time"
        
        print(f"✅ Metrics and monitoring test passed:")
        print(f"   Metrics collected: {len(metrics)} metrics")
        print(f"   Discovery time: {metrics['discovery_time']*1000:.1f}ms")
        print(f"   Extraction time: {metrics['extraction_time']*1000:.1f}ms")
        print(f"   Total workflow time: {metrics['total_processing_time']:.3f}s")
    
    @pytest.mark.asyncio
    async def test_workflow_output_persistence(self):
        """Test workflow result persistence and file output"""
        
        # Set up test containers
        test_containers = [
            'Creation Time 25 Aug 2025 02:30:47\nPersistence test with detailed content for file output validation.',
            'Creation Time 24 Aug 2025 15:22:33\nSecond container for persistence testing.'
        ]
        
        for container_content in test_containers:
            self.detector.add_container(container_content)
        
        # Run workflow
        mock_page = AsyncMock()
        result = await self.orchestrator.run_workflow(mock_page)
        
        # Test result persistence
        results_file = os.path.join(self.temp_dir, "workflow_results.json")
        metrics_file = os.path.join(self.temp_dir, "workflow_metrics.json")
        
        # Save results to files
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        with open(metrics_file, 'w') as f:
            json.dump(result['metrics'], f, indent=2)
        
        # Validate files were created and are readable
        assert os.path.exists(results_file), "Results file should be created"
        assert os.path.exists(metrics_file), "Metrics file should be created"
        
        # Validate file contents
        with open(results_file, 'r') as f:
            loaded_results = json.load(f)
            
        assert loaded_results['success'] == result['success'], "Loaded results should match original"
        assert len(loaded_results['results']) == len(result['results']), "Result count should match"
        
        with open(metrics_file, 'r') as f:
            loaded_metrics = json.load(f)
            
        assert loaded_metrics['containers_processed'] == result['metrics']['containers_processed'], "Metrics should match"
        
        # Test file size is reasonable
        results_size = os.path.getsize(results_file)
        metrics_size = os.path.getsize(metrics_file)
        
        assert results_size > 100, "Results file should have substantial content"
        assert metrics_size > 50, "Metrics file should have content"
        assert results_size < 1024 * 1024, "Results file should not be excessively large"  # <1MB
        
        print(f"✅ Output persistence test passed:")
        print(f"   Results file: {results_size} bytes")
        print(f"   Metrics file: {metrics_size} bytes")
        print(f"   Files saved to: {self.temp_dir}")
    
    def test_workflow_configuration_validation(self):
        """Test workflow configuration and setup validation"""
        
        # Test with custom extractor configuration
        custom_config = SimplifiedExtractionConfig(
            max_processing_time_ms=25,
            enable_debug_logging=True,
            strict_time_validation=True,
            min_prompt_length=10,
            max_prompt_length=500
        )
        
        custom_extractor = SimplifiedContainerExtractor(custom_config)
        custom_orchestrator = SimplifiedWorkflowOrchestrator(custom_extractor, self.detector)
        
        # Validate configuration is applied
        assert custom_orchestrator.extractor.config.max_processing_time_ms == 25, "Custom config should be applied"
        assert custom_orchestrator.extractor.config.enable_debug_logging is True, "Debug logging should be enabled"
        
        # Test extractor performance stats
        perf_stats = custom_orchestrator.extractor.get_performance_stats()
        
        assert 'config' in perf_stats, "Performance stats should include config"
        assert 'pattern_count' in perf_stats, "Performance stats should include pattern count"
        
        config_stats = perf_stats['config']
        assert config_stats['max_processing_time_ms'] == 25, "Config stats should reflect custom settings"
        assert config_stats['strict_time_validation'] is True, "Config stats should be accurate"
        
        print(f"✅ Configuration validation test passed:")
        print(f"   Custom config applied: {custom_config.max_processing_time_ms}ms timeout")
        print(f"   Pattern count: {perf_stats['pattern_count']}")


def run_simplified_workflow_integration_tests():
    """Run the complete simplified workflow integration test suite"""
    print("🚀 Simplified Workflow Integration Test Suite")
    print("=" * 70)
    
    # Test classes to run
    test_class = TestSimplifiedWorkflowIntegration
    test_instance = test_class()
    
    # Get test methods
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    test_results = {}
    
    for test_method_name in test_methods:
        print(f"\n📋 Running {test_method_name}")
        print("-" * 50)
        
        try:
            # Set up test
            test_instance.setup_method()
            
            # Run test
            test_method = getattr(test_instance, test_method_name)
            
            if asyncio.iscoroutinefunction(test_method):
                # Run async test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(test_method())
                finally:
                    loop.close()
            else:
                # Run sync test
                test_method()
            
            passed += 1
            test_results[test_method_name] = 'PASSED'
            
        except Exception as e:
            print(f"❌ {test_method_name}: {e}")
            failed += 1
            test_results[test_method_name] = f'FAILED: {e}'
            
        finally:
            # Clean up test
            try:
                test_instance.teardown_method()
            except:
                pass
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"🎯 Integration Test Results: {passed} passed, {failed} failed")
    
    success_rate = passed / (passed + failed) if (passed + failed) > 0 else 0
    
    if success_rate >= 0.95:
        print(f"🎉 Integration tests PASSED with {success_rate:.2%} success rate!")
        print("✅ Simplified workflow is ready for production deployment!")
    else:
        print(f"⚠️ Integration tests need improvement: {success_rate:.2%} success rate")
        print("❌ Please review failed tests before deploying.")
    
    return success_rate >= 0.95, test_results


if __name__ == "__main__":
    # Run integration tests
    success, results = run_simplified_workflow_integration_tests()
    
    # Save results
    results_file = "/home/olereon/workspace/github.com/olereon/automaton/tests/reports/simplified_workflow_integration_results.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            'success': success,
            'test_results': results,
            'timestamp': time.time()
        }, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    
    exit(0 if success else 1)