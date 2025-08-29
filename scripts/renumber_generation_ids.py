#!/usr/bin/env python3
"""
Generation ID Renumbering Script
Renumbers all generation IDs in the log file sequentially and adds a summary header.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

def renumber_generation_ids(log_file_path: str = None):
    """
    Renumber all generation IDs in the log file sequentially.
    
    Args:
        log_file_path: Path to the generation downloads log file
    """
    
    # Default log file path
    if log_file_path is None:
        log_file_path = Path(__file__).parent.parent / "logs" / "generation_downloads.txt"
    else:
        log_file_path = Path(log_file_path)
    
    # Check if file exists
    if not log_file_path.exists():
        print(f"❌ Log file not found: {log_file_path}")
        return False
    
    print(f"📄 Processing log file: {log_file_path}")
    
    try:
        # Read all lines from the file
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("⚠️ Log file is empty")
            return False
        
        # Pattern to match generation IDs (e.g., #000000001, #999999999, etc.)
        id_pattern = re.compile(r'#\d{9}')
        
        # Process lines and renumber IDs
        processed_lines = []
        id_counter = 1
        total_entries = 0
        
        for line in lines:
            # Skip existing summary lines at the beginning
            if line.startswith("Updated on ") or line.startswith("Total generations:"):
                continue
            
            # Check if line contains a generation ID
            if id_pattern.search(line):
                # Replace the ID with the new sequential number
                new_id = f"#{id_counter:09d}"
                new_line = id_pattern.sub(new_id, line)
                processed_lines.append(new_line)
                
                print(f"   ✏️ Entry {id_counter}: {new_id}")
                id_counter += 1
                total_entries += 1
            else:
                # Keep non-entry lines as-is (but this shouldn't happen in a proper log)
                processed_lines.append(line)
        
        # Create summary header
        current_time = datetime.now()
        summary_lines = [
            f"Updated on {current_time.strftime('%Y-%m-%d')} {current_time.strftime('%H:%M:%S')}\n",
            f"Total generations: {total_entries}\n",
            "=" * 80 + "\n",
            "\n"
        ]
        
        # Combine summary with processed lines
        final_content = summary_lines + processed_lines
        
        # Create backup of original file
        backup_path = log_file_path.with_suffix('.txt.backup')
        print(f"\n💾 Creating backup: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Write the renumbered content back to the file
        print(f"\n✍️ Writing renumbered content to: {log_file_path}")
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.writelines(final_content)
        
        # Print summary
        print("\n" + "=" * 60)
        print("✅ RENUMBERING COMPLETE")
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   • Updated on: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   • Total generations: {total_entries}")
        print(f"   • IDs renumbered: #000000001 to #{total_entries:09d}")
        print(f"   • Backup saved to: {backup_path}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing log file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    
    print("🔢 Generation ID Renumbering Script")
    print("=" * 60)
    
    # Check for command line argument
    if len(sys.argv) > 1:
        log_file_path = sys.argv[1]
        print(f"📁 Using specified log file: {log_file_path}")
    else:
        log_file_path = None
        print("📁 Using default log file: logs/generation_downloads.txt")
    
    print()
    
    # Run the renumbering
    success = renumber_generation_ids(log_file_path)
    
    if success:
        print("\n🎉 Script completed successfully!")
        print("💡 The generation IDs have been renumbered sequentially.")
        print("📌 A backup of the original file has been created.")
        return 0
    else:
        print("\n❌ Script failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)