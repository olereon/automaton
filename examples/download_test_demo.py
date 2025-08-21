#!/usr/bin/env python3
"""
Download Test Demonstration

This script demonstrates the enhanced download functionality with proper file management
and download location control. It tests both basic and enhanced download features.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
from utils.download_manager import create_download_manager, DownloadConfig


async def test_download_functionality():
    """Test the enhanced download functionality"""
    print("🔽 Download Functionality Test")
    print("=" * 50)
    
    # Create test download configuration
    test_download_config = {
        "name": "Download Test",
        "url": "https://file-examples.com/storage/fe68c1d2b1ad066fa3b4c5b/2017/10/file_example_JPG_100kB.jpg",
        "headless": False,  # Show browser for demonstration
        "viewport": {"width": 1280, "height": 720},
        "actions": [
            {
                "type": "download_file",
                "selector": "body",  # Clicking anywhere will trigger download for direct links
                "value": "test_image.jpg",  # Optional: specify filename
                "timeout": 30000,
                "description": "Download test image file"
            }
        ]
    }
    
    # Save test config
    test_config_dir = Path("examples/download_tests")
    test_config_dir.mkdir(exist_ok=True)
    config_file = test_config_dir / "download_test.json"
    
    with open(config_file, "w") as f:
        json.dump(test_download_config, f, indent=2)
    
    print(f"Test config created: {config_file}")
    
    # Test 1: Test download manager directly
    print("\n📁 Testing Download Manager Directly")
    print("-" * 40)
    
    try:
        download_manager = create_download_manager(
            base_path="/home/olereon/Downloads/automaton_vids",
            organize_by_date=True,
            organize_by_type=True
        )
        
        print(f"✅ Download manager created")
        print(f"📂 Download path: {download_manager.config.base_download_path}")
        print(f"📅 Organize by date: {download_manager.config.organize_by_date}")
        print(f"📋 Organize by type: {download_manager.config.organize_by_type}")
        
    except Exception as e:
        print(f"❌ Download manager test failed: {e}")
        return
    
    # Test 2: Test automation with download
    print("\n🤖 Testing Automation with Enhanced Downloads")
    print("-" * 50)
    
    try:
        # Load the test config
        from core.engine import AutomationSequenceBuilder
        
        config = AutomationSequenceBuilder.from_file(str(config_file))
        engine = WebAutomationEngine(config)
        
        print("🚀 Starting automation with download test...")
        
        # Run the automation
        results = await engine.run_automation()
        
        print("\n📊 Automation Results:")
        print(f"✅ Success: {results.get('success', False)}")
        print(f"📈 Actions completed: {results.get('actions_completed', 0)}")
        print(f"📋 Total actions: {results.get('total_actions', 0)}")
        
        # Check download results
        if hasattr(engine, 'download_manager') and engine.download_manager:
            summary = engine.download_manager.get_downloads_summary()
            print(f"\n📥 Download Summary:")
            print(f"   Total downloads: {summary['total_downloads']}")
            print(f"   Completed: {summary['completed']}")
            print(f"   Failed: {summary['failed']}")
            print(f"   Total size: {summary['total_size_mb']} MB")
            print(f"   Download directory: {summary['download_directory']}")
            
            for download in summary['downloads']:
                print(f"   📄 {download['filename']}")
                print(f"      └─ Path: {download['file_path']}")
                print(f"      └─ Size: {download['size_mb']} MB")
                print(f"      └─ Status: {download['status']}")
        
        print("\n✅ Download test completed successfully!")
        
    except Exception as e:
        print(f"❌ Automation test failed: {e}")
        import traceback
        traceback.print_exc()


async def create_sample_download_config():
    """Create a sample configuration file for download testing"""
    print("\n📝 Creating Sample Download Configuration")
    print("-" * 45)
    
    # Sample configuration with multiple download actions
    sample_config = {
        "name": "Video Generation Download Automation",
        "url": "https://your-video-generation-site.com",
        "headless": False,
        "viewport": {"width": 2560, "height": 1600},
        "actions": [
            {
                "type": "wait_for_element",
                "selector": "#login-form",
                "timeout": 10000,
                "description": "Wait for login form"
            },
            {
                "type": "input_text",
                "selector": "#username",
                "value": "your_username",
                "description": "Enter username"
            },
            {
                "type": "input_text",
                "selector": "#password",
                "value": "your_password",
                "description": "Enter password"
            },
            {
                "type": "click_button",
                "selector": "#login-button",
                "description": "Click login"
            },
            {
                "type": "wait_for_element",
                "selector": "#video-list",
                "timeout": 15000,
                "description": "Wait for video list to load"
            },
            {
                "type": "check_element",
                "selector": ".video-item .status",
                "value": "Completed",
                "description": "Check if video is completed"
            },
            {
                "type": "download_file",
                "selector": ".video-item .download-button",
                "value": "generated_video.mp4",
                "timeout": 60000,
                "description": "Download completed video"
            },
            {
                "type": "log_message",
                "value": {
                    "message": "Video download completed successfully",
                    "log_file": "logs/download_automation.log"
                },
                "description": "Log download completion"
            }
        ]
    }
    
    # Save sample config
    sample_dir = Path("examples/download_configs")
    sample_dir.mkdir(exist_ok=True)
    sample_file = sample_dir / "video_download_automation.json"
    
    with open(sample_file, "w") as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"✅ Sample configuration created: {sample_file}")
    print("\n💡 To use this configuration:")
    print(f"   1. Edit the URL and selectors for your specific site")
    print(f"   2. Update credentials (use credential manager for security)")
    print(f"   3. Run: python automaton-cli.py run -c {sample_file}")
    
    return sample_file


async def show_download_directory_info():
    """Show information about download directories"""
    print("\n📁 Download Directory Information")
    print("-" * 35)
    
    download_dirs = [
        "/home/olereon/Downloads/automaton_vids",
        "downloads",  # Project local downloads
        "/tmp/automaton_downloads"  # Temporary downloads
    ]
    
    for dir_path in download_dirs:
        path = Path(dir_path)
        if path.exists():
            try:
                files = list(path.glob("**/*"))
                size = sum(f.stat().st_size for f in files if f.is_file())
                size_mb = size / (1024 * 1024)
                
                print(f"📂 {dir_path}")
                print(f"   └─ Files: {len([f for f in files if f.is_file()])}")
                print(f"   └─ Size: {size_mb:.2f} MB")
                print(f"   └─ Last modified: {datetime.fromtimestamp(path.stat().st_mtime)}")
            except Exception as e:
                print(f"📂 {dir_path}: Error reading - {e}")
        else:
            print(f"📂 {dir_path}: Does not exist")


async def main():
    """Main demonstration function"""
    print("🎬 Enhanced Download System Demonstration")
    print("=" * 60)
    
    print("\nThis demonstration shows the enhanced download management system")
    print("that properly handles file downloads with organized storage.")
    
    try:
        # Show download directory info
        await show_download_directory_info()
        
        # Create sample configuration
        await create_sample_download_config()
        
        # Test download functionality
        test_choice = input("\n❓ Would you like to run the download test? (y/n): ").strip().lower()
        if test_choice == 'y':
            await test_download_functionality()
        
        print("\n📋 Download System Features:")
        print("   ✅ Proper file organization by date/type")
        print("   ✅ Configurable download paths")
        print("   ✅ Download completion detection")
        print("   ✅ File integrity verification")
        print("   ✅ Comprehensive download logging")
        print("   ✅ Automatic duplicate handling")
        print("   ✅ Fallback to basic download method")
        
        print("\n💡 Key Benefits:")
        print("   • Downloads go to /home/olereon/Downloads/automaton_vids")
        print("   • Files are organized by date (YYYY-MM-DD folders)")
        print("   • Can organize by file type (videos, images, etc.)")
        print("   • Automatic duplicate filename resolution")
        print("   • Complete download tracking and logging")
        print("   • Proper error handling and recovery")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())