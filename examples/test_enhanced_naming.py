#!/usr/bin/env python3.11
"""
Test script for enhanced file naming system
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig,
    EnhancedFileNamer
)

# Enable detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_file_naming_logic():
    """Test the enhanced file naming logic without browser automation"""
    
    print("🏷️ Testing Enhanced File Naming System")
    print("=" * 50)
    
    # Test different configurations
    test_configs = [
        {
            "name": "Video with Custom ID",
            "config": GenerationDownloadConfig(
                use_descriptive_naming=True,
                unique_id="initialT",
                naming_format="{media_type}_{creation_date}_{unique_id}",
                date_format="%Y-%m-%d-%H-%M-%S"
            ),
            "file_path": Path("test_video.mp4"),
            "creation_date": "24 Aug 2025 14:35:22",
            "expected_pattern": "vid_2025-08-24-14-35-22_initialT.mp4"
        },
        {
            "name": "Image with Project ID", 
            "config": GenerationDownloadConfig(
                use_descriptive_naming=True,
                unique_id="project_alpha",
                naming_format="{media_type}_{creation_date}_{unique_id}",
                date_format="%Y%m%d_%H%M%S"
            ),
            "file_path": Path("generated_image.png"),
            "creation_date": "2025-08-24 09:15:30",
            "expected_pattern": "img_20250824_091530_project_alpha.png"
        },
        {
            "name": "Audio with Sequence",
            "config": GenerationDownloadConfig(
                use_descriptive_naming=True,
                unique_id="seq001", 
                naming_format="{media_type}_{unique_id}_{creation_date}",
                date_format="%d-%m-%Y"
            ),
            "file_path": Path("audio_track.mp3"),
            "creation_date": "24/08/2025 16:45:12",
            "expected_pattern": "aud_seq001_24-08-2025.mp3"
        },
        {
            "name": "Legacy Sequential Naming",
            "config": GenerationDownloadConfig(
                use_descriptive_naming=False,
                id_format="#{:09d}"
            ),
            "file_path": Path("legacy_file.webm"),
            "creation_date": "24 Aug 2025 14:35:22", 
            "sequence_number": 42,
            "expected_pattern": "#000000042.webm"
        }
    ]
    
    print(f"🧪 Running {len(test_configs)} naming tests...\n")
    
    for i, test in enumerate(test_configs, 1):
        print(f"Test {i}: {test['name']}")
        print(f"  📁 Input File: {test['file_path'].name}")
        print(f"  📅 Creation Date: {test.get('creation_date', 'N/A')}")
        print(f"  🎯 Expected Pattern: {test['expected_pattern']}")
        
        try:
            # Create file namer
            namer = EnhancedFileNamer(test['config'])
            
            if test['config'].use_descriptive_naming:
                # Test descriptive naming
                result = namer.generate_filename(
                    test['file_path'],
                    creation_date=test['creation_date']
                )
            else:
                # Test legacy naming
                result = namer.generate_filename(
                    test['file_path'],
                    sequence_number=test.get('sequence_number')
                )
            
            print(f"  ✅ Generated: {result}")
            
            # Basic validation
            if test['config'].use_descriptive_naming:
                # Check media type
                expected_media = test['expected_pattern'].split('_')[0]
                actual_media = result.split('_')[0]
                if expected_media == actual_media:
                    print(f"  ✅ Media type correct: {actual_media}")
                else:
                    print(f"  ❌ Media type mismatch: expected {expected_media}, got {actual_media}")
                
                # Check unique ID presence
                if test['config'].unique_id in result:
                    print(f"  ✅ Unique ID included: {test['config'].unique_id}")
                else:
                    print(f"  ❌ Unique ID missing: {test['config'].unique_id}")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()

def test_media_type_detection():
    """Test media type detection for various file extensions"""
    
    print("🎬 Testing Media Type Detection")
    print("=" * 30)
    
    config = GenerationDownloadConfig()
    namer = EnhancedFileNamer(config)
    
    test_extensions = [
        # Videos
        ('.mp4', 'vid'), ('.avi', 'vid'), ('.mov', 'vid'), ('.webm', 'vid'),
        # Images  
        ('.jpg', 'img'), ('.png', 'img'), ('.gif', 'img'), ('.webp', 'img'),
        # Audio
        ('.mp3', 'aud'), ('.wav', 'aud'), ('.flac', 'aud'), ('.ogg', 'aud'),
        # Unknown
        ('.xyz', 'file'), ('.unknown', 'file')
    ]
    
    for ext, expected in test_extensions:
        result = namer.get_media_type(ext)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {ext:8} → {result:4} (expected: {expected})")

def test_date_parsing():
    """Test date parsing from various formats"""
    
    print("\n📅 Testing Date Parsing")
    print("=" * 25)
    
    config = GenerationDownloadConfig(date_format="%Y-%m-%d-%H-%M-%S")
    namer = EnhancedFileNamer(config)
    
    test_dates = [
        "24 Aug 2025 14:35:22",    # Current format
        "2025-08-24 14:35:22",    # ISO format
        "24/08/2025 14:35:22",    # EU format  
        "08/24/2025 14:35:22",    # US format
        "2025-08-24",             # Date only
        "24 Aug 2025",            # Readable date
        "Invalid Date",           # Should fallback
        "",                       # Empty should fallback
    ]
    
    for date_str in test_dates:
        result = namer.parse_creation_date(date_str)
        print(f"  📅 '{date_str}' → {result}")

async def demo_full_system():
    """Demonstrate the full enhanced naming system"""
    
    print("\n🚀 Enhanced Naming System Demo")
    print("=" * 40)
    
    # Load enhanced configuration
    config = GenerationDownloadConfig(
        downloads_folder="/home/olereon/workspace/github.com/olereon/automaton/downloads/demo_enhanced",
        use_descriptive_naming=True,
        unique_id="demo_test",
        naming_format="{media_type}_{creation_date}_{unique_id}",
        date_format="%Y-%m-%d-%H-%M-%S",
        max_downloads=3  # Small demo
    )
    
    print(f"📋 Configuration:")
    print(f"   • Descriptive Naming: {config.use_descriptive_naming}")
    print(f"   • Unique ID: {config.unique_id}")
    print(f"   • Format: {config.naming_format}")
    print(f"   • Date Format: {config.date_format}")
    print(f"   • Downloads Folder: {config.downloads_folder}")
    print()
    
    manager = GenerationDownloadManager(config)
    
    print("🎯 System Ready!")
    print("📝 Example filenames that would be generated:")
    
    # Show examples
    namer = EnhancedFileNamer(config)
    examples = [
        ("video.mp4", "24 Aug 2025 14:35:22"),
        ("image.png", "24 Aug 2025 15:22:11"), 
        ("audio.mp3", "24 Aug 2025 16:45:33")
    ]
    
    for filename, date in examples:
        result = namer.generate_filename(Path(filename), creation_date=date)
        print(f"   • {filename} → {result}")

if __name__ == "__main__":
    test_file_naming_logic()
    test_media_type_detection() 
    test_date_parsing()
    asyncio.run(demo_full_system())