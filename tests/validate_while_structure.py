#!/usr/bin/env python3
"""
Validate WHILE loop structure in the automation configuration
"""

import json
import sys
from pathlib import Path

def validate_while_structure(config_file):
    """Validate that WHILE loops are properly nested and matched"""
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    actions = config.get('actions', [])
    
    # Track loop nesting
    while_stack = []
    issues = []
    
    for i, action in enumerate(actions):
        action_type = action.get('type')
        
        if action_type == 'while_begin':
            while_stack.append({
                'index': i,
                'description': action.get('description', ''),
                'condition': action.get('value', {}).get('condition', '')
            })
            print(f"📍 WHILE_BEGIN at {i}: {action.get('description')}")
            
        elif action_type == 'while_end':
            if not while_stack:
                issues.append(f"WHILE_END at {i} without matching WHILE_BEGIN")
            else:
                start = while_stack.pop()
                print(f"✅ WHILE_END at {i} matches WHILE_BEGIN at {start['index']}")
                
        elif action_type == 'break':
            if not while_stack:
                issues.append(f"BREAK at {i} outside of any WHILE loop")
            else:
                print(f"✅ BREAK at {i} inside WHILE loop (started at {while_stack[-1]['index']})")
    
    # Check for unmatched WHILE_BEGIN
    for unmatched in while_stack:
        issues.append(f"WHILE_BEGIN at {unmatched['index']} without matching WHILE_END")
    
    print(f"\n📊 STRUCTURE ANALYSIS:")
    print(f"=" * 40)
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All WHILE loops properly nested and matched")
        print("✅ All BREAK statements inside WHILE loops")
        return True

def main():
    """Main validation function"""
    config_file = Path(__file__).parent.parent / "workflows" / "run-08-16-1.json"
    
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
    
    print("WHILE LOOP STRUCTURE VALIDATION")
    print("=" * 50)
    
    success = validate_while_structure(config_file)
    
    if success:
        print("\n✅ VALIDATION PASSED: WHILE/BREAK structure is correct")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED: WHILE/BREAK structure needs fixes")
        sys.exit(1)

if __name__ == "__main__":
    main()