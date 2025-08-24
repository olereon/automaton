#!/usr/bin/env python3.11
"""
Debug script to analyze prompt length issue in existing log files
"""

import os
import sys
import re
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def analyze_log_file():
    """Analyze the existing log file to understand prompt truncation"""
    
    log_file = Path("/home/olereon/workspace/github.com/olereon/automaton/logs/generation_downloads.txt")
    
    if not log_file.exists():
        print("❌ Log file not found")
        return
    
    print("🔍 Analyzing Generation Downloads Log")
    print("=" * 50)
    
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse entries
    entries = content.split('========================================')
    
    prompts = []
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) >= 3:
            file_id = lines[0].strip()
            date = lines[1].strip()
            prompt = lines[2].strip()
            
            if file_id.startswith('#'):
                prompts.append({
                    'id': file_id,
                    'date': date,
                    'prompt': prompt,
                    'length': len(prompt)
                })
    
    print(f"📊 Found {len(prompts)} prompt entries")
    print()
    
    # Analyze patterns
    lengths = [p['length'] for p in prompts]
    unique_prompts = set(p['prompt'] for p in prompts)
    
    print("📈 ANALYSIS RESULTS:")
    print(f"   • Total prompts: {len(prompts)}")
    print(f"   • Unique prompts: {len(unique_prompts)}")
    print(f"   • Length range: {min(lengths)} - {max(lengths)} chars")
    print(f"   • Most common length: {max(set(lengths), key=lengths.count)}")
    print()
    
    # Check for truncation patterns
    truncated_count = sum(1 for p in prompts if p['length'] <= 110)  # Suspiciously short
    print(f"📏 TRUNCATION ANALYSIS:")
    print(f"   • Potentially truncated prompts (≤110 chars): {truncated_count}/{len(prompts)}")
    print(f"   • Percentage truncated: {(truncated_count/len(prompts)*100):.1f}%")
    print()
    
    # Show examples
    print("📝 PROMPT EXAMPLES:")
    for i, prompt_data in enumerate(prompts[:3]):
        print(f"   {i+1}. ID: {prompt_data['id']}")
        print(f"      Length: {prompt_data['length']} chars")
        print(f"      Content: {prompt_data['prompt']}")
        print(f"      Ends with: '{prompt_data['prompt'][-20:]}'")
        print()
    
    # Check for specific truncation patterns
    print("🔍 TRUNCATION PATTERN DETECTION:")
    truncation_indicators = [
        " b",  # Current ending
        "...",
        " with",
        " and",
        " the"
    ]
    
    for indicator in truncation_indicators:
        count = sum(1 for p in prompts if p['prompt'].endswith(indicator))
        if count > 0:
            print(f"   • Ending with '{indicator}': {count} prompts")
    
    print()
    print("💡 RECOMMENDATIONS:")
    if truncated_count > 0:
        print("   • All prompts appear to be truncated at ~102 characters")
        print("   • This suggests DOM element truncation rather than logging issue")
        print("   • Need to investigate CSS text-overflow or JavaScript truncation")
        print("   • Try enhanced extraction methods in generation_download_manager.py")
    else:
        print("   • No truncation detected")

if __name__ == "__main__":
    analyze_log_file()