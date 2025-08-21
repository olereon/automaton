# Copy Action Sequence Script Guide

## Overview

The `copy_action_sequence.py` script copies the action sequence from `run-08-16-3.json` to all other `run-*.json` files in the workflows folder while preserving the original image paths and prompt texts from each target file.

## What the Script Does

1. **Reads the source file** (`run-08-16-3.json`) to extract the action sequence template
2. **Processes each target file** (all other `run-*.json` files) by:
   - Extracting existing image paths from `upload_image` actions
   - Extracting existing prompt texts from corresponding `input_text` actions
   - Replacing the entire action sequence with the source template
   - Restoring the original image paths and prompt texts to preserve file-specific data

## Features

- **Smart Preservation**: Automatically identifies and preserves image-prompt pairs
- **Backup Creation**: Creates `.backup` files before modifying originals
- **Dry Run Mode**: Test what changes would be made without actually modifying files
- **Verbose Logging**: Detailed output showing exactly what's being preserved and applied
- **Error Handling**: Comprehensive error handling and validation
- **Flexible Configuration**: Customizable source file, directory, and file patterns

## Usage

### Basic Usage

```bash
# Run with default settings (dry run first recommended)
python3.11 scripts/copy_action_sequence.py --dry-run

# Execute the actual changes
python3.11 scripts/copy_action_sequence.py
```

### Advanced Usage

```bash
# Use a different source file
python3.11 scripts/copy_action_sequence.py --source workflows/custom-template.json

# Process a different directory
python3.11 scripts/copy_action_sequence.py --workflow-dir other-workflows

# Use a different file pattern
python3.11 scripts/copy_action_sequence.py --pattern "config-*.json"

# Exclude the source file from processing (default behavior)
python3.11 scripts/copy_action_sequence.py --exclude-source

# Verbose output to see detailed processing
python3.11 scripts/copy_action_sequence.py --verbose
```

### Command Line Options

- `--source`: Source file containing the action sequence to copy (default: `workflows/run-08-16-3.json`)
- `--workflow-dir`: Directory containing workflow files (default: `workflows`)
- `--pattern`: Pattern to match target files (default: `run-*.json`)
- `--exclude-source`: Exclude the source file from processing (enabled by default)
- `--dry-run`: Show what would be done without actually modifying files
- `--verbose, -v`: Enable verbose logging

## How It Works

### Image-Prompt Pair Detection

The script looks for this pattern in each file:

1. **Upload Image Action**: `{"type": "upload_image", "value": "/path/to/image.png"}`
2. **Following Input Text Action**: `{"type": "input_text", "selector": "[data-test-id=\"creation-form-textarea\"]", "value": "prompt text"}`

### Preservation Process

1. **Extract**: For each target file, find all image-prompt pairs and save them
2. **Replace**: Replace the entire action sequence with the source template
3. **Restore**: Apply the preserved image paths and prompt texts to the new sequence

### Example

**Before**: Target file has image `/path/to/old-image.png` and prompt "Old prompt text"
**After**: Target file uses the new action sequence but keeps `/path/to/old-image.png` and "Old prompt text"

## Safety Features

- **Backup Files**: Original files are backed up as `.backup` before modification
- **Dry Run Mode**: Test changes without modifying files
- **Validation**: Checks for valid JSON and required action structure
- **Error Recovery**: Detailed error messages and graceful failure handling

## File Structure

The script expects workflow files to be in this format:

```json
{
  "name": "...",
  "url": "...",
  "actions": [
    {
      "type": "upload_image",
      "value": "/path/to/image.png"
    },
    {
      "type": "input_text",
      "selector": "[data-test-id=\"creation-form-textarea\"]",
      "value": "prompt text"
    }
  ]
}
```

## Output Example

```
2025-08-17 17:42:38 - INFO - Loading source file: workflows/run-08-16-3.json
2025-08-17 17:42:38 - INFO - Source file contains 69 actions
2025-08-17 17:42:38 - INFO - Found 16 target files
2025-08-17 17:42:38 - INFO - Processing: run-08-16-1.json
2025-08-17 17:42:38 - INFO - Found 2 image-prompt pairs to preserve
2025-08-17 17:42:38 - INFO - Created backup: run-08-16-1.json.backup
2025-08-17 17:42:38 - INFO - Successfully saved: run-08-16-1.json
2025-08-17 17:42:38 - INFO - Successfully processed 16/16 files
```

## Troubleshooting

### Common Issues

1. **No image-prompt pairs found**: Check that your files have the expected structure
2. **Permission errors**: Ensure you have write access to the workflow directory
3. **JSON errors**: Validate your JSON files are properly formatted

### Verification

After running the script, you can verify the changes by:

1. Checking that backup files were created
2. Comparing action counts between source and target files
3. Verifying that preserved image paths and prompts are still present

## Requirements

- Python 3.7+
- Standard library modules only (no external dependencies)
- Read/write access to the workflow directory

## Location

The script is located at: `scripts/copy_action_sequence.py`