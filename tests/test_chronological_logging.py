#!/usr/bin/env python3
"""
Test suite for chronological logging functionality in generation download manager
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.generation_download_manager import (
    GenerationDownloadLogger, 
    GenerationDownloadConfig, 
    GenerationMetadata,
    DuplicateMode
)


class TestChronologicalLogging(unittest.TestCase):
    """Test cases for chronological insertion of log entries"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.logs_dir = Path(self.test_dir) / "logs"
        self.downloads_dir = Path(self.test_dir) / "downloads"
        self.logs_dir.mkdir(exist_ok=True)
        self.downloads_dir.mkdir(exist_ok=True)
        
        # Create test configuration
        self.config = GenerationDownloadConfig(
            logs_folder=str(self.logs_dir),
            log_filename="test_generations.txt",
            downloads_folder=str(self.downloads_dir)
        )
        
        # Create logger instance
        self.logger = GenerationDownloadLogger(self.config)
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
    def test_empty_file_insertion(self):
        """Test inserting into empty log file"""
        metadata = GenerationMetadata(
            file_id="#000000001",
            generation_date="28 Aug 2025 14:30:15",
            prompt="Test prompt for empty file",
            download_timestamp="2025-08-28T14:30:15",
            file_path=str(self.downloads_dir / "test.jpg")
        )
        
        result = self.logger.log_download(metadata)
        self.assertTrue(result)
        
        # Verify file content
        log_path = self.logs_dir / "test_generations.txt"
        self.assertTrue(log_path.exists())
        
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertIn("#000000001", content)
        self.assertIn("28 Aug 2025 14:30:15", content)
        self.assertIn("Test prompt for empty file", content)
        
    def test_chronological_ordering(self):
        """Test that entries are sorted chronologically (newest first)"""
        # Insert entries out of chronological order
        entries = [
            GenerationMetadata(
                file_id="#000000001",
                generation_date="28 Aug 2025 10:00:00",
                prompt="Middle entry",
                download_timestamp="2025-08-28T10:00:00",
                file_path=str(self.downloads_dir / "middle.jpg")
            ),
            GenerationMetadata(
                file_id="#000000002",
                generation_date="28 Aug 2025 15:00:00",
                prompt="Newest entry",
                download_timestamp="2025-08-28T15:00:00",
                file_path=str(self.downloads_dir / "newest.jpg")
            ),
            GenerationMetadata(
                file_id="#000000003",
                generation_date="28 Aug 2025 05:00:00",
                prompt="Oldest entry",
                download_timestamp="2025-08-28T05:00:00",
                file_path=str(self.downloads_dir / "oldest.jpg")
            )
        ]
        
        # Log all entries
        for entry in entries:
            result = self.logger.log_download(entry)
            self.assertTrue(result)
            
        # Read and verify order
        log_path = self.logs_dir / "test_generations.txt"
        with open(log_path, 'r') as f:
            lines = f.readlines()
            
        # Find the positions of each prompt
        positions = {}
        for i, line in enumerate(lines):
            if "Newest entry" in line:
                positions["newest"] = i
            elif "Middle entry" in line:
                positions["middle"] = i
            elif "Oldest entry" in line:
                positions["oldest"] = i
                
        # Verify chronological order (newest first)
        self.assertLess(positions["newest"], positions["middle"])
        self.assertLess(positions["middle"], positions["oldest"])
        
    def test_placeholder_id_usage(self):
        """Test that #999999999 is used for new entries"""
        metadata = GenerationMetadata(
            file_id=None,  # No ID provided
            generation_date="28 Aug 2025 12:00:00",
            prompt="Entry without ID",
            download_timestamp="2025-08-28T12:00:00",
            file_path=str(self.downloads_dir / "no_id.jpg")
        )
        
        result = self.logger.log_download(metadata)
        self.assertTrue(result)
        
        # Verify placeholder ID is used
        log_path = self.logs_dir / "test_generations.txt"
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertIn("#999999999", content)
        
    def test_various_date_formats(self):
        """Test parsing various date formats"""
        date_formats = [
            ("28 Aug 2025 14:30:15", "Standard format"),
            ("2025-08-28 14:30:15", "ISO format"),
            ("28/08/2025 14:30:15", "DD/MM/YYYY format"),
            ("08/28/2025 14:30:15", "MM/DD/YYYY format")
        ]
        
        for date_str, desc in date_formats:
            metadata = GenerationMetadata(
                file_id=f"#00000{len(date_formats)}",
                generation_date=date_str,
                prompt=f"Test with {desc}",
                download_timestamp="2025-08-28T14:30:15",
                file_path=str(self.downloads_dir / f"test_{desc}.jpg")
            )
            
            # Create a fresh logger for each test
            logger = GenerationDownloadLogger(self.config)
            parsed_date = logger._parse_date_for_comparison(date_str)
            self.assertIsNotNone(parsed_date, f"Failed to parse: {desc}")
            
    def test_invalid_date_fallback(self):
        """Test that invalid dates fall back to append mode"""
        metadata = GenerationMetadata(
            file_id="#000000001",
            generation_date="Invalid Date String",
            prompt="Entry with invalid date",
            download_timestamp="2025-08-28T14:30:15",
            file_path=str(self.downloads_dir / "invalid.jpg")
        )
        
        result = self.logger.log_download(metadata)
        self.assertTrue(result)  # Should still succeed with fallback
        
        # Verify entry was logged
        log_path = self.logs_dir / "test_generations.txt"
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertIn("Entry with invalid date", content)
        
    def test_duplicate_mode_configuration(self):
        """Test SKIP vs FINISH duplicate modes"""
        # Test SKIP mode configuration
        skip_config = GenerationDownloadConfig.create_with_skip_mode(
            logs_folder=str(self.logs_dir),
            log_filename="skip_test.txt",
            downloads_folder=str(self.downloads_dir)
        )
        self.assertEqual(skip_config.duplicate_mode, DuplicateMode.SKIP)
        self.assertFalse(skip_config.stop_on_duplicate)
        
        # Test FINISH mode configuration
        finish_config = GenerationDownloadConfig.create_with_finish_mode(
            logs_folder=str(self.logs_dir),
            log_filename="finish_test.txt",
            downloads_folder=str(self.downloads_dir)
        )
        self.assertEqual(finish_config.duplicate_mode, DuplicateMode.FINISH)
        self.assertTrue(finish_config.stop_on_duplicate)
        
    def test_file_corruption_recovery(self):
        """Test recovery from corrupted log file"""
        # Create a corrupted log file
        log_path = self.logs_dir / "test_generations.txt"
        with open(log_path, 'w') as f:
            f.write("Corrupted content without proper format\n")
            f.write("Random text here\n")
            
        # Try to log new entry
        metadata = GenerationMetadata(
            file_id="#000000001",
            generation_date="28 Aug 2025 14:30:15",
            prompt="Recovery test entry",
            download_timestamp="2025-08-28T14:30:15",
            file_path=str(self.downloads_dir / "recovery.jpg")
        )
        
        result = self.logger.log_download(metadata)
        self.assertTrue(result)  # Should succeed despite corruption
        
        # Verify new entry was added
        with open(log_path, 'r') as f:
            content = f.read()
            
        self.assertIn("Recovery test entry", content)
        
    def test_large_file_performance(self):
        """Test performance with large number of entries"""
        import time
        
        # Create 100 entries
        for i in range(100):
            metadata = GenerationMetadata(
                file_id=f"#00000{i:04d}",
                generation_date=f"28 Aug 2025 {i//60:02d}:{i%60:02d}:00",
                prompt=f"Entry number {i}",
                download_timestamp=f"2025-08-28T{i//60:02d}:{i%60:02d}:00",
                file_path=str(self.downloads_dir / f"file_{i}.jpg")
            )
            self.logger.log_download(metadata)
            
        # Add one more entry and measure time
        start_time = time.time()
        
        metadata = GenerationMetadata(
            file_id="#000000999",
            generation_date="28 Aug 2025 12:00:00",
            prompt="Performance test entry",
            download_timestamp="2025-08-28T12:00:00",
            file_path=str(self.downloads_dir / "perf_test.jpg")
        )
        
        result = self.logger.log_download(metadata)
        elapsed_time = time.time() - start_time
        
        self.assertTrue(result)
        self.assertLess(elapsed_time, 1.0)  # Should complete within 1 second
        

if __name__ == "__main__":
    unittest.main()