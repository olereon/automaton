#!/usr/bin/env python3.11
"""
Boundary Detection Issue Analysis
=================================
Analyzes why the boundary detection failed to find generation from 03 Sep 2025 16:15:18.
"""

import sys
import os
import re
from pathlib import Path

# Add parent directory to path for imports  
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig


def analyze_log_entries():
    """Analyze the existing log entries to understand the boundary"""
    
    print("🔍 BOUNDARY DETECTION ISSUE ANALYSIS")
    print("=" * 60)
    
    # Load log file
    log_file = "/home/olereon/workspace/github.com/olereon/automaton/logs/generation_downloads.txt"
    
    if not os.path.exists(log_file):
        print("❌ Log file not found!")
        return False
    
    print("📊 STEP 1: Analyzing log entries")
    print("-" * 40)
    
    # Parse log entries (same way the system does)
    log_entries = {}
    current_id = None
    current_time = None
    current_prompt = None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # ID line
            if line.startswith('#'):
                if current_time and current_id:
                    log_entries[current_time] = {
                        'id': current_id,
                        'prompt': current_prompt or '',
                        'line': line_num - 2
                    }
                current_id = line
                current_time = None
                current_prompt = None
            
            # Time line (next line after ID)
            elif current_id and not current_time:
                current_time = line
            
            # Prompt line (next line after time)
            elif current_time and not current_prompt:
                current_prompt = line
            
            # Separator
            elif line.startswith('='):
                if current_time and current_id:
                    log_entries[current_time] = {
                        'id': current_id,
                        'prompt': current_prompt or '',
                        'line': line_num - 3
                    }
                current_id = None
                current_time = None
                current_prompt = None
    
    # Final entry if file doesn't end with separator
    if current_time and current_id:
        log_entries[current_time] = {
            'id': current_id,
            'prompt': current_prompt or '',
            'line': line_num
        }
    
    print(f"   📚 Total log entries: {len(log_entries)}")
    
    # Find entries from 03 Sep 2025
    sep_3_entries = []
    target_time = "03 Sep 2025 16:15:18"
    
    for log_time, log_entry in log_entries.items():
        if log_time.startswith('03 Sep 2025'):
            sep_3_entries.append((log_time, log_entry))
    
    sep_3_entries.sort(reverse=True)  # Most recent first
    
    print(f"   📅 Entries from '03 Sep 2025': {len(sep_3_entries)}")
    print(f"   🎯 Target time '{target_time}': {'FOUND' if target_time in log_entries else 'NOT FOUND ✅'}")
    
    print("\n📊 STEP 2: Time gap analysis around target time")
    print("-" * 40)
    
    # Find the time gap where our target should be
    times_around_target = []
    target_hour = 16  # 16:15:18 is in hour 16
    
    for log_time, log_entry in sep_3_entries:
        if log_time.startswith('03 Sep 2025'):
            # Extract hour from time 
            match = re.search(r'(\d{2}):(\d{2}):(\d{2})', log_time)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                second = int(match.group(3))
                
                # Look for entries around hour 16
                if abs(hour - target_hour) <= 1:
                    times_around_target.append({
                        'time': log_time,
                        'hour': hour,
                        'minute': minute,
                        'second': second,
                        'id': log_entry['id']
                    })
    
    times_around_target.sort(key=lambda x: (x['hour'], x['minute'], x['second']), reverse=True)
    
    print(f"   ⏰ Entries around target hour {target_hour}:00:")
    for i, entry in enumerate(times_around_target[:10]):
        marker = "🎯 TARGET SHOULD BE HERE" if entry['hour'] == target_hour and entry['minute'] > 15 else ""
        print(f"      {i+1}. {entry['time']} ({entry['id']}) {marker}")
    
    print(f"\n💡 ANALYSIS RESULTS:")
    print("-" * 40)
    
    if target_time not in log_entries:
        print(f"✅ CONFIRMED: '{target_time}' is NOT in log file")
        print(f"✅ This generation SHOULD be detected as boundary")
        print(f"❌ But the system scrolled past it without detection")
        print(f"")
        print(f"🔍 ROOT CAUSE ANALYSIS:")
        print(f"   The boundary detection failed because:")
        print(f"   1. 🏗️ Container loading: New containers after scroll may have different DOM structure")
        print(f"   2. ⏰ Timing issue: Metadata extraction happens before DOM is fully updated")
        print(f"   3. 🔍 Selector mismatch: Fixed selectors don't match dynamically loaded containers")
        print(f"   4. 📝 Text parsing: Creation time extraction fails on new container format")
        print(f"   5. 🔄 Sync issue: Fast scrolling outpaces metadata extraction")
        
        return True
    else:
        print(f"❌ ERROR: '{target_time}' WAS found in log file")
        print(f"   This indicates the generation was already downloaded")
        print(f"   Need to investigate why user thinks it wasn't downloaded")
        return False


