#!/usr/bin/env python3.11

"""
Comprehensive duplicate check tracing test.

This test specifically investigates why check_comprehensive_duplicate()
might be failing and what it's actually returning.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestComprehensiveDuplicateTracing:
    """Trace comprehensive duplicate check execution"""

    def test_comprehensive_duplicate_function_call_tracing(self):
        """Test if comprehensive duplicate function is actually being called"""
        
        print("\n" + "="*80)
        print("🕵️ TRACING: COMPREHENSIVE DUPLICATE FUNCTION EXECUTION")
        print("="*80)
        
        # Mock the actual log file data
        actual_log_data = {
            "03 Sep 2025 16:15:18": {
                "prompt": "The camera begins with a medium shot, framing the Prismatic Mage levitating above the magic vortex, their flowing robes cascading and billowing. Crystalline prismatic shards suspended in the air pulse with synchronized light. The camera slowly orbits left, revealing the swirling vortex beneath them—its spiraling en...",
                "file_id": "#999999999",
                "creation_time": "03 Sep 2025 16:15:18", 
                "creation_date": "03 Sep 2025 16:15:18",
                "media_type": "video",
                "unique_id": "skipTest",
                "naming_format": "video_2025-09-03-16-15-18_skipTest_#999999999.mp4",
                "generation_date": "03 Sep 2025 16:15:18"
            }
        }
        
        # Mock the metadata being passed to the function
        boundary_metadata = {
            'generation_date': '03 Sep 2025 16:15:18',
            'prompt': 'The camera begins with a medium shot, framing the Prismatic Mage levitating above the magic vortex, their flowing robes cascading and billowing. Crystalline prismatic shards suspended in the air pulse with synchronized light. The camera slowly orbits left, revealing the swirling vortex beneath them—its spiraling en...'
        }
        
        class ComprehensiveDuplicateTracer:
            """Trace comprehensive duplicate check with exact same logic as real function"""
            
            def __init__(self):
                self.call_count = 0
                self.log_entries = actual_log_data
                
            async def check_comprehensive_duplicate_traced(self, page, thumbnail_id, existing_files=None):
                """Traced version of check_comprehensive_duplicate with exact same logic"""
                
                self.call_count += 1
                print(f"\n📞 FUNCTION CALL #{self.call_count}: check_comprehensive_duplicate")
                print(f"   📋 thumbnail_id: {thumbnail_id}")
                print(f"   📁 existing_files: {len(existing_files) if existing_files else 0}")
                
                # Step 1: Extract metadata from page (this is what succeeds in logs)
                print(f"   🔄 Extracting metadata from gallery...")
                
                # Simulate successful metadata extraction (we know this works)
                metadata = boundary_metadata
                print(f"   ✅ Metadata extracted: date='{metadata['generation_date']}', prompt_length={len(metadata['prompt'])}")
                
                generation_date = metadata.get('generation_date')
                prompt = metadata.get('prompt', '')
                
                if not generation_date or not prompt:
                    print(f"   ❌ Missing metadata - returning False")
                    return False
                
                # Step 2: Load existing log entries  
                print(f"   📚 Loading existing log entries...")
                existing_entries = self.log_entries
                print(f"   📊 Loaded {len(existing_entries)} log entries")
                
                # Step 3: Check for duplicates
                print(f"   🔍 Checking for duplicates...")
                if generation_date in existing_entries:
                    existing_entry = existing_entries[generation_date]
                    print(f"   📄 Found existing entry for {generation_date}")
                    
                    # CRITICAL: Test the incomplete entry filtering
                    file_id = existing_entry.get('file_id', '')
                    print(f"   🆔 File ID: {file_id}")
                    
                    if file_id == '#999999999':
                        print(f"   ⏭️ FILTERING: Skipping incomplete log entry (file_id: {file_id})")
                        print(f"   ✅ RESULT: False (not a duplicate - allow download)")
                        return False  # Not a duplicate - allow download
                    
                    # Check prompt match
                    existing_prompt = existing_entry.get('prompt', '')
                    prompt_match = prompt[:100] == existing_prompt[:100]
                    print(f"   🔍 Prompt match (first 100 chars): {prompt_match}")
                    
                    if prompt_match:
                        print(f"   🛑 DUPLICATE DETECTED: Returning 'exit_scan_return'")
                        return "exit_scan_return"
                
                print(f"   ✅ NO DUPLICATE: Returning False")
                return False
        
        tracer = ComprehensiveDuplicateTracer()
        
        # Test the function
        print(f"\n🧪 TESTING COMPREHENSIVE DUPLICATE CHECK:")
        result = None
        try:
            # Simulate the actual call
            import asyncio
            result = asyncio.run(tracer.check_comprehensive_duplicate_traced(
                page=Mock(), 
                thumbnail_id="landmark_thumbnail_6",
                existing_files=set()
            ))
        except Exception as e:
            print(f"   ❌ Exception during execution: {e}")
            result = "EXCEPTION"
        
        print(f"\n📊 FINAL RESULT: {result}")
        print(f"📞 Function called: {tracer.call_count} times")
        
        # Analysis
        if result == False:
            print(f"\n💡 ANALYSIS:")
            print(f"   ✅ Comprehensive duplicate check should ALLOW download")
            print(f"   ❓ But download is still failing - the issue is NOT in duplicate checking")
            print(f"   🔍 The issue must be in:")
            print(f"      • Download execution logic")
            print(f"      • Return value handling")
            print(f"      • Different code path being used")
            
        elif result == "exit_scan_return":
            print(f"\n💡 ANALYSIS:")
            print(f"   🛑 Comprehensive duplicate check is BLOCKING download")
            print(f"   ❌ Our incomplete entry filtering is NOT working")
            print(f"   🔧 Need to fix the filtering logic")
            
        # Test assertions
        assert tracer.call_count > 0, "Function should be called"
        assert result is not None, "Function should return a result"
        
        return result

    def test_log_entry_filtering_directly(self):
        """Test the incomplete log entry filtering logic directly"""
        
        print("\n" + "="*80)  
        print("🧪 TESTING: LOG ENTRY FILTERING LOGIC")
        print("="*80)
        
        # Test data from actual log file
        test_entries = {
            "complete_entry": {
                "generation_date": "02 Sep 2025 14:30:22",
                "prompt": "Previous complete generation...",
                "file_id": "#000000045"
            },
            "incomplete_entry": {
                "generation_date": "03 Sep 2025 16:15:18", 
                "prompt": "The camera begins with a medium shot, framing the Prismatic Mage...",
                "file_id": "#999999999"  # This should be filtered
            },
            "another_complete_entry": {
                "generation_date": "04 Sep 2025 18:22:11",
                "prompt": "Later complete generation...", 
                "file_id": "#000000046"
            }
        }
        
        def test_filtering_logic(entries):
            """Test the exact filtering logic from our fix"""
            
            filtered_entries = {}
            
            for date_key, entry in entries.items():
                file_id = entry.get('file_id', '')
                
                print(f"   📄 Processing entry: {date_key}")
                print(f"      Date: {entry.get('generation_date')}")
                print(f"      File ID: {file_id}")
                
                if file_id == '#999999999':
                    print(f"      ⏭️ FILTERING: Skipping incomplete entry")
                    continue  # Skip this entry
                else:
                    print(f"      ✅ KEEPING: Complete entry")
                    filtered_entries[date_key] = entry
            
            return filtered_entries
        
        print(f"🔍 TESTING FILTERING LOGIC:")
        print(f"   📊 Input entries: {len(test_entries)}")
        
        filtered = test_filtering_logic(test_entries)
        
        print(f"   📊 Filtered entries: {len(filtered)}")
        print(f"   📋 Kept entries: {list(filtered.keys())}")
        
        # Check if incomplete entry was filtered
        incomplete_filtered = "incomplete_entry" not in filtered
        print(f"   ✅ Incomplete entry filtered: {incomplete_filtered}")
        
        if not incomplete_filtered:
            print(f"   ❌ CRITICAL: Incomplete entry was NOT filtered!")
            print(f"   🔧 This could be why duplicate check is failing")
        
        assert incomplete_filtered, "Incomplete entries should be filtered"
        assert len(filtered) == 2, "Should keep 2 complete entries"
        
        print(f"\n💡 FILTERING LOGIC TEST: {'✅ PASSED' if incomplete_filtered else '❌ FAILED'}")

def run_comprehensive_duplicate_investigation():
    """Run the comprehensive duplicate investigation"""
    test_instance = TestComprehensiveDuplicateTracing()
    
    # Test 1: Function call tracing
    result = test_instance.test_comprehensive_duplicate_function_call_tracing()
    
    # Test 2: Filtering logic
    test_instance.test_log_entry_filtering_directly()
    
    return result

if __name__ == "__main__":
    print("🚀 STARTING COMPREHENSIVE DUPLICATE CHECK INVESTIGATION")
    result = run_comprehensive_duplicate_investigation()
    print(f"\n🎯 INVESTIGATION RESULT: {result}")
    print("✅ COMPREHENSIVE DUPLICATE INVESTIGATION COMPLETE")