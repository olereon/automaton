#!/usr/bin/env python3
"""
Fix import statements in all example files
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern replacements
    replacements = [
        # Fix direct core imports
        (r'from core\.engine import', 'from src.core.engine import'),
        (r'from core\.controller import', 'from src.core.controller import'),
        (r'from interfaces\.gui import', 'from src.interfaces.gui import'),
        (r'from interfaces\.cli import', 'from src.interfaces.cli import'),
        (r'from utils\.', 'from src.utils.'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Check if we need to add proper path setup
    if 'sys.path.insert' not in content and 'from src.' in content:
        # Find the import section
        import_match = re.search(r'(import.*?\n)+', content)
        if import_match:
            import_end = import_match.end()
            
            path_setup = """
# Add parent directory to path for imports
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

"""
            # Insert path setup before the first from import
            first_from = content.find('from src.')
            if first_from > 0:
                content = content[:first_from] + path_setup + content[first_from:]
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all example files"""
    examples_dir = Path(__file__).parent.parent / "examples"
    
    print("🔧 Fixing imports in example files...")
    fixed_count = 0
    
    for py_file in examples_dir.glob("*.py"):
        if fix_imports_in_file(py_file):
            print(f"  ✅ Fixed: {py_file.name}")
            fixed_count += 1
        else:
            print(f"  ⏭️  Skipped: {py_file.name} (no changes needed)")
    
    print(f"\n✨ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()