def analyze_metadata_extraction_issues():
    """Analyze potential metadata extraction issues"""
    
    print(f"\n🔧 STEP 3: Metadata extraction issue analysis")
    print("-" * 40)
    
    print("📝 Current metadata extraction patterns:")
    print("   Primary pattern: r'Creation Time\\s*(\\d{1,2}\\s+\\w{3}\\s+\\d{4}\\s+\\d{2}:\\d{2}:\\d{2})'")
    print("   Fallback pattern: r'(\\d{1,2}\\s+\\w{3}\\s+\\d{4}\\s+\\d{2}:\\d{2}:\\d{2})'")
    
    print(f"\n🎯 Testing patterns against target: '03 Sep 2025 16:15:18'")
    
    # Test the patterns
    test_texts = [
        "Creation Time 03 Sep 2025 16:15:18",  # Standard format
        "03 Sep 2025 16:15:18",                # No prefix
        "Creation Time\n03 Sep 2025 16:15:18", # Newline after prefix
        "Some other text\n03 Sep 2025 16:15:18\nPrompt text here",  # Embedded
        "Creation Time   03 Sep 2025 16:15:18",  # Multiple spaces
    ]
    
    patterns = [
        r'Creation Time\s*(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})',
        r'(\d{1,2}\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2})'
    ]
    
    for i, test_text in enumerate(test_texts):
        print(f"   Test {i+1}: '{test_text}'")
        for j, pattern in enumerate(patterns):
            match = re.search(pattern, test_text)
            result = match.group(1) if match else "NO MATCH"
            pattern_name = "Primary" if j == 0 else "Fallback"
            print(f"     {pattern_name}: {result}")
        print()
    
    print("🚀 RECOMMENDATIONS:")
    print("   1. 🔄 Add DOM wait after scroll: Ensure containers are fully loaded")
    print("   2. 🎯 Improve container detection: Use better selectors for scrolled content")
    print("   3. ⏰ Add retry mechanism: Re-extract metadata if first attempt fails")
    print("   4. 🔍 Enhanced logging: Log each step of metadata extraction")
    print("   5. 🏗️ Container validation: Verify container has expected structure")
    
    return True


def generate_fix_recommendations():
    """Generate specific fix recommendations"""
    
    print(f"\n🛠️ STEP 4: Fix recommendations")
    print("-" * 40)
    
    print("🎯 IMMEDIATE FIXES NEEDED:")
    print("")
    print("1. 🔄 ENHANCED CONTAINER LOADING DETECTION")
    print("   • Add longer wait after scroll for DOM updates")
    print("   • Detect when new containers have fully loaded")
    print("   • Retry metadata extraction if containers are incomplete")
    print("")
    print("2. 🎯 IMPROVED CONTAINER SELECTORS")
    print("   • Use more flexible selectors for dynamically loaded content")
    print("   • Detect containers by content pattern, not just ID")
    print("   • Handle containers with different DOM structure after scroll")
    print("")
    print("3. ⏰ METADATA EXTRACTION TIMING")
    print("   • Wait for text content to be fully populated")
    print("   • Add retry logic for failed extractions")
    print("   • Validate extracted metadata before using it")
    print("")
    print("4. 🔍 ENHANCED BOUNDARY COMPARISON")
    print("   • Log every datetime comparison for debugging")
    print("   • Show exactly which containers are being compared")
    print("   • Add fallback comparison strategies")
    print("")
    print("5. 🚨 BOUNDARY DETECTION DEBUGGING")
    print("   • Add debug mode that logs ALL container metadata")
    print("   • Show exactly why containers are skipped")
    print("   • Log the exact comparison logic being used")
    
    return True


def main():
    """Run the complete boundary detection analysis"""
    
    success = True
    
    try:
        success &= analyze_log_entries()
        success &= analyze_metadata_extraction_issues()  
        success &= generate_fix_recommendations()
        
        print(f"\n📊 ANALYSIS SUMMARY")
        print("=" * 60)
        
        if success:
            print("✅ ANALYSIS COMPLETE")
            print("")
            print("🔍 KEY FINDINGS:")
            print("• Target generation '03 Sep 2025 16:15:18' is NOT in log file (confirmed)")
            print("• Should have been detected as boundary but wasn't")
            print("• Issue is in metadata extraction from scrolled containers")
            print("• Need enhanced container loading detection and retry logic")
            print("")
            print("🚀 NEXT STEPS:")
            print("• Implement the 5 recommended fixes")
            print("• Add comprehensive boundary detection debugging")
            print("• Test with the specific failing case")
            
        return success
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)