#!/usr/bin/env python3
"""
Apply Queue Fix to Workflow Files
Applies the same queue handling modifications from run-08-16-1.json to files 2-16.
"""

import json
import os
from pathlib import Path

def apply_queue_fix(file_path):
    """Apply the queue fix modifications to a single workflow file"""
    print(f"Processing {file_path}...")
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        actions = data.get('actions', [])
        if not actions:
            print(f"  No actions found in {file_path}")
            return False
            
        # Find the indices of key actions to modify
        initial_queue_check_idx = None
        conditional_wait_idx = None
        initial_queue_click_idx = None
        while_begin_idx = None
        
        for i, action in enumerate(actions):
            # Find initial queue check (before while loop)
            if (action.get('type') == 'check_element' and 
                action.get('selector') == '.sc-dMmcxd.cZTIpi' and
                'Check if queue has space' in action.get('description', '')):
                initial_queue_check_idx = i
                print(f"  Found initial queue check at index {i}")
                
            # Find conditional wait
            elif (action.get('type') == 'conditional_wait' and
                  'Retry if queue element not found' in action.get('description', '')):
                conditional_wait_idx = i
                print(f"  Found conditional wait at index {i}")
                
            # Find initial queue click 
            elif (action.get('type') == 'click_button' and
                  action.get('selector') == '.sc-dMmcxd.cZTIpi' and
                  'click-the-queue-numb' in action.get('description', '')):
                initial_queue_click_idx = i
                print(f"  Found initial queue click at index {i}")
                
            # Find while_begin
            elif action.get('type') == 'while_begin':
                while_begin_idx = i
                print(f"  Found while_begin at index {i}")
                break
        
        if not all([initial_queue_check_idx is not None, while_begin_idx is not None]):
            print(f"  Could not find required actions in {file_path}")
            return False
            
        # Extract task creation actions from inside the while loop
        # Look for the task creation sequence after while_begin
        task_creation_start = None
        task_creation_end = None
        
        # Find the first task creation action (log message "Creating task")
        for i in range(while_begin_idx + 1, len(actions)):
            action = actions[i]
            if (action.get('type') == 'log_message' and
                'Creating task #0' in action.get('value', {}).get('message', '')):
                task_creation_start = i
                print(f"  Found task creation start at index {i}")
                break
                
        # Find the end of first task creation (after increment_variable and log_message)
        if task_creation_start is not None:
            for i in range(task_creation_start, len(actions)):
                action = actions[i]
                if (action.get('type') == 'log_message' and
                    'Successfully created task #1' in action.get('value', {}).get('message', '')):
                    # Include actions until after the wait between tasks
                    for j in range(i + 1, len(actions)):
                        next_action = actions[j]
                        if (next_action.get('type') == 'wait' and
                            'Wait between tasks' in next_action.get('description', '')):
                            task_creation_end = j + 1
                            print(f"  Found task creation end at index {task_creation_end}")
                            break
                    break
                    
        if task_creation_start is None or task_creation_end is None:
            print(f"  Could not find task creation sequence in {file_path}")
            return False
            
        # Extract the task creation actions
        task_creation_actions = actions[task_creation_start:task_creation_end]
        print(f"  Extracted {len(task_creation_actions)} task creation actions")
        
        # Find queue check after task creation
        queue_check_after_idx = None
        for i in range(task_creation_end, len(actions)):
            action = actions[i]
            if (action.get('type') == 'check_element' and
                action.get('selector') == '.sc-dMmcxd.cZTIpi' and
                'Final queue space check' in action.get('description', '')):
                queue_check_after_idx = i
                print(f"  Found queue check after task creation at index {i}")
                break
                
        # Build new actions list
        new_actions = []
        
        # 1. Keep everything up to initial queue check
        new_actions.extend(actions[:initial_queue_check_idx])
        
        # 2. Add the task creation actions (moved from inside while loop)
        # Add settings actions first (they were moved to before task creation in the reference)
        settings_actions = [
            {
                "type": "click_button",
                "selector": "[data-test-id=\"creation-form-button-setting\"]",
                "value": None,
                "timeout": 2000,
                "description": "Click settings button"
            },
            {
                "type": "wait",
                "selector": None,
                "value": 1500,
                "timeout": 2000,
                "description": "Wait for settings to open"
            },
            {
                "type": "toggle_setting",
                "selector": "[data-test-id=\"creation-form-checkbox-generateWidthCredits\"]",
                "value": False,
                "timeout": 2000,
                "description": "Toggle off credits"
            },
            {
                "type": "wait",
                "selector": None,
                "value": 500,
                "timeout": 2000,
                "description": "Wait after toggle"
            },
            {
                "type": "click_button",
                "selector": "[data-test-id=\"creation-form-button-setting\"]",
                "value": None,
                "timeout": 2000,
                "description": "Close settings"
            }
        ]
        
        new_actions.extend(settings_actions)
        
        # Find upload_image and input_text actions from task creation sequence
        upload_start = None
        for i, action in enumerate(task_creation_actions):
            if action.get('type') == 'click_button' and 'First Frame' in action.get('selector', ''):
                upload_start = i
                break
                
        if upload_start is not None:
            # Add the upload and prompt actions
            upload_actions = task_creation_actions[upload_start:]
            # Find where to stop (after submit)
            for i, action in enumerate(upload_actions):
                if action.get('type') == 'click_button' and 'submit' in action.get('selector', ''):
                    # Include submit, increment, log, and wait
                    new_actions.extend(upload_actions[:i+4])
                    break
        
        # 3. Add queue check after task creation
        if queue_check_after_idx is not None:
            # Add queue update actions
            queue_update_actions = [
                {
                    "type": "click_button", 
                    "selector": "[data-test-id=\"sidebar-menuitem-button-Favorites\"]",
                    "value": None,
                    "timeout": 2000,
                    "description": "click-heart-button2"
                },
                {
                    "type": "wait",
                    "selector": None, 
                    "value": 2000,
                    "timeout": 2000,
                    "description": "Wait for queue to update after task submission"
                }
            ]
            new_actions.extend(queue_update_actions)
            
            # Add queue check
            new_actions.append(actions[queue_check_after_idx])
            
            # Add queue click
            next_action = actions[queue_check_after_idx + 1]
            if next_action.get('type') == 'click_button' and next_action.get('selector') == '.sc-dMmcxd.cZTIpi':
                new_actions.append(next_action)
        
        # 4. Add while loop and everything after
        new_actions.extend(actions[while_begin_idx:])
        
        # Update the data
        data['actions'] = new_actions
        
        # Save the file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"  Successfully updated {file_path}")
        print(f"  Actions: {len(actions)} -> {len(new_actions)}")
        return True
        
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return False

def main():
    """Apply queue fix to all workflow files 2-16"""
    base_dir = Path(__file__).parent / "workflows"
    
    files_to_update = []
    for i in range(2, 17):
        file_path = base_dir / f"run-08-16-{i}.json"
        if file_path.exists():
            files_to_update.append(file_path)
    
    print(f"Found {len(files_to_update)} files to update")
    
    successful = 0
    failed = 0
    
    for file_path in files_to_update:
        if apply_queue_fix(file_path):
            successful += 1
        else:
            failed += 1
    
    print(f"\nCompleted: {successful} successful, {failed} failed")

if __name__ == "__main__":
    main()