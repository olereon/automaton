#!/usr/bin/env python3
"""
Fast Generation Downloader
Optimized automation script for quick generation downloads with duplicate detection.
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import re

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from src directory
try:
    from src.core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
except ImportError:
    # Alternative import path
    sys.path.insert(0, os.path.join(parent_dir, 'src'))
    from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType


class FastGenerationDownloader:
    """Optimized generation downloader with duplicate detection and fast processing"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.downloads_folder = None
        self.existing_files = set()
        
    def scan_existing_files(self):
        """Scan downloads folder for existing files and extract creation times"""
        if not self.downloads_folder or not os.path.exists(self.downloads_folder):
            print("📁 Downloads folder not found or not set")
            return
        
        print(f"🔍 Scanning existing files in: {self.downloads_folder}")
        
        # Pattern to match files with creation time: video_2025-08-27-02-20-06_gen_#000000001.mp4
        file_pattern = re.compile(r'video_(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})_')
        
        for file_path in Path(self.downloads_folder).glob("*.mp4"):
            match = file_pattern.search(file_path.name)
            if match:
                creation_time = match.group(1)
                self.existing_files.add(creation_time)
                print(f"   📄 Found: {file_path.name} -> {creation_time}")
        
        print(f"✅ Found {len(self.existing_files)} existing files")
        
    def check_duplicate_exists(self, creation_time: str) -> bool:
        """Check if a file with the given creation time already exists"""
        # Convert format if needed: "27 Aug 2025 02:20:06" -> "2025-08-27-02-20-06" 
        if creation_time in self.existing_files:
            return True
            
        # Try to parse different time formats
        try:
            # Parse: "27 Aug 2025 02:20:06"
            dt = datetime.strptime(creation_time, "%d %b %Y %H:%M:%S")
            formatted_time = dt.strftime("%Y-%m-%d-%H-%M-%S")
            return formatted_time in self.existing_files
        except ValueError:
            try:
                # Parse: "2025-08-27-02-20-06" 
                dt = datetime.strptime(creation_time, "%Y-%m-%d-%H-%M-%S")
                formatted_time = creation_time
                return formatted_time in self.existing_files
            except ValueError:
                print(f"⚠️ Could not parse creation time format: {creation_time}")
                return False
    
    async def run_fast_download(self):
        """Run the optimized download automation"""
        
        print("🚀 Fast Generation Downloader")
        print("=" * 60)
        
        # Load configuration
        if not self.config_path.exists():
            print(f"❌ Configuration file not found: {self.config_path}")
            return False
        
        with open(self.config_path, 'r') as f:
            config_data = json.load(f)
        
        # Extract downloads folder for duplicate checking
        for action_data in config_data['actions']:
            if action_data.get('type') == 'start_generation_downloads':
                self.downloads_folder = action_data.get('value', {}).get('downloads_folder')
                break
        
        # Scan for existing files before starting
        if self.downloads_folder:
            self.scan_existing_files()
        
        # Convert to AutomationConfig
        actions = []
        for action_data in config_data['actions']:
            action = Action(
                type=ActionType(action_data['type']),
                selector=action_data.get('selector'),
                value=action_data.get('value'),
                timeout=action_data.get('timeout', 10000),
                description=action_data.get('description')
            )
            actions.append(action)
        
        config = AutomationConfig(
            name=config_data['name'],
            url=config_data['url'],
            actions=actions,
            headless=config_data.get('headless', False),
            viewport=config_data.get('viewport', {"width": 2560, "height": 1440})
        )
        
        # Create automation engine
        engine = WebAutomationEngine(config)
        
        try:
            print(f"📋 Automation: {config.name}")
            print(f"🌐 URL: {config.url}")
            print(f"🎬 Actions: {len(config.actions)}")
            print(f"⚡ Optimized for fast downloads with duplicate detection")
            print()
            
            # Run automation
            print("🔥 Starting optimized automation...")
            start_time = datetime.now()
            
            results = await engine.run_automation()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n📊 Results (Duration: {duration:.2f}s):")
            print(f"✅ Success: {results['success']}")
            print(f"⚡ Actions completed: {results['actions_completed']}/{results['total_actions']}")
            
            if results.get('errors'):
                print(f"❌ Errors: {len(results['errors'])}")
                for i, error in enumerate(results['errors'][:3], 1):
                    print(f"   {i}. {error}")
            
            # Check for generation-specific results
            generation_results = results.get('outputs', {})
            if generation_results:
                print("\n🎯 Generation Download Results:")
                for key, value in generation_results.items():
                    if isinstance(value, dict) and 'downloads_completed' in value:
                        downloads_completed = value['downloads_completed']
                        print(f"📥 Downloads completed: {downloads_completed}")
                        if value.get('manager_status'):
                            status = value['manager_status']
                            print(f"📁 Downloads folder: {status.get('downloads_folder', 'Unknown')}")
                            print(f"📝 Log file: {status.get('log_file_path', 'Unknown')}")
                        
                        # Performance metrics
                        if downloads_completed > 0:
                            avg_time = duration / downloads_completed
                            print(f"⚡ Average time per download: {avg_time:.2f}s")
            
            print(f"\n🎉 Fast download completed in {duration:.2f}s!")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during automation: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            # Cleanup
            try:
                await engine.cleanup()
                print("🧹 Cleanup completed")
            except:
                pass


async def main():
    """Main entry point"""
    
    # Get config path from command line or use default
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        # Default to the fast config in the same directory
        config_path = os.path.join(os.path.dirname(__file__), "fast_generation_config.json")
    
    downloader = FastGenerationDownloader(config_path)
    
    try:
        success = await downloader.run_fast_download()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Download interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)