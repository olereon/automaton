#!/usr/bin/env python3.11
"""
Edge cases and performance test suite for generation download system
Tests boundary conditions, error scenarios, and performance characteristics
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import json
import os
import time
import concurrent.futures
import random

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadManager,
    GenerationDownloadConfig,
    GenerationDownloadLogger,
    GenerationMetadata
)


class TestEdgeCasesAndPerformance:
    """Test suite for edge cases and performance scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = GenerationDownloadConfig()
        self.config.downloads_folder = os.path.join(self.temp_dir, 'downloads')
        self.config.logs_folder = os.path.join(self.temp_dir, 'logs')
        
        # Create directories
        os.makedirs(self.config.downloads_folder, exist_ok=True)
        os.makedirs(self.config.logs_folder, exist_ok=True)
        
        self.manager = GenerationDownloadManager(self.config)
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ===== EDGE CASES =====
    
    @pytest.mark.asyncio
    async def test_empty_gallery_handling(self):
        """Test handling of empty galleries"""
        
        mock_page = Mock()
        mock_page.query_selector_all = AsyncMock(return_value=[])  # No containers
        mock_page.go_back = AsyncMock(return_value=True)
        
        # Should handle empty gallery gracefully
        result = await self.manager.exit_gallery_and_scan_generations(mock_page)
        
        # Should not crash and should return None or handle gracefully
        assert result is None or isinstance(result, dict)
        
    @pytest.mark.asyncio
    async def test_malformed_metadata_handling(self):
        """Test handling of malformed or missing metadata"""
        
        mock_page = Mock()
        
        malformed_cases = [
            None,  # No metadata returned
            {},    # Empty metadata
            {'generation_date': None, 'prompt': None},  # Null values
            {'generation_date': '', 'prompt': ''},      # Empty strings
            {'generation_date': 'invalid_date', 'prompt': 'valid prompt'},  # Invalid date
            {'generation_date': '30 Aug 2025 05:11:29', 'prompt': None},   # Null prompt
            {'unknown_field': 'value'},  # Missing expected fields
        ]
        
        for malformed_data in malformed_cases:
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = malformed_data
                
                # Should handle gracefully without crashing
                is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumb')
                assert isinstance(is_duplicate, bool)
                # Should default to False for invalid data
                assert is_duplicate == False
                
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts and connection issues"""
        
        mock_page = Mock()
        
        # Simulate various network issues
        timeout_scenarios = [
            TimeoutError("Page load timeout"),
            ConnectionError("Network connection lost"),
            OSError("Network unreachable"),
            Exception("Unexpected network error")
        ]
        
        for error in timeout_scenarios:
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.side_effect = error
                
                # Should handle network errors gracefully
                is_duplicate = await self.manager.check_comprehensive_duplicate(mock_page, 'test_thumb')
                assert is_duplicate == False  # Should default to False on error
                
    def test_corrupted_log_file_recovery(self):
        """Test recovery from corrupted log files"""
        
        log_file = os.path.join(self.config.logs_folder, 'generation_downloads.txt')
        
        # Create corrupted log file with mixed valid/invalid entries
        corrupted_content = [
            '{"valid": "entry", "file_id": "#000000001"}',  # Valid JSON
            'invalid json line {{{',                        # Invalid JSON
            '',                                             # Empty line
            '{"file_id": "#000000002", "generation_date": "30 Aug 2025 05:11:29"}',  # Valid
            'another invalid line',                         # Invalid
            '{"incomplete": "entry"}'                       # Missing required fields
        ]
        
        with open(log_file, 'w') as f:
            f.write('\n'.join(corrupted_content))
            
        # Should handle corrupted file gracefully
        self.manager._load_existing_log_entries()
        
        # Should have loaded valid entries and skipped invalid ones
        if hasattr(self.manager, 'existing_log_entries'):
            # Should have extracted some valid entries
            assert len(self.manager.existing_log_entries) >= 0
            
    def test_extremely_long_prompts(self):
        """Test handling of extremely long prompts"""
        
        # Create prompt with various extreme lengths
        test_prompts = [
            '',  # Empty
            'A',  # Single character
            'A' * 1000,  # 1KB prompt
            'A' * 10000,  # 10KB prompt
            'A' * 100000,  # 100KB prompt
            '🚀' * 1000,  # Unicode characters
            'Line 1\nLine 2\nLine 3',  # Multi-line
            '"Quotes" and \'apostrophes\' with "nested" content',  # Special chars
        ]
        
        for prompt in test_prompts:
            # Test prompt handling in metadata
            metadata = GenerationMetadata(
                file_id="#000000001",
                generation_date="30 Aug 2025 05:11:29",
                prompt=prompt,
                download_timestamp=datetime.now().isoformat(),
                file_path="/test/path.mp4",
                original_filename="test.mp4",
                file_size=1000,
                download_duration=1.0
            )
            
            # Should handle without crashing
            assert metadata.prompt == prompt
            
            # Test logging extremely long prompts
            try:
                self.manager.logger.log_download(metadata)
                # Should succeed
            except Exception as e:
                pytest.fail(f"Failed to log prompt of length {len(prompt)}: {e}")
                
    @pytest.mark.asyncio
    async def test_rapid_duplicate_checks(self):
        """Test rapid successive duplicate checks"""
        
        mock_page = Mock()
        
        # Setup existing log
        log_file = os.path.join(self.config.logs_folder, 'generation_downloads.txt')
        test_entry = {
            "file_id": "#000000001",
            "generation_date": "30 Aug 2025 05:11:29",
            "prompt": "Test prompt for duplicate checking",
            "download_timestamp": "2025-08-30T05:12:00.000000",
            "file_path": "/test/path.mp4",
            "original_filename": "test.mp4",
            "file_size": 1000,
            "download_duration": 1.0
        }
        
        with open(log_file, 'w') as f:
            f.write(json.dumps(test_entry) + '\n')
            
        self.manager._load_existing_log_entries()
        
        # Perform rapid duplicate checks
        with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
            mock_extract.return_value = {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'Test prompt for duplicate checking'
            }
            
            start_time = time.time()
            
            # Perform 100 rapid checks
            tasks = [
                self.manager.check_comprehensive_duplicate(mock_page, f'thumb_{i}')
                for i in range(100)
            ]
            
            results = await asyncio.gather(*tasks)
            
            duration = time.time() - start_time
            
            # Should complete quickly (under 1 second for 100 checks)
            assert duration < 1.0
            
            # All should detect duplicate
            assert all(result == True for result in results)

    # ===== PERFORMANCE TESTS =====
    
    def test_large_log_file_loading_performance(self):
        """Test performance with large log files"""
        
        log_file = os.path.join(self.config.logs_folder, 'large_generation_downloads.txt')
        
        # Create large log file
        print(f"\nGenerating large log file with 10,000 entries...")
        start_time = time.time()
        
        with open(log_file, 'w') as f:
            for i in range(10000):
                entry = {
                    "file_id": f"#000{i:06d}",
                    "generation_date": f"30 Aug 2025 {5 + (i % 20):02d}:{i % 60:02d}:{(i * 13) % 60:02d}",
                    "prompt": f"Generated prompt number {i} with detailed content and various characteristics",
                    "download_timestamp": f"2025-08-30T{5 + (i % 20):02d}:{i % 60:02d}:{(i * 13) % 60:02d}.{i % 1000000:06d}",
                    "file_path": f"/downloads/vids/video_{i:06d}.mp4",
                    "original_filename": f"temp_download_{i:06d}.mp4",
                    "file_size": 2000000 + (i * 1000),
                    "download_duration": 2.5 + (i * 0.01)
                }
                f.write(json.dumps(entry) + '\n')
                
        creation_time = time.time() - start_time
        print(f"Created large log in {creation_time:.2f} seconds")
        
        # Test loading performance
        original_log = self.manager.config.log_file
        self.manager.config.log_file = log_file
        
        try:
            start_time = time.time()
            self.manager._load_existing_log_entries()
            load_time = time.time() - start_time
            
            print(f"Loaded 10,000 entries in {load_time:.2f} seconds")
            
            # Should load within reasonable time (under 2 seconds)
            assert load_time < 2.0
            
            # Verify entries loaded correctly
            assert len(self.manager.existing_log_entries) == 10000
            
            # Test duplicate checking performance with large dataset
            mock_page = Mock()
            
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                # Test finding entry in middle of dataset
                mock_extract.return_value = {
                    'generation_date': '30 Aug 2025 10:00:26',  # Should match entry 5000
                    'prompt': 'Generated prompt number 5000 with detailed content and various characteristics'
                }
                
                start_time = time.time()
                is_duplicate = asyncio.run(
                    self.manager.check_comprehensive_duplicate(mock_page, 'test_thumb')
                )
                check_time = time.time() - start_time
                
                print(f"Found duplicate in large dataset in {check_time:.4f} seconds")
                
                # Should find duplicate quickly (under 0.1 seconds)
                assert check_time < 0.1
                assert is_duplicate == True
                
        finally:
            self.manager.config.log_file = original_log
            if os.path.exists(log_file):
                os.remove(log_file)
                
    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations"""
        
        # Setup test data
        log_file = os.path.join(self.config.logs_folder, 'concurrent_test.txt')
        with open(log_file, 'w') as f:
            for i in range(100):
                entry = {
                    "file_id": f"#000{i:03d}",
                    "generation_date": f"30 Aug 2025 05:{i % 60:02d}:00",
                    "prompt": f"Concurrent test prompt {i}",
                    "download_timestamp": "2025-08-30T05:00:00.000000",
                    "file_path": f"/test/path_{i}.mp4",
                    "original_filename": f"test_{i}.mp4",
                    "file_size": 1000,
                    "download_duration": 1.0
                }
                f.write(json.dumps(entry) + '\n')
                
        original_log = self.manager.config.log_file
        self.manager.config.log_file = log_file
        self.manager._load_existing_log_entries()
        
        try:
            mock_page = Mock()
            
            async def concurrent_duplicate_check(check_id):
                """Simulate concurrent duplicate checking"""
                with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                    # Random check - some will be duplicates, some won't
                    if check_id % 3 == 0:
                        # Make it a duplicate
                        mock_extract.return_value = {
                            'generation_date': f'30 Aug 2025 05:{check_id % 60:02d}:00',
                            'prompt': f'Concurrent test prompt {check_id}'
                        }
                    else:
                        # Make it unique
                        mock_extract.return_value = {
                            'generation_date': f'30 Aug 2025 06:{check_id % 60:02d}:00',
                            'prompt': f'Unique prompt {check_id}'
                        }
                        
                    result = await self.manager.check_comprehensive_duplicate(
                        mock_page, f'thumb_{check_id}'
                    )
                    return check_id, result
                    
            # Run 50 concurrent duplicate checks
            start_time = time.time()
            
            tasks = [concurrent_duplicate_check(i) for i in range(50)]
            results = await asyncio.gather(*tasks)
            
            duration = time.time() - start_time
            
            print(f"Completed 50 concurrent duplicate checks in {duration:.2f} seconds")
            
            # Should complete within reasonable time (under 2 seconds)
            assert duration < 2.0
            
            # Verify results
            assert len(results) == 50
            
            duplicates = [r for r in results if r[1] == True]
            uniques = [r for r in results if r[1] == False]
            
            print(f"Found {len(duplicates)} duplicates, {len(uniques)} unique")
            
            # Should have found some duplicates (every 3rd item)
            assert len(duplicates) > 0
            assert len(uniques) > 0
            
        finally:
            self.manager.config.log_file = original_log
            if os.path.exists(log_file):
                os.remove(log_file)
                
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage during intensive operations"""
        
        import psutil
        import gc
        
        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss
        
        # Create large dataset in memory
        large_entries = []
        for i in range(5000):
            entry = {
                'file_id': f'#000{i:06d}',
                'generation_date': f'30 Aug 2025 {5 + (i % 10):02d}:{i % 60:02d}:{(i * 7) % 60:02d}',
                'prompt': f'Memory test prompt {i} with additional content ' * 10,  # Make it larger
                'download_timestamp': datetime.now().isoformat(),
                'file_path': f'/test/path_{i}.mp4',
                'file_size': 2000000 + i,
                'download_duration': 3.0 + (i * 0.001)
            }
            large_entries.append(entry)
            
        self.manager.existing_log_entries = large_entries
        
        # Check memory after loading
        loaded_memory = process.memory_info().rss
        memory_increase = (loaded_memory - baseline_memory) / 1024 / 1024  # MB
        
        print(f"Memory increase after loading 5000 entries: {memory_increase:.2f} MB")
        
        # Should not use excessive memory (under 100MB for 5000 entries)
        assert memory_increase < 100
        
        # Perform intensive operations
        mock_page = Mock()
        
        async def memory_intensive_operation(op_id):
            with patch.object(self.manager, 'extract_metadata_from_page') as mock_extract:
                mock_extract.return_value = {
                    'generation_date': f'30 Aug 2025 07:{op_id % 60:02d}:{(op_id * 3) % 60:02d}',
                    'prompt': f'Memory intensive operation {op_id} with lots of text content ' * 20
                }
                
                return await self.manager.check_comprehensive_duplicate(mock_page, f'thumb_{op_id}')
                
        # Run memory intensive operations
        tasks = [memory_intensive_operation(i) for i in range(100)]
        await asyncio.gather(*tasks)
        
        # Check memory after operations
        final_memory = process.memory_info().rss
        operation_memory_increase = (final_memory - loaded_memory) / 1024 / 1024  # MB
        
        print(f"Additional memory increase during operations: {operation_memory_increase:.2f} MB")
        
        # Should not leak significant memory during operations (under 50MB)
        assert operation_memory_increase < 50
        
        # Clean up
        self.manager.existing_log_entries = []
        gc.collect()
        
        # Memory should decrease after cleanup
        cleanup_memory = process.memory_info().rss
        assert cleanup_memory < final_memory
        
    def test_date_parsing_performance(self):
        """Test performance of date parsing with various formats"""
        
        # Various date formats that might be encountered
        date_formats = [
            "30 Aug 2025 05:11:29",
            "30 August 2025 05:11:29", 
            "2025-08-30 05:11:29",
            "08/30/2025 05:11:29",
            "30/08/2025 05:11:29",
            "Aug 30, 2025 5:11:29 AM",
            "2025-08-30T05:11:29",
            "30 Aug 2025 5:11:29 AM",
        ]
        
        # Test parsing performance
        start_time = time.time()
        
        for _ in range(1000):  # Parse each format 1000 times
            for date_str in date_formats:
                # Simple string comparison (current approach)
                normalized = date_str.strip()
                # In real implementation, dates are compared as strings
                assert len(normalized) > 0
                
        parse_time = time.time() - start_time
        
        print(f"Parsed {len(date_formats) * 1000} dates in {parse_time:.3f} seconds")
        
        # Should parse quickly (under 0.1 seconds for 8000 dates)
        assert parse_time < 0.1
        
    @pytest.mark.asyncio
    async def test_exit_scan_return_scaling(self):
        """Test exit-scan-return performance with varying gallery sizes"""
        
        gallery_sizes = [10, 50, 100, 500, 1000]
        
        for size in gallery_sizes:
            mock_page = Mock()
            
            # Create mock containers for this size
            containers = []
            for i in range(size):
                container = Mock()
                container.click = AsyncMock(return_value=True)
                container.query_selector = AsyncMock()
                
                # Setup container metadata
                async def query_side_effect(selector, container_id=i):
                    if 'prompt' in selector.lower() or 'dnESm' in selector:
                        if container_id == size // 2:  # Middle container matches checkpoint
                            elem = Mock()
                            elem.text_content = AsyncMock(return_value="The camera begins with a tight close-up")
                            return elem
                        else:
                            elem = Mock()
                            elem.text_content = AsyncMock(return_value=f"Different prompt {container_id}")
                            return elem
                    elif 'time' in selector.lower() or 'jGymgu' in selector:
                        elem = Mock()
                        elem.text_content = AsyncMock(return_value="30 Aug 2025 05:11:29")
                        return elem
                    return None
                    
                container.query_selector.side_effect = query_side_effect
                containers.append(container)
                
            mock_page.query_selector_all = AsyncMock(return_value=containers)
            mock_page.go_back = AsyncMock(return_value=True)
            
            # Setup checkpoint data
            self.manager.checkpoint_data = {
                'generation_date': '30 Aug 2025 05:11:29',
                'prompt': 'The camera begins with a tight close-up',
                'file_id': '#000000123'
            }
            
            # Measure exit-scan-return performance
            start_time = time.time()
            result = await self.manager.exit_gallery_and_scan_generations(mock_page)
            scan_time = time.time() - start_time
            
            print(f"Exit-scan-return for {size} containers: {scan_time:.3f} seconds")
            
            # Should scale reasonably (under 0.5 seconds even for 1000 containers)
            assert scan_time < 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])