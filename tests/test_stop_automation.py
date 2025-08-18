#!/usr/bin/env python3
"""
Test script for stop_automation functionality
Tests that the new STOP_AUTOMATION action properly terminates automation
"""

import json
import sys
from pathlib import Path

def validate_stop_automation_implementation(config_file):
    """Validate that the configuration has proper stop_automation implementation"""
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    actions = config.get('actions', [])
    
    print(f"Validating stop_automation in {len(actions)} actions...")
    
    # Find all stop_automation actions
    stop_automation_actions = []
    for i, action in enumerate(actions):
        if action.get('type') == 'stop_automation':
            stop_automation_actions.append({
                'index': i,
                'action': action
            })
    
    print(f"Found {len(stop_automation_actions)} STOP_AUTOMATION actions")
    
    # Validate each stop_automation action
    issues = []
    for stop_action in stop_automation_actions:
        action = stop_action['action']
        index = stop_action['index']
        
        # Check for proper configuration
        value = action.get('value', {})
        if not value:
            issues.append(f"STOP_AUTOMATION at index {index} missing value configuration")
        else:
            if 'reason' not in value:
                issues.append(f"STOP_AUTOMATION at index {index} missing 'reason' in value")
            if 'log_file' not in value:
                issues.append(f"STOP_AUTOMATION at index {index} missing 'log_file' in value")
        
        print(f"  ✓ STOP_AUTOMATION at index {index}")
        if value.get('reason'):
            print(f"    Reason: {value['reason']}")
        if value.get('log_file'):
            print(f"    Log file: {value['log_file']}")
    
    # Check that old BREAK actions are removed
    break_actions = []
    for i, action in enumerate(actions):
        if action.get('type') == 'break':
            break_actions.append(i)
    
    if break_actions:
        issues.append(f"Found {len(break_actions)} old BREAK actions at indices: {break_actions}")
    else:
        print("  ✓ No old BREAK actions found")
    
    # Check that WHILE loops used for BREAK are removed
    while_begin_actions = []
    while_end_actions = []
    for i, action in enumerate(actions):
        if action.get('type') == 'while_begin':
            condition = action.get('value', {}).get('condition')
            if condition == 'always_true':
                while_begin_actions.append(i)
        elif action.get('type') == 'while_end':
            while_end_actions.append(i)
    
    if while_begin_actions:
        issues.append(f"Found {len(while_begin_actions)} unnecessary WHILE_BEGIN actions at indices: {while_begin_actions}")
    else:
        print("  ✓ No unnecessary WHILE_BEGIN actions found")
    
    # Validate queue detection flow
    queue_checks = []
    for i, action in enumerate(actions):
        if (action.get('type') == 'check_element' and 
            ('reached your' in str(action.get('selector', '')) or
             'reached your' in str(action.get('value', {}).get('value', '')))):
            queue_checks.append(i)
    
    print(f"Found {len(queue_checks)} queue detection checks")
    
    # Check that each queue check is followed by proper logic
    for check_index in queue_checks:
        # Look for IF_BEGIN after the check
        if_found = False
        stop_found = False
        
        for j in range(check_index + 1, min(check_index + 5, len(actions))):
            action = actions[j]
            if action.get('type') == 'if_begin':
                if_found = True
            elif action.get('type') == 'stop_automation':
                stop_found = True
                break
        
        if not if_found:
            issues.append(f"Queue check at {check_index} not followed by IF_BEGIN")
        if not stop_found:
            issues.append(f"Queue check at {check_index} not followed by STOP_AUTOMATION")
        else:
            print(f"  ✓ Queue check at {check_index} properly configured")
    
    # Validation results
    print("\n=== Validation Results ===")
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Stop automation implementation is correct!")
        print("\nImplementation features:")
        print(f"  - {len(stop_automation_actions)} STOP_AUTOMATION actions with proper configuration")
        print(f"  - {len(queue_checks)} queue detection checks with proper flow")
        print("  - No old BREAK actions remaining")
        print("  - No unnecessary WHILE loops")
        print("  - Proper error logging configured")
        return True

def main():
    """Main test function"""
    config_file = Path(__file__).parent.parent / "workflows" / "run-08-16-1.json"
    
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
    
    print(f"Testing STOP_AUTOMATION implementation in: {config_file}")
    print("=" * 70)
    
    success = validate_stop_automation_implementation(config_file)
    
    if success:
        print("\n✅ Test PASSED: STOP_AUTOMATION is properly implemented")
        print("\nExpected behavior:")
        print("  1. Queue full popup detected → check_element succeeds")
        print("  2. IF condition met → Enter error handling")
        print("  3. Log error message")
        print("  4. STOP_AUTOMATION executed → Automation terminates immediately")
        print("  5. Scheduler detects failure → Retry triggered")
        sys.exit(0)
    else:
        print("\n❌ Test FAILED: STOP_AUTOMATION implementation needs fixes")
        sys.exit(1)

if __name__ == "__main__":
    main()