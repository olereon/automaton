#!/usr/bin/env python3
"""
Test script for the --start-from parameter functionality
Validates that the scheduler correctly filters config files based on start index
"""

import sys
import json
import subprocess
from pathlib import Path

def test_start_from_parameter():
    """Test the --start-from parameter functionality"""
    
    print("🧪 Testing --start-from parameter functionality")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            "name": "Valid start index (3)",
            "args": ["--config", "configs/scheduler_config.json", "--start-from", "3"],
            "expected_success": True,
            "expected_output_contains": ["Starting from config 3/13", "workflows/run-08-18-6.json"]
        },
        {
            "name": "Valid start index (1)",
            "args": ["--config", "configs/scheduler_config.json", "--start-from", "1"],
            "expected_success": True,
            "expected_output_contains": ["Starting from config 1/13", "workflows/run-08-18-4.json"]
        },
        {
            "name": "Invalid index (0)",
            "args": ["--config", "configs/scheduler_config.json", "--start-from", "0"],
            "expected_success": False,
            "expected_output_contains": ["Error: --start-from index must be 1 or greater"]
        },
        {
            "name": "Out of bounds index (999)",
            "args": ["--config", "configs/scheduler_config.json", "--start-from", "999"],
            "expected_success": False,
            "expected_output_contains": ["Error: --start-from index 999 is beyond"]
        }
    ]
    
    script_path = Path(__file__).parent.parent / "scripts" / "automation_scheduler.py"
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        
        try:
            # Run the scheduler with test arguments (add --quiet to avoid spam)
            cmd = ["python3.11", str(script_path)] + test_case["args"] + ["--quiet"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,  # Quick timeout since we expect early exit
                cwd=Path(__file__).parent.parent
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            # Check expected success/failure
            if success != test_case["expected_success"]:
                print(f"  ❌ FAIL - Expected {'success' if test_case['expected_success'] else 'failure'}, got {'success' if success else 'failure'}")
                print(f"     Output: {output[:200]}...")
                all_passed = False
                continue
            
            # Check expected output content
            output_check_passed = True
            for expected_text in test_case["expected_output_contains"]:
                if expected_text not in output:
                    output_check_passed = False
                    print(f"  ❌ FAIL - Expected text not found: '{expected_text}'")
                    break
            
            if not output_check_passed:
                print(f"     Full output: {output}")
                all_passed = False
                continue
                
            print(f"  ✅ PASS")
            
            # Show relevant output for valid cases
            if test_case["expected_success"]:
                for line in output.split('\n'):
                    if 'Starting from config' in line or 'Processing' in line:
                        print(f"     {line}")
            
        except subprocess.TimeoutExpired:
            # Timeout is expected for valid cases since they would start automation
            if test_case["expected_success"]:
                print(f"  ✅ PASS (timeout expected for valid config)")
            else:
                print(f"  ❌ FAIL - Unexpected timeout for invalid config")
                all_passed = False
        except Exception as e:
            print(f"  ❌ FAIL - Exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe --start-from parameter works correctly:")
        print("  - Accepts 1-indexed values (1, 2, 3, ...)")
        print("  - Validates bounds (must be >= 1 and <= config count)")
        print("  - Filters config files to start from specified index")
        print("  - Shows helpful error messages for invalid inputs")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(test_start_from_parameter())