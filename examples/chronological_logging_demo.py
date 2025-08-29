#!/usr/bin/env python3
"""
Demonstration of chronological logging feature for generation downloads
Shows how entries are automatically sorted by Creation Time (newest first)
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.generation_download_manager import (
    GenerationDownloadLogger,
    GenerationDownloadConfig,
    GenerationMetadata,
    DuplicateMode
)


def print_separator():
    """Print a visual separator"""
    print("=" * 80)


def demonstrate_chronological_insertion():
    """Demonstrate chronological insertion of log entries"""
    print("\n🎯 CHRONOLOGICAL LOGGING DEMONSTRATION")
    print_separator()
    
    # Create temporary directories for demo
    test_dir = tempfile.mkdtemp()
    logs_dir = Path(test_dir) / "logs"
    downloads_dir = Path(test_dir) / "downloads"
    logs_dir.mkdir(exist_ok=True)
    downloads_dir.mkdir(exist_ok=True)
    
    try:
        # Create configuration
        config = GenerationDownloadConfig(
            logs_folder=str(logs_dir),
            log_filename="demo_generations.txt",
            downloads_folder=str(downloads_dir)
        )
        
        # Create logger
        logger = GenerationDownloadLogger(config)
        log_path = logs_dir / "demo_generations.txt"
        
        print(f"📁 Log file location: {log_path}")
        print_separator()
        
        # Simulate downloading generations out of order
        print("\n📥 Simulating downloads (out of chronological order):")
        print("-" * 40)
        
        # Entry 1: Middle time
        entry1 = GenerationMetadata(
            file_id="#000000001",
            generation_date="28 Aug 2025 12:00:00",
            prompt="A serene mountain landscape at sunset",
            download_timestamp="2025-08-28T18:00:00",  # Downloaded at 6 PM
            file_path=str(downloads_dir / "mountain.jpg")
        )
        print(f"1️⃣ Downloading: {entry1.generation_date} - {entry1.prompt[:30]}...")
        logger.log_download(entry1)
        
        # Entry 2: Newest time
        entry2 = GenerationMetadata(
            file_id="#000000002",
            generation_date="28 Aug 2025 18:30:00",
            prompt="Futuristic city with neon lights",
            download_timestamp="2025-08-28T18:01:00",  # Downloaded 1 minute later
            file_path=str(downloads_dir / "city.jpg")
        )
        print(f"2️⃣ Downloading: {entry2.generation_date} - {entry2.prompt[:30]}...")
        logger.log_download(entry2)
        
        # Entry 3: Oldest time
        entry3 = GenerationMetadata(
            file_id="#000000003",
            generation_date="28 Aug 2025 06:00:00",
            prompt="Ocean waves crashing on rocky shore",
            download_timestamp="2025-08-28T18:02:00",  # Downloaded 2 minutes later
            file_path=str(downloads_dir / "ocean.jpg")
        )
        print(f"3️⃣ Downloading: {entry3.generation_date} - {entry3.prompt[:30]}...")
        logger.log_download(entry3)
        
        # Entry 4: Using placeholder ID
        entry4 = GenerationMetadata(
            file_id=None,  # No ID - will use #999999999
            generation_date="28 Aug 2025 15:00:00",
            prompt="Abstract art with vibrant colors",
            download_timestamp="2025-08-28T18:03:00",
            file_path=str(downloads_dir / "abstract.jpg")
        )
        print(f"4️⃣ Downloading: {entry4.generation_date} - {entry4.prompt[:30]}... (no ID)")
        logger.log_download(entry4)
        
        print_separator()
        print("\n✅ All entries downloaded!")
        print_separator()
        
        # Display the log file content
        print("\n📄 LOG FILE CONTENT (automatically sorted by Creation Time):")
        print("-" * 40)
        
        with open(log_path, 'r') as f:
            content = f.read()
            print(content)
            
        print_separator()
        print("\n🔍 ANALYSIS:")
        print("-" * 40)
        print("✨ Notice how entries are automatically sorted chronologically!")
        print("📅 Newest entries appear first (18:30:00)")
        print("📅 Oldest entries appear last (06:00:00)")
        print("🆔 Entry without ID uses #999999999 placeholder")
        print("🎯 This ensures the log reflects the actual generation timeline")
        
    finally:
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)


def demonstrate_duplicate_modes():
    """Demonstrate SKIP vs FINISH duplicate modes"""
    print("\n\n🔄 DUPLICATE MODE DEMONSTRATION")
    print_separator()
    
    # Create temporary directories
    test_dir = tempfile.mkdtemp()
    logs_dir = Path(test_dir) / "logs"
    downloads_dir = Path(test_dir) / "downloads"
    logs_dir.mkdir(exist_ok=True)
    downloads_dir.mkdir(exist_ok=True)
    
    try:
        print("\n1️⃣ FINISH Mode (stops on duplicate):")
        print("-" * 40)
        
        # Create config with FINISH mode
        finish_config = GenerationDownloadConfig.create_with_finish_mode(
            logs_folder=str(logs_dir),
            log_filename="finish_mode.txt",
            downloads_folder=str(downloads_dir)
        )
        
        print(f"   Mode: {finish_config.duplicate_mode.value}")
        print(f"   Stop on duplicate: {finish_config.stop_on_duplicate}")
        print("   Behavior: Automation stops when reaching previously downloaded content")
        
        print("\n2️⃣ SKIP Mode (continues past duplicates):")
        print("-" * 40)
        
        # Create config with SKIP mode
        skip_config = GenerationDownloadConfig.create_with_skip_mode(
            logs_folder=str(logs_dir),
            log_filename="skip_mode.txt",
            downloads_folder=str(downloads_dir)
        )
        
        print(f"   Mode: {skip_config.duplicate_mode.value}")
        print(f"   Stop on duplicate: {skip_config.stop_on_duplicate}")
        print("   Behavior: Skips duplicates and continues searching for new generations")
        
        print_separator()
        print("\n💡 Use Cases:")
        print("-" * 40)
        print("📌 FINISH Mode: Use when you want to download only new content since last run")
        print("📌 SKIP Mode: Use when gallery may have mixed old/new content throughout")
        
    finally:
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)


def demonstrate_edge_cases():
    """Demonstrate handling of edge cases"""
    print("\n\n🔧 EDGE CASE HANDLING DEMONSTRATION")
    print_separator()
    
    # Create temporary directories
    test_dir = tempfile.mkdtemp()
    logs_dir = Path(test_dir) / "logs"
    downloads_dir = Path(test_dir) / "downloads"
    logs_dir.mkdir(exist_ok=True)
    downloads_dir.mkdir(exist_ok=True)
    
    try:
        config = GenerationDownloadConfig(
            logs_folder=str(logs_dir),
            log_filename="edge_cases.txt",
            downloads_folder=str(downloads_dir)
        )
        
        logger = GenerationDownloadLogger(config)
        
        print("\n1️⃣ Testing invalid date format:")
        print("-" * 40)
        
        invalid_entry = GenerationMetadata(
            file_id="#000000001",
            generation_date="Invalid Date Format",
            prompt="Entry with invalid date",
            download_timestamp="2025-08-28T12:00:00",
            file_path=str(downloads_dir / "invalid.jpg")
        )
        
        result = logger.log_download(invalid_entry)
        print(f"   Result: {'✅ Success (fallback to append)' if result else '❌ Failed'}")
        
        print("\n2️⃣ Testing various date formats:")
        print("-" * 40)
        
        date_formats = [
            "28 Aug 2025 14:30:15",  # Standard
            "2025-08-28 14:30:15",   # ISO
            "28/08/2025 14:30:15",   # DD/MM/YYYY
            "08/28/2025 14:30:15"    # MM/DD/YYYY
        ]
        
        for i, date_str in enumerate(date_formats, 1):
            entry = GenerationMetadata(
                file_id=f"#00000000{i+1}",
                generation_date=date_str,
                prompt=f"Testing date format: {date_str}",
                download_timestamp="2025-08-28T14:30:15",
                file_path=str(downloads_dir / f"date_test_{i}.jpg")
            )
            
            result = logger.log_download(entry)
            parsed = logger._parse_date_for_comparison(date_str)
            print(f"   Format {i}: {date_str:25} - {'✅ Parsed' if parsed else '❌ Failed'}")
        
        print("\n3️⃣ Testing placeholder ID assignment:")
        print("-" * 40)
        
        no_id_entry = GenerationMetadata(
            file_id=None,
            generation_date="28 Aug 2025 16:00:00",
            prompt="Entry without file ID",
            download_timestamp="2025-08-28T16:00:00",
            file_path=str(downloads_dir / "no_id.jpg")
        )
        
        logger.log_download(no_id_entry)
        
        log_path = logs_dir / "edge_cases.txt"
        with open(log_path, 'r') as f:
            content = f.read()
            
        has_placeholder = "#999999999" in content
        print(f"   Placeholder ID used: {'✅ Yes' if has_placeholder else '❌ No'}")
        
        print_separator()
        
    finally:
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 GENERATION DOWNLOAD CHRONOLOGICAL LOGGING DEMO")
    print("=" * 80)
    
    # Run demonstrations
    demonstrate_chronological_insertion()
    demonstrate_duplicate_modes()
    demonstrate_edge_cases()
    
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE!")
    print("=" * 80)
    print("\n💡 Key Takeaways:")
    print("   • Entries are automatically sorted by Creation Time (newest first)")
    print("   • Placeholder ID #999999999 is used for new entries")
    print("   • Two duplicate modes: FINISH (stop) and SKIP (continue)")
    print("   • Robust date parsing supports multiple formats")
    print("   • Graceful fallback for invalid dates")
    print("=" * 80 + "\n")