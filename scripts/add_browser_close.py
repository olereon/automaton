#!/usr/bin/env python3
"""
Add keep_browser_open: false to all workflow configurations
This ensures browser closes after each workflow run to prevent login conflicts
"""

import json
from pathlib import Path

def add_browser_close_to_config(file_path):
    """Add keep_browser_open: false to a workflow config"""
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        # Add keep_browser_open: false to root level
        config['keep_browser_open'] = False
        
        # Save the updated config
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to update {file_path}: {e}")
        return False

def main():
    """Update all run-08-16-*.json workflow files"""
    workflows_dir = Path(__file__).parent.parent / "workflows"
    
    # Find all run-08-16-*.json files
    workflow_files = list(workflows_dir.glob("run-08-16-*.json"))
    
    print(f"Found {len(workflow_files)} workflow files to update")
    print("="*50)
    
    success_count = 0
    for file_path in sorted(workflow_files):
        if add_browser_close_to_config(file_path):
            success_count += 1
    
    print("="*50)
    print(f"✅ Successfully updated {success_count}/{len(workflow_files)} files")
    print("\n🎯 Browser will now close after each workflow run!")
    print("This prevents login conflicts and improves reliability.")

if __name__ == "__main__":
    main()