#!/usr/bin/env python3
"""
Test script to compare landmark-based vs legacy metadata extraction.
Run this alongside generation_download_demo.py to see the differences.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig

async def compare_extraction_methods():
    """Compare landmark vs legacy extraction methods"""
    
    print("🔍 LANDMARK vs LEGACY Metadata Extraction Comparison")
    print("=" * 60)
    
    # Load the demo config
    config_path = Path(__file__).parent / "generation_download_config.json"
    with open(config_path, 'r') as f:
        config_data = json.load(f)
    
    start_action = None
    for action in config_data['actions']:
        if action['type'] == 'start_generation_downloads':
            start_action = action['value']
            break
    
    if not start_action:
        print("❌ No generation download action found in config")
        return
    
    # Test 1: Legacy extraction (baseline)
    print("\n🔧 Testing LEGACY extraction method...")
    legacy_config = GenerationDownloadConfig(
        # Disable landmark extraction
        landmark_extraction_enabled=False,
        landmark_fallback_enabled=False,
        
        # Use existing settings
        use_descriptive_naming=start_action.get('use_descriptive_naming', True),
        unique_id="legacy_test",
        naming_format=start_action.get('naming_format', "{media_type}_{creation_date}_{unique_id}"),
        date_format=start_action.get('date_format', "%Y-%m-%d-%H-%M-%S"),
        
        # Legacy selectors
        generation_date_selector=start_action.get('generation_date_selector', ''),
        prompt_selector=start_action.get('prompt_selector', ''),
        
        # Debug
        enable_debug_logging=True,
        debug_log_file="logs/legacy_extraction_test.log"
    )
    
    legacy_manager = GenerationDownloadManager(legacy_config)
    print(f"✅ Legacy manager created - Debug: {legacy_config.debug_log_file}")
    
    # Test 2: Landmark extraction (new method)
    print("\n🚀 Testing NEW LANDMARK extraction method...")
    landmark_config = GenerationDownloadConfig(
        # Enable landmark extraction
        landmark_extraction_enabled=True,
        landmark_fallback_enabled=True,
        landmark_validation_strict=False,
        
        # Landmark settings
        image_to_video_text=start_action.get('image_to_video_text', 'Image to video'),
        creation_time_text=start_action.get('creation_time_text', 'Creation Time'),
        
        # Use same settings for comparison
        use_descriptive_naming=start_action.get('use_descriptive_naming', True),
        unique_id="landmark_test",
        naming_format=start_action.get('naming_format', "{media_type}_{creation_date}_{unique_id}"),
        date_format=start_action.get('date_format', "%Y-%m-%d-%H-%M-%S"),
        
        # Debug
        enable_debug_logging=True,
        debug_log_file="logs/landmark_extraction_test.log"
    )
    
    landmark_manager = GenerationDownloadManager(landmark_config)
    print(f"✅ Landmark manager created - Debug: {landmark_config.debug_log_file}")
    
    print("\n📋 Configuration Comparison:")
    print(f"  🔧 Legacy method:")
    print(f"     • Landmark extraction: {legacy_config.landmark_extraction_enabled}")
    print(f"     • Unique ID: {legacy_config.unique_id}")
    print(f"     • Debug log: {legacy_config.debug_log_file}")
    
    print(f"  🚀 Landmark method:")
    print(f"     • Landmark extraction: {landmark_config.landmark_extraction_enabled}")
    print(f"     • Image to video text: '{landmark_config.image_to_video_text}'")
    print(f"     • Creation time text: '{landmark_config.creation_time_text}'")
    print(f"     • Unique ID: {landmark_config.unique_id}")
    print(f"     • Debug log: {landmark_config.debug_log_file}")
    
    print("\n🎯 Ready for Testing!")
    print("📌 Instructions:")
    print("  1. Run the generation_download_demo.py in another terminal")
    print("  2. The demo will use the NEW landmark-based extraction")
    print("  3. Check the debug logs to compare extraction methods:")
    print(f"     • Legacy log: {legacy_config.debug_log_file}")
    print(f"     • Landmark log: {landmark_config.debug_log_file}")
    print("  4. Compare the extracted metadata and file naming")
    
    print("\n📊 Key Differences to Look For:")
    print("  ✅ Landmark method should:")
    print("     • Find correct 'Image to video' container")
    print("     • Extract accurate date/time per thumbnail")
    print("     • Generate unique file names per generation")
    print("     • Show improved success rates")
    print("  ❌ Legacy method typically:")
    print("     • Uses fragile CSS selectors")
    print("     • May extract wrong dates (same for all files)")
    print("     • Less reliable element detection")
    
    return True

if __name__ == "__main__":
    asyncio.run(compare_extraction_methods())