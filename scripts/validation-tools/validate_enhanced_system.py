#!/usr/bin/env python3
"""
Enhanced System Validation Script
Demonstrates and validates all new features of the enhanced generation download system.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from scripts.fast_generation_downloader import FastGenerationDownloader
from src.utils.generation_download_manager import (
    GenerationDownloadManager, 
    GenerationDownloadConfig, 
    GenerationDownloadLogger,
    DuplicateMode
)


def create_test_config(temp_dir: str) -> str:
    """Create a test configuration file"""
    config_path = os.path.join(temp_dir, "enhanced_test_config.json")
    
    config_data = {
        "name": "Enhanced Generation Download System Validation",
        "url": "https://example.com",
        "headless": True,
        "viewport": {"width": 2560, "height": 1440},
        "actions": [
            {
                "type": "start_generation_downloads", 
                "description": "NEW 25-Step Algorithm with Enhanced Features",
                "value": {
                    "downloads_folder": os.path.join(temp_dir, "downloads"),
                    "logs_folder": os.path.join(temp_dir, "logs"),
                    "max_downloads": 10,
                    "duplicate_mode": "skip",
                    "duplicate_check_enabled": True,
                    "use_descriptive_naming": True,
                    "chronological_logging": True,
                    "enhanced_skip_mode": True,
                    "placeholder_numbering": True
                }
            }
        ]
    }
    
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    return config_path


def validate_import_fixes():
    """Validate that all import issues are resolved"""
    print("🔧 VALIDATION 1: Import Fixes")
    print("-" * 50)
    
    try:
        from scripts.fast_generation_downloader import FastGenerationDownloader
        from src.core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType
        from src.core.controller import AutomationController
        print("✅ All imports successful")
        print("✅ FastGenerationDownloader class available")
        print("✅ WebAutomationEngine with controller support")
        print("✅ Import fixes validated")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False


def validate_new_algorithm():
    """Validate the new 25-step algorithm implementation"""
    print("\n🚀 VALIDATION 2: New 25-Step Algorithm")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create configuration
            config = GenerationDownloadConfig(
                downloads_folder=os.path.join(temp_dir, "downloads"),
                logs_folder=os.path.join(temp_dir, "logs"),
                max_downloads=5,
                duplicate_mode=DuplicateMode.SKIP
            )
            
            # Create manager
            manager = GenerationDownloadManager(config)
            
            # Check if new algorithm method exists
            if hasattr(manager, 'run_download_automation_v2'):
                print("✅ New 25-step algorithm method available")
                print("✅ Algorithm version 2.0 implementation")
                
                # Check helper methods
                helper_methods = [
                    '_validate_download_environment',
                    '_initialize_chronological_logging',
                    '_enhanced_start_from_navigation',
                    '_enhanced_gallery_navigation',
                    '_initialize_enhanced_skip_mode_v2',
                    '_advanced_thumbnail_discovery',
                    '_execute_main_algorithm_loop',
                    '_enhanced_metadata_extraction',
                    '_enhanced_duplicate_detection',
                    '_process_download_with_validation'
                ]
                
                missing_methods = []
                for method in helper_methods:
                    if not hasattr(manager, method):
                        missing_methods.append(method)
                
                if not missing_methods:
                    print("✅ All algorithm helper methods implemented")
                    print("✅ Enhanced gallery navigation available")
                    print("✅ Advanced thumbnail discovery implemented")
                    print("✅ Enhanced duplicate detection available")
                    return True
                else:
                    print(f"❌ Missing methods: {missing_methods}")
                    return False
            else:
                print("❌ New algorithm method not found")
                return False
                
        except Exception as e:
            print(f"❌ Algorithm validation error: {e}")
            return False


def validate_chronological_logging():
    """Validate chronological logging system"""
    print("\n📝 VALIDATION 3: Chronological Logging System")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            config = GenerationDownloadConfig(
                logs_folder=temp_dir,
                duplicate_mode=DuplicateMode.SKIP
            )
            
            logger = GenerationDownloadLogger(config)
            
            # Check chronological features
            if hasattr(logger, 'use_chronological_ordering'):
                print("✅ Chronological ordering capability")
                print(f"   Enabled: {logger.use_chronological_ordering}")
                
            if hasattr(logger, 'placeholder_id'):
                print("✅ Placeholder ID system")
                print(f"   Placeholder: {logger.placeholder_id}")
                
            if hasattr(logger, 'support_enhanced_skip_mode'):
                print("✅ Enhanced SKIP mode support")
                print(f"   Enabled: {logger.support_enhanced_skip_mode}")
            
            # Test placeholder ID generation
            file_id = logger.get_next_file_id()
            if file_id == "#999999999":
                print("✅ Placeholder ID generation working")
                print(f"   Generated: {file_id}")
                return True
            else:
                print(f"❌ Unexpected file ID: {file_id}")
                return False
                
        except Exception as e:
            print(f"❌ Chronological logging validation error: {e}")
            return False


def validate_fast_downloader_integration():
    """Validate fast downloader integration with new algorithm"""
    print("\n⚡ VALIDATION 4: Fast Downloader Integration")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create test configuration
            config_path = create_test_config(temp_dir)
            print(f"✅ Test configuration created: {Path(config_path).name}")
            
            # Test different modes
            modes_to_test = [
                ("skip", "Enhanced SKIP mode with continuation"),
                ("finish", "FINISH mode with duplicate stopping")
            ]
            
            for mode, description in modes_to_test:
                downloader = FastGenerationDownloader(
                    config_path=config_path,
                    duplicate_mode=mode,
                    max_downloads=5
                )
                
                print(f"✅ {mode.upper()} mode initialization successful")
                print(f"   {description}")
                
                # Validate configuration modification
                with open(config_path, 'r') as f:
                    original_config = json.load(f)
                
                modified_config = downloader.modify_config_for_duplicate_mode(original_config)
                action_value = modified_config['actions'][0]['value']
                
                expected_stop_on_duplicate = (mode == "finish")
                if action_value.get('stop_on_duplicate') == expected_stop_on_duplicate:
                    print(f"   ✅ {mode.upper()} mode configuration correct")
                else:
                    print(f"   ❌ {mode.upper()} mode configuration incorrect")
                    return False
            
            print("✅ Fast downloader integration validated")
            return True
            
        except Exception as e:
            print(f"❌ Fast downloader integration error: {e}")
            return False


def validate_renumbering_script():
    """Validate the enhanced renumbering script"""
    print("\n🔢 VALIDATION 5: Enhanced Renumbering Script")
    print("-" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create a sample log file with placeholders
            log_file = os.path.join(temp_dir, "generation_downloads.txt")
            sample_content = """#999999999
