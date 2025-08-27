#!/usr/bin/env python3
"""
Unit Tests for Metadata Extraction Fixes

Focused unit tests for specific components of the metadata extraction system.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationDownloadConfig,
    EnhancedFileNamer,
    GenerationMetadata
)


class TestEnhancedFileNamer:
    """Unit tests for Enhanced File Namer"""

    @pytest.fixture
    def config(self):
        return GenerationDownloadConfig(
            use_descriptive_naming=True,
            unique_id="test",
            naming_format="{media_type}_{creation_date}_{unique_id}",
            date_format="%Y-%m-%d-%H-%M-%S"
        )

    @pytest.fixture
    def namer(self, config):
        return EnhancedFileNamer(config)

    def test_get_media_type(self, namer):
        """Test media type detection from file extensions"""
        assert namer.get_media_type("mp4") == "vid"
        assert namer.get_media_type(".mp4") == "vid"
        assert namer.get_media_type("jpg") == "img"
        assert namer.get_media_type("mp3") == "aud"
        assert namer.get_media_type("unknown") == "file"

    def test_parse_creation_date_valid_formats(self, namer):
        """Test date parsing with valid formats"""
        test_cases = [
            ("24 Aug 2025 01:37:01", "2025-08-24-01-37-01"),
            ("2025-08-24 01:37:01", "2025-08-24-01-37-01"),
            ("24/08/2025 01:37:01", "2025-08-24-01-37-01"),
            ("08/24/2025 01:37:01", "2025-08-24-01-37-01"),
            ("2025-08-24", "2025-08-24-00-00-00"),
            ("24 Aug 2025", "2025-08-24-00-00-00"),
        ]
        
        for input_date, expected in test_cases:
            result = namer.parse_creation_date(input_date)
            assert result == expected, f"Failed for input: {input_date}"

    def test_parse_creation_date_invalid_formats(self, namer):
        """Test date parsing with invalid formats"""
        invalid_inputs = [
            "",
            None,
            "Unknown Date",
            "Invalid Date Format",
            "Not a date",
            "32 Aug 2025 25:70:99",
        ]
        
        for invalid_input in invalid_inputs:
            result = namer.parse_creation_date(invalid_input)
            
            # Should return current timestamp format
            assert isinstance(result, str)
            assert len(result.split('-')) == 6  # YYYY-MM-DD-HH-MM-SS
            
            # Should be close to current time (within 1 minute)
            try:
                parsed = datetime.strptime(result, "%Y-%m-%d-%H-%M-%S")
                time_diff = abs((datetime.now() - parsed).total_seconds())
                assert time_diff < 60, f"Generated time too far from current: {result}"
            except ValueError:
                pytest.fail(f"Generated invalid timestamp format: {result}")

    def test_generate_filename_descriptive(self, namer):
        """Test descriptive filename generation"""
        test_file = Path("/tmp/test.mp4")
        
        result = namer.generate_filename(
            file_path=test_file,
            creation_date="24 Aug 2025 01:37:01"
        )
        
        expected = "vid_2025-08-24-01-37-01_test.mp4"
        assert result == expected

    def test_generate_filename_fallback_to_sequential(self, namer):
        """Test fallback to sequential naming"""
        # Disable descriptive naming
        namer.config.use_descriptive_naming = False
        
        test_file = Path("/tmp/test.mp4")
        
        result = namer.generate_filename(
            file_path=test_file,
            sequence_number=42
        )
        
        expected = "#000000042.mp4"
        assert result == expected

    def test_sanitize_filename(self, namer):
        """Test filename sanitization"""
        test_cases = [
            ("normal_file.mp4", "normal_file.mp4"),
            ("file<>with|bad*chars.mp4", "file__with_bad_chars.mp4"),
            ('file"with:quotes.mp4', "file_with_quotes.mp4"),
            ("file with spaces.mp4", "file_with_spaces.mp4"),
            ("a" * 250 + ".mp4", True),  # Should be truncated
        ]
        
        for input_name, expected in test_cases:
            result = namer.sanitize_filename(input_name)
            
            if isinstance(expected, bool):
                # Check length constraint
                assert len(result) <= 200
            else:
                assert result == expected
            
            # Ensure no invalid characters remain
            invalid_chars = '<>:"/\\|?*'
            assert not any(char in result for char in invalid_chars)

    def test_generate_filename_with_unknown_date(self, namer):
        """Test filename generation with unknown date"""
        test_file = Path("/tmp/test.mp4")
        
        result = namer.generate_filename(
            file_path=test_file,
            creation_date="Unknown Date"
        )
        
        # Should use current timestamp
        assert result.startswith("vid_")
        assert result.endswith("_test.mp4")
        assert len(result.split('_')) == 3  # vid, date, unique_id

    def test_different_file_extensions(self, namer):
        """Test with different file extensions"""
        extensions = [
            (".mp4", "vid"),
            (".jpg", "img"), 
            (".mp3", "aud"),
            (".txt", "file"),
            (".unknown", "file")
        ]
        
        for ext, expected_type in extensions:
            test_file = Path(f"/tmp/test{ext}")
            
            result = namer.generate_filename(
                file_path=test_file,
                creation_date="24 Aug 2025 01:37:01"
            )
            
            assert result.startswith(f"{expected_type}_")
            assert result.endswith(f"_test{ext}")


class TestGenerationMetadata:
    """Unit tests for GenerationMetadata dataclass"""

    def test_metadata_creation(self):
        """Test creating GenerationMetadata objects"""
        metadata = GenerationMetadata(
            file_id="#000000001",
            generation_date="24 Aug 2025 01:37:01",
            prompt="Test prompt for generation",
            download_timestamp="2025-08-24 12:00:00",
            file_path="/test/path/file.mp4",
            original_filename="download.mp4",
            file_size=1024000,
            download_duration=15.5
        )
        
        assert metadata.file_id == "#000000001"
        assert metadata.generation_date == "24 Aug 2025 01:37:01"
        assert metadata.prompt == "Test prompt for generation"
        assert metadata.file_size == 1024000
        assert metadata.download_duration == 15.5

    def test_metadata_defaults(self):
        """Test GenerationMetadata with default values"""
        metadata = GenerationMetadata(
            file_id="#000000001",
            generation_date="24 Aug 2025 01:37:01",
            prompt="Test prompt",
            download_timestamp="2025-08-24 12:00:00",
            file_path="/test/path/file.mp4"
        )
        
        # Check defaults
        assert metadata.original_filename == ""
        assert metadata.file_size == 0
        assert metadata.download_duration == 0.0


class TestGenerationDownloadConfig:
    """Unit tests for GenerationDownloadConfig"""

    def test_default_config(self):
        """Test default configuration values"""
        config = GenerationDownloadConfig()
        
        # Check key defaults
        assert config.max_downloads == 50
        assert config.starting_file_id == 1
        assert config.use_descriptive_naming == True
        assert config.unique_id == "gen"
        assert config.creation_time_text == "Creation Time"
        assert config.prompt_ellipsis_pattern == "</span>..."

    def test_custom_config(self):
        """Test custom configuration"""
        config = GenerationDownloadConfig(
            max_downloads=100,
            unique_id="custom",
            use_descriptive_naming=False,
            creation_time_text="Custom Creation Time"
        )
        
        assert config.max_downloads == 100
        assert config.unique_id == "custom"
        assert config.use_descriptive_naming == False
        assert config.creation_time_text == "Custom Creation Time"

    def test_config_paths(self):
        """Test configuration path handling"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = GenerationDownloadConfig(
                downloads_folder=temp_dir + "/downloads",
                logs_folder=temp_dir + "/logs"
            )
            
            assert config.downloads_folder == temp_dir + "/downloads"
            assert config.logs_folder == temp_dir + "/logs"


