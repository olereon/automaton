#!/usr/bin/env python3
"""
Fast Generation Downloader
Optimized automation script for quick generation downloads with duplicate detection.
"""

import asyncio
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import re

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import from src directory
try:
    from src.core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
    from src.core.controller import AutomationController
except ImportError:
    try:
        # Alternative import path
        sys.path.insert(0, os.path.join(parent_dir, 'src'))
        from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
        from core.controller import AutomationController
    except ImportError:
        # Final fallback - direct import
        import importlib.util
        engine_spec = importlib.util.spec_from_file_location("engine", os.path.join(parent_dir, "src", "core", "engine.py"))
        engine_module = importlib.util.module_from_spec(engine_spec)
        engine_spec.loader.exec_module(engine_module)
        WebAutomationEngine = engine_module.WebAutomationEngine
        AutomationConfig = engine_module.AutomationConfig
        Action = engine_module.Action
        ActionType = engine_module.ActionType
        
        controller_spec = importlib.util.spec_from_file_location("controller", os.path.join(parent_dir, "src", "core", "controller.py"))
        controller_module = importlib.util.module_from_spec(controller_spec)
        controller_spec.loader.exec_module(controller_module)
        AutomationController = controller_module.AutomationController


class FastGenerationDownloader:
    """Optimized generation downloader with duplicate detection and fast processing"""
    
    def __init__(self, config_path: str, duplicate_mode: str = "finish", start_from: str = None, max_downloads: int = None):
        self.config_path = Path(config_path)
        self.duplicate_mode = duplicate_mode.lower()
        self.start_from = start_from
        self.max_downloads = max_downloads  # Command-line override for max downloads
        self.downloads_folder = None
        self.existing_files = set()
        
        print(f"🔄 Duplicate Mode: {self.duplicate_mode.upper()}")
        if self.duplicate_mode == "skip":
            print("   📌 Will skip duplicates and continue searching for new generations")
        else:
            print("   📌 Will stop when reaching previously downloaded content")
            
        if self.start_from:
            print(f"🎯 Start From: {self.start_from}")
            print("   📌 Will search for this generation and start downloading from the next one")
        
        if self.max_downloads:
            print(f"📊 Max Downloads: {self.max_downloads}")
            print(f"   📌 Will limit downloads to {self.max_downloads} items")
        
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
    
    def modify_config_for_duplicate_mode(self, config_data):
        """Modify configuration for duplicate handling (both SKIP and FINISH modes)"""
        print(f"⚙️ Modifying configuration for {self.duplicate_mode.upper()} mode...")
        
        # Find the start_generation_downloads action and modify it
        for action_data in config_data['actions']:
            if action_data.get('type') == 'start_generation_downloads':
                if 'value' not in action_data:
                    action_data['value'] = {}
                
                # CRITICAL: Always ensure duplicate checking is enabled
                action_data['value']['duplicate_check_enabled'] = True
                print("   ✅ Set duplicate_check_enabled = True (CRITICAL FIX)")
                
                # Add start_from parameter if specified
                if self.start_from:
                    action_data['value']['start_from'] = self.start_from
                    print(f"   🎯 Set start_from = '{self.start_from}'")
                
                # Override max_downloads if specified on command line
                if self.max_downloads is not None:
                    original_max = action_data['value'].get('max_downloads', 'not set')
                    action_data['value']['max_downloads'] = self.max_downloads
                    print(f"   📊 Override max_downloads: {original_max} → {self.max_downloads}")
                
                if self.duplicate_mode == "skip":
                    # Set SKIP mode parameters
                    action_data['value']['stop_on_duplicate'] = False
                    action_data['value']['duplicate_mode'] = 'skip'
                    action_data['value']['skip_duplicates'] = True
                    
                    print("   ✅ Set stop_on_duplicate = False")
                    print("   ✅ Set duplicate_mode = 'skip'")
                    print("   ✅ Set skip_duplicates = True")
                    
                    # Add skip mode description
                    skip_description = action_data.get('description', '') + ' [SKIP MODE: Continue past duplicates]'
                    action_data['description'] = skip_description
                    
                else:
                    # Set FINISH mode parameters (default behavior)
                    action_data['value']['stop_on_duplicate'] = True
                    action_data['value']['duplicate_mode'] = 'finish'
                    action_data['value']['skip_duplicates'] = False
                    
                    print("   ✅ Set stop_on_duplicate = True")
                    print("   ✅ Set duplicate_mode = 'finish'")
                    print("   ✅ Set skip_duplicates = False")
                    
                    # Add finish mode description
                    finish_description = action_data.get('description', '') + ' [FINISH MODE: Stop at duplicates]'
                    action_data['description'] = finish_description
                
                break
        
        return config_data
    
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
        
        # Modify configuration for duplicate mode (SKIP or FINISH) 
        config_data = self.modify_config_for_duplicate_mode(config_data)
        
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
            action_type = ActionType(action_data['type'])
            action_value = action_data.get('value')
            
            # Handle actions that require a value but might not have one in the config
            if action_type in [ActionType.CHECK_GENERATION_STATUS] and action_value is None:
                print(f"⚠️ Warning: Action {action_type.value} requires a value but none was provided. Using empty dict as default.")
                action_value = {}
            
            action = Action(
                type=action_type,
                selector=action_data.get('selector'),
                value=action_value,
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
        
        # Create automation controller and engine with stop functionality
        controller = AutomationController()
        controller.start_automation(total_actions=self.max_downloads or 50)
        engine = WebAutomationEngine(config, controller=controller)
        
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
                controller.stop_automation()
                print("🧹 Cleanup completed")
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup warning: {cleanup_error}")
                pass


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fast Generation Downloader with SKIP/FINISH mode support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config (FINISH mode)
  python fast_generation_downloader.py
  
  # Run with SKIP mode (continue past duplicates)
  python fast_generation_downloader.py --mode skip
  
  # Use custom config file with SKIP mode
  python fast_generation_downloader.py --config my_config.json --mode skip
  
  # Run with FINISH mode (stop on duplicates) - explicit
  python fast_generation_downloader.py --mode finish
  
  # Start from specific generation
  python fast_generation_downloader.py --start-from "03 Sep 2025 16:15:18"
  
  # Combine start-from with SKIP mode
  python fast_generation_downloader.py --mode skip --start-from "03 Sep 2025 16:15:18"
  
  # Limit downloads to specific number
  python fast_generation_downloader.py --max-downloads 5
  
  # Combine all options
  python fast_generation_downloader.py --config my_config.json --mode skip --max-downloads 10
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=os.path.join(os.path.dirname(__file__), "fast_generation_config.json"),
        help='Path to configuration file (default: fast_generation_config.json)'
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['skip', 'finish'],
        default='finish',
        help='Duplicate handling mode: "skip" continues past duplicates, "finish" stops on duplicates (default: finish)'
    )
    
    parser.add_argument(
        '--scan-only', '-s',
        action='store_true',
        help='Only scan existing files and exit (useful for debugging)'
    )
    
    parser.add_argument(
        '--start-from', '-f',
        type=str,
        help='Start downloads from specific datetime (format: "DD MMM YYYY HH:MM:SS", e.g., "03 Sep 2025 16:15:18")'
    )
    
    parser.add_argument(
        '--max-downloads', '-n',
        type=int,
        help='Maximum number of downloads (overrides config file value)'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    
    args = parse_arguments()
    
    print("🚀 Fast Generation Downloader")
    print("=" * 60)
    print(f"📁 Config file: {args.config}")
    print(f"🔄 Duplicate mode: {args.mode.upper()}")
    
    if args.mode == "skip":
        print("📌 SKIP mode: Will continue searching past duplicate generations")
    else:
        print("📌 FINISH mode: Will stop when reaching previously downloaded content")
        
    if args.start_from:
        print(f"🎯 Start from: {args.start_from}")
        print("📌 Will search for this generation and start downloading from the next one")
    
    if args.max_downloads:
        print(f"📊 Max downloads: {args.max_downloads}")
        print("📌 Will override config file max_downloads setting")
    
    print("=" * 60)
    
    downloader = FastGenerationDownloader(args.config, args.mode, args.start_from, args.max_downloads)
    
    # If scan-only mode, just scan and exit
    if args.scan_only:
        print("🔍 Scan-only mode: Analyzing existing files...")
        
        # Load config to get downloads folder
        if Path(args.config).exists():
            with open(args.config, 'r') as f:
                config_data = json.load(f)
            
            for action_data in config_data['actions']:
                if action_data.get('type') == 'start_generation_downloads':
                    downloader.downloads_folder = action_data.get('value', {}).get('downloads_folder')
                    break
        
        if downloader.downloads_folder:
            downloader.scan_existing_files()
            print("\n✅ Scan complete. Exiting.")
            return 0
        else:
            print("❌ Could not determine downloads folder from config")
            return 1
    
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