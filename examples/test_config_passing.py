#!/usr/bin/env python3.11
"""
Test script to verify configuration passing is working correctly
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.generation_download_manager import GenerationDownloadConfig

def test_config_passing():
    """Test that configuration is passed correctly"""
    
    print("🧪 Testing Configuration Passing")
    print("=" * 40)
    
    # Load the main config file
    config_path = project_root / "examples" / "generation_download_config.json"
    
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    # Extract the start_generation_downloads action
    download_action = None
    for action in config_data['actions']:
        if action['type'] == 'start_generation_downloads':
            download_action = action
            break
    
    if not download_action:
        print("❌ No start_generation_downloads action found!")
        return
    
    action_value = download_action.get('value', {})
    
    print("📋 Configuration in JSON file:")
    print(f"   • use_descriptive_naming: {action_value.get('use_descriptive_naming', 'NOT SET')}")
    print(f"   • unique_id: {action_value.get('unique_id', 'NOT SET')}")
    print(f"   • naming_format: {action_value.get('naming_format', 'NOT SET')}")
    print(f"   • date_format: {action_value.get('date_format', 'NOT SET')}")
    print()
    
    # Test creating GenerationDownloadConfig with these values
    try:
        config = GenerationDownloadConfig(
            downloads_folder=action_value.get('downloads_folder', '/tmp'),
            logs_folder=action_value.get('logs_folder', '/tmp'),
            max_downloads=action_value.get('max_downloads', 1),
            
            # Enhanced naming configuration
            use_descriptive_naming=action_value.get('use_descriptive_naming', True),
            unique_id=action_value.get('unique_id', 'gen'),
            naming_format=action_value.get('naming_format', '{media_type}_{creation_date}_{unique_id}'),
            date_format=action_value.get('date_format', '%Y-%m-%d-%H-%M-%S'),
        )
        
        print("✅ GenerationDownloadConfig created successfully!")
        print(f"   • use_descriptive_naming: {config.use_descriptive_naming}")
        print(f"   • unique_id: {config.unique_id}")
        print(f"   • naming_format: {config.naming_format}")
        print(f"   • date_format: {config.date_format}")
        print()
        
        # Test the file namer
        from src.utils.generation_download_manager import EnhancedFileNamer
        
        namer = EnhancedFileNamer(config)
        test_filename = namer.generate_filename(
            Path("test_video.mp4"),
            creation_date="25 Aug 2025 14:35:22"
        )
        
        print("🎯 Test filename generation:")
        print(f"   Input: test_video.mp4, date: '25 Aug 2025 14:35:22'")
        print(f"   Output: {test_filename}")
        
        if "initialT" in test_filename:
            print("   ✅ Unique ID 'initialT' found in filename!")
        else:
            print("   ❌ Unique ID 'initialT' NOT found in filename!")
            print(f"   Expected to contain 'initialT', got: {test_filename}")
        
        # Test date parsing
        parsed_date = namer.parse_creation_date("25 Aug 2025 14:35:22")
        print(f"   Parsed date: {parsed_date}")
        
        if "2025-08-25-14-35-22" in parsed_date:
            print("   ✅ Date parsing working correctly!")
        else:
            print("   ⚠️  Date parsing might have issues")
            
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_passing()