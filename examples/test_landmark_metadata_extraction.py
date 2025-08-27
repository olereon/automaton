#!/usr/bin/env python3
"""
Test script for the new landmark-based metadata extraction system.
This script tests the "Image to video" landmark strategy for extracting metadata.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.engine import WebAutomationEngine, AutomationConfig
from core.controller import AutomationController
from utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig

async def test_landmark_extraction():
    """Test the landmark-based metadata extraction"""
    print("🧪 Testing New Landmark-Based Metadata Extraction")
    print("=" * 60)
    
    # Create controller for stop functionality
    controller = AutomationController()
    controller.start()
    
    try:
        # Configure the generation download system with landmark extraction
        download_config = GenerationDownloadConfig(
            # Enable new landmark-based extraction
            landmark_extraction_enabled=True,
            landmark_fallback_enabled=True,
            landmark_validation_strict=False,
            
            # Landmark configuration
            image_to_video_text="Image to video",
            creation_time_text="Creation Time",
            
            # Enhanced naming with metadata
            use_descriptive_naming=True,
            unique_id="landmarkTest",
            naming_format="{media_type}_{creation_date}_{unique_id}",
            date_format="%Y-%m-%d-%H-%M-%S",
            
            # Download settings
            download_directory="/home/olereon/workspace/github.com/olereon/automaton/downloads/landmark_test",
            max_downloads=5,
            
            # Debug logging
            enable_debug_logging=True,
            debug_log_file="logs/landmark_extraction_test.log"
        )
        
        # Create download manager
        download_manager = GenerationDownloadManager(download_config)
        
        # Create automation engine
        config = AutomationConfig(
            name="Landmark Metadata Extraction Test",
            url="https://wan.video/generate",
            headless=False,  # Show browser for testing
            viewport={"width": 2560, "height": 1440}
        )
        
        engine = WebAutomationEngine(config, controller=controller)
        engine.set_download_manager(download_manager)
        
        print("✅ Test setup completed")
        print(f"📁 Download directory: {download_config.download_directory}")
        print(f"📝 Debug log: {download_config.debug_log_file}")
        print(f"🎯 Landmark text: '{download_config.image_to_video_text}'")
        print(f"⏰ Date format: {download_config.date_format}")
        
        # Launch browser
        print("\n🌐 Launching browser...")
        await engine._setup_browser()
        
        print("📄 Navigate to the generation page manually and:")
        print("  1. Login to your account")
        print("  2. Go to a page with completed generations")
        print("  3. Click on a generation thumbnail to select it")
        print("  4. Press Enter in this terminal to start extraction test")
        
        input("Press Enter when ready to test extraction...")
        
        # Test metadata extraction
        print("\n🔍 Testing metadata extraction...")
        
        # Test landmark-based extraction
        metadata = await download_manager.extract_metadata_from_page(engine.page)
        
        if metadata:
            print("\n✅ LANDMARK EXTRACTION SUCCESS!")
            print("📊 Extracted Metadata:")
            for key, value in metadata.items():
                print(f"  • {key}: {value}")
            
            # Test filename generation
            test_filename = download_manager.generate_filename(
                Path("test.mp4"), 
                creation_date=metadata.get('generation_date'),
                sequence_number=1
            )
            print(f"\n📁 Generated filename: {test_filename}")
            
        else:
            print("❌ EXTRACTION FAILED - No metadata extracted")
            print("🔍 Check debug logs for details")
        
        # Show debug information
        if hasattr(download_manager, 'debug_logger') and download_manager.debug_logger:
            debug_entries = download_manager.debug_logger.get_debug_summary()
            print(f"\n📋 Debug entries: {len(debug_entries)}")
            
            if debug_entries:
                latest_entry = debug_entries[-1]
                print("🔧 Latest extraction attempt:")
                for key, value in latest_entry.items():
                    if isinstance(value, (str, int, float, bool)):
                        print(f"  • {key}: {value}")
        
        print("\n🎮 Browser will stay open for manual testing")
        print("   Use Ctrl+W to pause/resume, Ctrl+T to stop")
        print("   Click on different thumbnails and press 'e' + Enter to extract metadata")
        
        # Interactive testing loop
        while True:
            try:
                user_input = input("\nOptions: (e)xtract, (q)uit: ").strip().lower()
                
                if user_input == 'q':
                    break
                elif user_input == 'e':
                    print("🔍 Extracting metadata from current page...")
                    metadata = await download_manager.extract_metadata_from_page(engine.page)
                    
                    if metadata:
                        print("✅ Extraction successful:")
                        for key, value in metadata.items():
                            print(f"  • {key}: {value}")
                    else:
                        print("❌ Extraction failed")
                else:
                    print("Invalid option. Use 'e' to extract or 'q' to quit.")
                    
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if 'engine' in locals():
            try:
                await engine.cleanup()
            except:
                pass
        controller.stop()
        print("✅ Test cleanup completed")

if __name__ == "__main__":
    asyncio.run(test_landmark_extraction())