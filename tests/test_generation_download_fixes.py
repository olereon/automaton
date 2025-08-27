#!/usr/bin/env python3.11
"""
Test script to verify generation download manager fixes
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.generation_download_manager import (
    GenerationMetadata, 
    GenerationDownloadConfig, 
    EnhancedFileNamer, 
    GenerationDownloadLogger
)


def test_generation_metadata_creation():
    """Test that GenerationMetadata objects can be created correctly"""
    metadata = GenerationMetadata(
        file_id="test123",
        generation_date="2024-08-27 10:30:45",
        prompt="Test prompt for generation",
        download_timestamp=datetime.now().isoformat(),
        file_path="/test/path/video.mp4",
        original_filename="temp_file.mp4",
        file_size=1024000,
        download_duration=5.5
    )
    
    assert metadata.file_id == "test123"
    assert metadata.generation_date == "2024-08-27 10:30:45"
    assert metadata.prompt == "Test prompt for generation"
    assert metadata.file_size == 1024000
    assert metadata.download_duration == 5.5


def test_filename_generation_with_initTest():
    """Test that filenames are generated correctly with initTest unique_id"""
    config = GenerationDownloadConfig()
    config.use_descriptive_naming = True
    config.unique_id = "initTest"
    config.naming_format = "{media_type}_{creation_date}_{unique_id}"
    config.date_format = "%Y-%m-%d-%H-%M-%S"
    
    file_namer = EnhancedFileNamer(config)
    
    # Test with mp4 file
    test_file = Path("/tmp/test_video.mp4")
    filename = file_namer.generate_filename(
        file_path=test_file,
        creation_date="2024-08-27 10:30:45",
        sequence_number=1
    )
    
    # Verify filename structure
    assert filename.endswith(".mp4"), "Filename should end with .mp4 extension"
    assert filename.startswith("vid_"), "Filename should start with vid_ media type"
    assert "initTest" in filename, "Filename should contain initTest unique_id"
    assert "2024-08-27-10-30-45" in filename, "Filename should contain formatted date"
    
    expected_filename = "vid_2024-08-27-10-30-45_initTest.mp4"
    assert filename == expected_filename, f"Expected {expected_filename}, got {filename}"


def test_logger_accepts_metadata_object():
    """Test that GenerationLogger.log_download accepts GenerationMetadata objects"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = GenerationDownloadConfig()
        config.logs_folder = temp_dir
        
        logger = GenerationDownloadLogger(config)
        
        metadata = GenerationMetadata(
            file_id="test456",
            generation_date="2024-08-27 15:20:30", 
            prompt="Another test prompt",
            download_timestamp=datetime.now().isoformat(),
            file_path="/test/path2/video2.mp4",
            original_filename="temp_file2.mp4",
            file_size=2048000,
            download_duration=3.2
        )
        
        # This should not raise an exception
        result = logger.log_download(metadata)
        assert result == True, "log_download should return True for successful logging"
        
        # Verify log file was created and contains expected content
        log_file = Path(temp_dir) / config.log_filename
        assert log_file.exists(), f"Log file should be created at {log_file}"
        
        log_content = log_file.read_text(encoding='utf-8')
        assert "test456" in log_content, "Log should contain file_id"
        assert "Another test prompt" in log_content, "Log should contain prompt"


def test_media_type_mapping():
    """Test that media types are correctly mapped"""
    config = GenerationDownloadConfig()
    file_namer = EnhancedFileNamer(config)
    
    # Test various extensions
    assert file_namer.get_media_type(".mp4") == "vid"
    assert file_namer.get_media_type(".avi") == "vid"
    assert file_namer.get_media_type(".mov") == "vid"
    assert file_namer.get_media_type(".jpg") == "img"
    assert file_namer.get_media_type(".png") == "img"
    assert file_namer.get_media_type(".unknown") == "file"


if __name__ == "__main__":
    # Run tests directly
    print("Running generation download manager fix tests...")
    
    test_generation_metadata_creation()
    print("✅ GenerationMetadata creation test passed")
    
    test_filename_generation_with_initTest()
    print("✅ Filename generation with initTest test passed")
    
    test_logger_accepts_metadata_object()
    print("✅ Logger metadata object test passed")
    
    test_media_type_mapping()
    print("✅ Media type mapping test passed")
    
    print("\n🎉 All tests passed! Generation download manager fixes are working correctly.")