class TestUtilityFunctions:
    """Unit tests for utility functions and helpers"""

    def test_date_selection_logic(self):
        """Test date selection logic directly"""
        from utils.generation_download_manager import GenerationDownloadManager
        
        config = GenerationDownloadConfig()
        manager = GenerationDownloadManager(config)
        
        # Test with no candidates
        result = manager._select_best_date_candidate([])
        assert result == "Unknown Date"
        
        # Test with single candidate
        candidates = [{"extracted_date": "24 Aug 2025 01:37:01", "element_index": 0}]
        result = manager._select_best_date_candidate(candidates)
        assert result == "24 Aug 2025 01:37:01"
        
        # Test with multiple candidates - should prefer least common
        candidates = [
            {"extracted_date": "24 Aug 2025 01:37:01", "element_index": 0},
            {"extracted_date": "24 Aug 2025 01:37:01", "element_index": 1},  # Common
            {"extracted_date": "23 Aug 2025 15:42:13", "element_index": 2}   # Unique
        ]
        result = manager._select_best_date_candidate(candidates)
        assert result == "23 Aug 2025 15:42:13"

    def test_filename_collision_handling(self):
        """Test handling of filename collisions"""
        config = GenerationDownloadConfig(use_descriptive_naming=True, unique_id="test")
        namer = EnhancedFileNamer(config)
        
        test_file = Path("/tmp/test.mp4")
        
        # Mock Path.exists to simulate collision
        with patch('pathlib.Path.exists') as mock_exists:
            # First call returns True (file exists), then False
            mock_exists.side_effect = [True, False]
            
            # Note: This test may need adjustment based on actual collision handling logic
            # The generate_filename method should handle collisions internally
            result = namer.generate_filename(
                file_path=test_file,
                creation_date="24 Aug 2025 01:37:01"
            )
            
            # Should generate some valid filename
            assert isinstance(result, str)
            assert result.endswith(".mp4")

    def test_error_handling_in_date_parsing(self):
        """Test error handling during date parsing"""
        config = GenerationDownloadConfig()
        namer = EnhancedFileNamer(config)
        
        # Test error handling by providing malformed date that will trigger exception handling
        invalid_dates = [
            "Not a date at all",
            "32 Aug 2025 25:70:99",  # Invalid values  
            "",
            None
        ]
        
        for invalid_date in invalid_dates:
            result = namer.parse_creation_date(invalid_date)
            
            # Should fallback to current timestamp
            assert isinstance(result, str)
            assert len(result.split('-')) == 6
            
            # Should be close to current time (within 1 minute)
            try:
                parsed = datetime.strptime(result, "%Y-%m-%d-%H-%M-%S")
                time_diff = abs((datetime.now() - parsed).total_seconds())
                assert time_diff < 60, f"Generated time too far from current: {result}"
            except ValueError:
                pytest.fail(f"Generated invalid timestamp format: {result}")

    def test_media_type_edge_cases(self):
        """Test media type detection edge cases"""
        config = GenerationDownloadConfig()
        namer = EnhancedFileNamer(config)
        
        # Test edge cases
        assert namer.get_media_type("") == "file"
        assert namer.get_media_type(".") == "file" 
        assert namer.get_media_type("MP4") == "vid"  # Case insensitive
        assert namer.get_media_type("...mp4") == "vid"  # Multiple dots


if __name__ == "__main__":
    pytest.main([__file__, "-v"])