#!/usr/bin/env python3
"""
Fix workflow files by removing incorrectly added heart button click and wait actions.
These actions were mistakenly added and break the workflow by navigating away from the generate page.
"""

import json
from pathlib import Path

def fix_workflow_file(file_path):
    """Remove the incorrectly added heart button click and wait actions"""
    print(f"Processing {file_path.name}...")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        actions = data.get('actions', [])
        if not actions:
            print(f"  No actions found in {file_path.name}")
            return False
        
        # Find and remove the incorrectly added actions
        # Looking for the pattern: heart button click followed by small-wait (100ms)
        # that appears BEFORE the settings button click
        
        new_actions = []
        i = 0
        removed_count = 0
        
        while i < len(actions):
            action = actions[i]
            
            # Check if this is the incorrectly added heart button + wait sequence
            # It would be right after "Log automation start" and before "Click settings button"
            if (i > 0 and i < len(actions) - 1 and
                action.get('type') == 'click_button' and 
                action.get('selector') == '[data-test-id="sidebar-menuitem-button-Favorites"]' and
                action.get('description') == 'Click-heart-button'):
                
                # Check if next action is the small-wait
                next_action = actions[i + 1] if i + 1 < len(actions) else None
                if (next_action and 
                    next_action.get('type') == 'wait' and 
                    next_action.get('value') == 100 and
                    next_action.get('description') == 'small-wait'):
                    
                    # Skip both actions (the incorrect heart button and wait)
                    print(f"  Removing incorrect heart button click at index {i}")
                    print(f"  Removing small-wait at index {i+1}")
                    i += 2  # Skip both actions
                    removed_count += 2
                    continue
            
            # Keep this action
            new_actions.append(action)
            i += 1
        
        if removed_count > 0:
            # Update the actions
            data['actions'] = new_actions
            
            # Save the file
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"  ✅ Removed {removed_count} incorrect actions")
            print(f"  Actions: {len(actions)} -> {len(new_actions)}")
            return True
        else:
            print(f"  ✅ No incorrect actions found (file is clean)")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {file_path.name}: {e}")
        return False

def main():
    """Fix all run-08-16-*.json workflow files"""
    workflows_dir = Path(__file__).parent.parent / "workflows"
    
    # Process files 2-16 (file 1 is the reference and should be correct)
    files_to_fix = []
    for i in range(2, 17):
        file_path = workflows_dir / f"run-08-16-{i}.json"
        if file_path.exists():
            files_to_fix.append(file_path)
    
    print(f"Found {len(files_to_fix)} workflow files to check and fix")
    print("="*50)
    
    fixed_count = 0
    for file_path in sorted(files_to_fix):
        if fix_workflow_file(file_path):
            fixed_count += 1
    
    print("="*50)
    print(f"✅ Fixed {fixed_count} files")
    print(f"📊 {len(files_to_fix) - fixed_count} files were already correct")
    
    # Verify all files now have the same action count
    print("\n📋 Verifying action counts:")
    ref_file = workflows_dir / "run-08-16-1.json"
    with open(ref_file, 'r') as f:
        ref_data = json.load(f)
        ref_count = len(ref_data.get('actions', []))
    print(f"  Reference (run-08-16-1.json): {ref_count} actions")
    
    for file_path in sorted(files_to_fix):
        with open(file_path, 'r') as f:
            data = json.load(f)
            action_count = len(data.get('actions', []))
            status = "✅" if action_count == ref_count else "❌"
            print(f"  {status} {file_path.name}: {action_count} actions")

if __name__ == "__main__":
    main()