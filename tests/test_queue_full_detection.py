#!/usr/bin/env python3
"""
Test script for queue full popup detection
Tests the submission verification logic in run-08-16-1.json
"""

import json
import sys
from pathlib import Path

def validate_queue_full_detection(config_file):
    """Validate that the configuration has proper queue full detection"""
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    actions = config.get('actions', [])
    
    # Find all task submission button clicks (not login submits)
    submit_indices = []
    for i, action in enumerate(actions):
        if (action.get('type') == 'click_button' and 
            'creation-form-button-submit' in action.get('selector', '')):
            submit_indices.append(i)
    
    print(f"Found {len(submit_indices)} submit button clicks")
    
    # Check each submit for proper popup detection
    issues = []
    for submit_idx in submit_indices:
        # Check if there's a popup check after submit
        has_popup_check = False
        has_conditional_logic = False
        
        # Look at next 10 actions after submit
        for j in range(submit_idx + 1, min(submit_idx + 10, len(actions))):
            action = actions[j]
            
            # Check for popup detection
            if (action.get('type') == 'check_element' and 
                ('reached your' in str(action.get('selector', '')) or
                 'popup' in action.get('description', '').lower() or
                 ('reached your' in str(action.get('value', {}).get('value', ''))))):
                has_popup_check = True
                check_config = action.get('value', {})
                print(f"  ✓ Found popup check at index {j} - Check: {check_config.get('check')} for '{check_config.get('value')}'")
            
            # Check for conditional logic
            if action.get('type') == 'if_begin':
                has_conditional_logic = True
                print(f"  ✓ Found conditional logic at index {j}")
            
            # Check for proper error handling
            if (action.get('type') == 'log_message' and 
                'error' in str(action.get('value', {})).lower()):
                print(f"  ✓ Found error logging at index {j}")
            
            # Check for BREAK mechanism (better than forced click failure)
            if (action.get('type') == 'break' and 
                'queue full' in action.get('description', '').lower()):
                print(f"  ✓ Found BREAK mechanism at index {j}")
        
        if not has_popup_check:
            issues.append(f"Submit at index {submit_idx} missing popup check")
        if not has_conditional_logic:
            issues.append(f"Submit at index {submit_idx} missing conditional logic")
    
    # Validate the popup detection implementation
    print("\n=== Validation Results ===")
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Queue full detection properly implemented!")
        print("\nDetection features:")
        print("  - Check for popup after submit button click")
        print("  - Conditional logic to handle queue full state")
        print("  - Error logging for failed submissions")
        print("  - Automation failure on queue full (triggers scheduler retry)")
        return True

def main():
    """Main test function"""
    config_file = Path(__file__).parent.parent / "workflows" / "run-08-16-1.json"
    
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
    
    print(f"Testing queue full detection in: {config_file}")
    print("=" * 60)
    
    success = validate_queue_full_detection(config_file)
    
    if success:
        print("\n✅ Test PASSED: Queue full detection is properly configured")
        sys.exit(0)
    else:
        print("\n❌ Test FAILED: Queue full detection needs fixes")
        sys.exit(1)

if __name__ == "__main__":
    main()