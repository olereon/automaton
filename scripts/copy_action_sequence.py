#!/usr/bin/env python3
"""
Script to copy action sequence from chosen json to all run-*.json files
while preserving the FIRST image path and prompt text.

This script:
1. Reads the source action sequence from chosen json
2. For each target run-*.json file, extracts the FIRST image path and prompt text
3. Replaces the action sequence with the source sequence
4. Applies the preserved image path and prompt text to ALL upload_image and input_text actions
"""

import json
import os
import glob
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Union


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {file_path}: {e}")
        raise
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        raise


def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Save data to a JSON file with proper formatting."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully saved: {file_path}")
    except Exception as e:
        logging.error(f"Error saving {file_path}: {e}")
        raise


def extract_first_image_and_prompt_data(actions: List[Dict[str, Any]]) -> Union[Tuple[str, str], None]:
    """
    Extract ONLY the first image path and prompt text from actions.
    
    Returns:
        Tuple: (image_path, prompt_text) or None if not found
    """
    for i, action in enumerate(actions):
        # Find the first upload_image action
        if action.get('type') == 'upload_image' and action.get('value'):
            image_path = action['value']
            
            # Find the next input_text action (prompt)
            for j in range(i + 1, len(actions)):
                next_action = actions[j]
                if (next_action.get('type') == 'input_text' and 
                    next_action.get('selector') == "[data-test-id=\"creation-form-textarea\"]" and 
                    next_action.get('value')):
                    prompt_text = next_action['value']
                    logging.debug(f"Found first image-prompt pair: {os.path.basename(image_path)}")
                    return (image_path, prompt_text)
            break  # Stop after first upload_image, even if no matching prompt found
    
    return None


def apply_preserved_data_to_all(actions: List[Dict[str, Any]], preserved_data: Union[Tuple[str, str], None]) -> List[Dict[str, Any]]:
    """
    Apply the SINGLE preserved image path and prompt text to ALL corresponding actions in the sequence.
    
    Args:
        actions: The new action sequence
        preserved_data: Tuple of (image_path, prompt_text) or None
    
    Returns:
        Modified action sequence with preserved data applied to all matching actions
    """
    if not preserved_data:
        logging.warning("No preserved data to apply")
        return actions
    
    image_path, prompt_text = preserved_data
    logging.info(f"Applying preserved data to all actions: {os.path.basename(image_path)}")
    
    # Create a copy to avoid modifying the original
    modified_actions = [action.copy() for action in actions]
    
    # Apply preserved data to ALL upload_image and input_text actions
    for i, action in enumerate(modified_actions):
        if action.get('type') == 'upload_image':
            action['value'] = image_path
            logging.debug(f"Applied image path at action {i}: {os.path.basename(image_path)}")
        
        elif (action.get('type') == 'input_text' and 
              action.get('selector') == "[data-test-id=\"creation-form-textarea\"]"):
            action['value'] = prompt_text
            logging.debug(f"Applied prompt text at action {i}: {prompt_text[:50]}...")
    
    return modified_actions


def process_file(source_actions: List[Dict[str, Any]], target_file: str, dry_run: bool = False) -> bool:
    """
    Process a single target file by replacing its action sequence while preserving image data.
    
    Args:
        source_actions: The source action sequence to copy
        target_file: Path to the target file to modify
        dry_run: If True, don't actually save the file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logging.info(f"Processing: {os.path.basename(target_file)}")
        
        # Load target file
        target_data = load_json_file(target_file)
        
        # Extract preserved data from target file (only the first pair)
        preserved_data = extract_first_image_and_prompt_data(target_data.get('actions', []))
        
        if preserved_data:
            image_path, prompt_text = preserved_data
            logging.info(f"Found first image-prompt pair to preserve: {os.path.basename(image_path)}")
        else:
            logging.warning(f"No image-prompt pair found in {target_file}")
        
        # Copy source actions and apply preserved data to all matching actions
        new_actions = apply_preserved_data_to_all(source_actions.copy(), preserved_data)
        
        # Update target data with new actions
        target_data['actions'] = new_actions
        
        # Save the modified file (unless dry run)
        if not dry_run:
            # Create backup
            backup_file = target_file + '.backup'
            if not os.path.exists(backup_file):
                save_json_file(load_json_file(target_file), backup_file)
                logging.info(f"Created backup: {backup_file}")
            
            save_json_file(target_data, target_file)
        else:
            logging.info(f"DRY RUN: Would update {target_file}")
        
        return True
        
    except Exception as e:
        logging.error(f"Failed to process {target_file}: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--source', 
        default='workflows/run-08-18-1.json',
        help='Source file containing the action sequence to copy (default: workflows/run-08-18-1.json)'
    )
    parser.add_argument(
        '--workflow-dir',
        default='workflows',
        help='Directory containing workflow files (default: workflows)'
    )
    parser.add_argument(
        '--pattern',
        default='run-*.json',
        help='Pattern to match target files (default: run-*.json)'
    )
    parser.add_argument(
        '--exclude-source',
        action='store_true',
        help='Exclude the source file from processing'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually modifying files'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    try:
        # Load source file
        source_file = args.source
        if not os.path.isabs(source_file):
            source_file = os.path.join(os.getcwd(), source_file)
            
        logging.info(f"Loading source file: {source_file}")
        source_data = load_json_file(source_file)
        source_actions = source_data.get('actions', [])
        
        if not source_actions:
            logging.error("No actions found in source file")
            return 1
        
        logging.info(f"Source file contains {len(source_actions)} actions")
        
        # Find target files
        workflow_dir = args.workflow_dir
        if not os.path.isabs(workflow_dir):
            workflow_dir = os.path.join(os.getcwd(), workflow_dir)
            
        pattern = os.path.join(workflow_dir, args.pattern)
        target_files = glob.glob(pattern)
        
        if args.exclude_source:
            source_basename = os.path.basename(source_file)
            target_files = [f for f in target_files if os.path.basename(f) != source_basename]
        
        if not target_files:
            logging.error(f"No target files found matching pattern: {pattern}")
            return 1
        
        logging.info(f"Found {len(target_files)} target files")
        
        # Process each target file
        success_count = 0
        for target_file in sorted(target_files):
            if process_file(source_actions, target_file, args.dry_run):
                success_count += 1
        
        logging.info(f"Successfully processed {success_count}/{len(target_files)} files")
        
        if args.dry_run:
            logging.info("DRY RUN completed - no files were actually modified")
        
        return 0 if success_count == len(target_files) else 1
        
    except Exception as e:
        logging.error(f"Script failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())