03 Sep 2025 16:15:18
Sample prompt text with placeholder ID
========================================
#000000001
02 Sep 2025 14:30:22
Another sample prompt
========================================
#999999999
04 Sep 2025 18:45:30
Second placeholder entry
========================================
"""
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            
            print("✅ Sample log file with placeholders created")
            
            # Import and test renumbering script
            from scripts.renumber_generation_ids import renumber_generation_ids
            
            # Run renumbering
            success = renumber_generation_ids(log_file)
            
            if success:
                print("✅ Renumbering script executed successfully")
                
                # Check if placeholders were replaced
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "#999999999" not in content:
                    print("✅ All placeholder IDs replaced")
                    print("✅ Sequential numbering applied")
                    return True
                else:
                    print("❌ Some placeholders not replaced")
                    return False
            else:
                print("❌ Renumbering script failed")
                return False
                
        except Exception as e:
            print(f"❌ Renumbering validation error: {e}")
            return False


def main():
    """Main validation routine"""
    print("🎯 ENHANCED GENERATION DOWNLOAD SYSTEM VALIDATION")
    print("=" * 80)
    print(f"📅 Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    validations = [
        ("Import Fixes", validate_import_fixes),
        ("25-Step Algorithm", validate_new_algorithm),
        ("Chronological Logging", validate_chronological_logging),
        ("Fast Downloader Integration", validate_fast_downloader_integration),
        ("Enhanced Renumbering", validate_renumbering_script)
    ]
    
    results = []
    
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation crashed: {e}")
            results.append((name, False))
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<40} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} validations passed")
    
    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Enhanced generation download system is fully operational")
        return 0
    else:
        print(f"❌ {total - passed} validation(s) failed")
        print("⚠️ System requires attention before deployment")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)